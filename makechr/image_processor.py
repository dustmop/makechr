import chr_tile
import errors
import guess_best_palette
import id_manifest
import palette
import ppu_memory
import rgb
from constants import *


class ImageProcessor(object):
  """Converts pixel art image into data structures in the PPU's memory."""

  def __init__(self):
    self._ppu_memory = ppu_memory.PpuMemory()
    self._nt_count = {}
    self._nametable_cache = {}
    self._color_manifest = id_manifest.IdManifest()
    self._dot_manifest = id_manifest.IdManifest()
    self._block_color_manifest = id_manifest.IdManifest()
    self._artifacts = [row[:] for row in
                       [[None]*(NUM_BLOCKS_X*2)]*(NUM_BLOCKS_Y*2)]
    self._err = errors.ErrorCollector()

  def load_image(self, img):
    (self.image_x, self.image_y) = img.size
    self.pixels = img.convert('RGB').load()

  def artifacts(self):
    return self._artifacts

  def ppu_memory(self):
    return self._ppu_memory

  def nt_count(self):
    return self._nt_count

  def err(self):
    return self._err

  def color_manifest(self):
    return self._color_manifest

  def dot_manifest(self):
    return self._dot_manifest

  def components_to_nescolor(self, r, g, b):
    """Convert RGB color components to an index into the NES system palette.

    Given the color components of a pixel from PIL/pillow, find the
    corresponding index in the NES system palette that most closely matches
    that color. Save the result in RGB_XLAT so future accesses will be fast.
    If the color cannot be converted, return -1.

    r: The red value of the pixel.
    g: The green value of the pixel.
    b: The blue value of the pixel.
    """
    found_nc = -1
    found_diff = float('infinity')
    colors = rgb.RGB_COLORS
    for i,allow_val in enumerate(colors):
      diff_r = abs(r - allow_val / (256 * 256))
      diff_g = abs(g - (allow_val / 256) % 256)
      diff_b = abs(b - allow_val % 256)
      diff = diff_r + diff_g + diff_b
      if diff < found_diff:
        found_nc = i
        found_diff = diff
    if found_diff > rgb.COLOR_TOLERANCE:
      return -1
    if found_nc == 0x0d:
      found_nc = 0x0f
    color_val = r * 256 * 256 + g * 256 + b
    rgb.RGB_XLAT[color_val] = found_nc
    return found_nc

  def collect_error(self, e, block_y, block_x, i, j, is_block=False):
    """Add the exception to the error exception and clear the artifacts entry.

    e: The exception that got caught.
    block_y: The y of the block.
    block_x: The x of the block.
    i: Y offset of the tile within the block.
    j: X offset of the tile within the block.
    is_block: Whether the error is at the block level, or tile level.
    """
    self._err.add(e)
    if is_block:
      self._artifacts[block_y * 2 + 0][block_x * 2 + 0] = [0, 0, 0]
      self._artifacts[block_y * 2 + 0][block_x * 2 + 1] = [0, 0, 0]
      self._artifacts[block_y * 2 + 1][block_x * 2 + 0] = [0, 0, 0]
      self._artifacts[block_y * 2 + 1][block_x * 2 + 1] = [0, 0, 0]
    else:
      self._artifacts[block_y * 2 + i][block_x * 2 + j] = [0, 0, 0]

  def process_tile(self, tile_y, tile_x):
    """Process the tile and save artifact information.

    Process the tile to obtain its color needs and dot profile, verifying that
    the tile contains colors that match the system palette, and does not contain
    too many colors. This method is called many times for an image, so it
    contains a lot of micro-optimizations. The image should have already been
    loaded using self.load_image. Return the color_needs and dot_profile.

    tile_y: The y position of the tile, 0..31.
    tile_x: The x position of the tile, 0..29.
    """
    pixel_y = tile_y * TILE_SIZE
    pixel_x = tile_x * TILE_SIZE
    color_needs = bytearray([0xff, 0xff, 0xff, 0xff])
    dot_profile = bytearray(TILE_SIZE * TILE_SIZE)
    # Check if this tile overruns the image.
    if pixel_y + TILE_SIZE > self.image_y or pixel_x + TILE_SIZE > self.image_x:
      return color_needs, dot_profile
    # Get local variables for frequently accessed data. This improves
    # performance. 'xlat' is mutated whenever 'components_to_nescolor_func' is
    # called.
    ps = self.pixels
    xlat = rgb.RGB_XLAT
    components_to_nescolor_func = self.components_to_nescolor
    for i in xrange(TILE_SIZE):
      row = i * TILE_SIZE
      for j in xrange(TILE_SIZE):
        # Get the current pixel value 'p', convert it to a nescolor 'nc'.
        p = ps[pixel_x + j, pixel_y + i]
        color_val = (p[0] << 16) + (p[1] << 8) + p[2]
        if color_val in xlat:
          nc = xlat[color_val]
        else:
          nc = components_to_nescolor_func(p[0], p[1], p[2])
          if nc == -1:
            raise errors.ColorNotAllowedError(p, tile_y, tile_x, i, j)
        # Add the nescolor 'nc' to the 'color_needs'. Insert it into the first
        # position that is equal to 0xff, otherwise append it to the end.
        for idx in xrange(4):
          if color_needs[idx] == nc:
            break
          if color_needs[idx] == 0xff:
            color_needs[idx] = nc
            break
        else:
          color_needs.append(nc)
          idx = len(color_needs) - 1
        dot_profile[row + j] = idx
    if len(color_needs) > PALETTE_SIZE:
      raise errors.PaletteOverflowError(tile_y, tile_x)
    return color_needs, dot_profile

  def process_block(self, block_y, block_x, is_sprite):
    """Process the individual tiles in the block.

    block_y: The y position of the block, 0..15.
    block_x: The x position of the block, 0..14.
    """
    block_color_needs = set([])
    y = block_y * 2
    x = block_x * 2
    process_tile_func = self.process_tile
    for i in xrange(2):
      for j in xrange(2):
        try:
          (color_needs, dot_profile) = process_tile_func(y + i, x + j)
        except (errors.PaletteOverflowError, errors.ColorNotAllowedError) as e:
          self.collect_error(e, block_y, block_x, i, j)
          continue
        cid = self._color_manifest.id(color_needs)
        did = self._dot_manifest.id(dot_profile)
        self._artifacts[y + i][x + j] = [cid, did, None]
        block_color_needs |= set(color_needs)
    if not is_sprite:
      block_color_needs = block_color_needs - set([0xff])
      if len(block_color_needs) > PALETTE_SIZE:
        raise errors.PaletteOverflowError(block_y, block_x, is_block=True)
      bcid = self._block_color_manifest.id(block_color_needs)
      self._artifacts[y][x][ARTIFACT_BCID] = bcid

  def get_dot_xlat(self, color_needs, palette_option):
    """Create an xlat object to convert the color_needs to the palette.

    color_needs: The color_needs to convert.
    palette_option: The palette to target.
    """
    dot_xlat = []
    for c in color_needs:
      if c is 0xff:
        continue
      for i,p in enumerate(palette_option):
        if c == p:
          dot_xlat.append(i)
          break
      else:
        raise IndexError
    return dot_xlat

  def get_nametable_num(self, xlat, did, is_locked_tiles):
    """Get the dot_profile, xlat its dots making a nametable tile, and save it.

    xlat: Dot translator.
    did: Id for the dot_profile.
    """
    if is_locked_tiles and len(self._ppu_memory.chr_data) == 0x100:
      return 0
    key = str([did] + xlat)
    if key in self._nametable_cache:
      nt_num = self._nametable_cache[key]
    else:
      dot_profile = self._dot_manifest.at(did)
      tile = chr_tile.ChrTile()
      for row in xrange(8):
        for col in xrange(8):
          i = row * 8 + col
          val = xlat[dot_profile[i]]
          tile.set(row, col, val)
      nt_num = len(self._ppu_memory.chr_data)
      self._ppu_memory.chr_data.append(tile)
      self._nt_count[nt_num] = 0
      if not is_locked_tiles:
        self._nametable_cache[key] = nt_num
    self._nt_count[nt_num] += 1
    return nt_num

  def get_color_sets(self, color_element_list):
    sets = []
    for color_needs in color_element_list:
      try:
        idx = list(color_needs).index(0xff)
        sets.append(color_needs[0:idx])
      except ValueError:
        sets.append(color_needs)
    return sets

  def make_palette(self, palette_text, bg_color, is_sprite):
    """Construct the palette object from parsable text or color_needs.

    palette_text: Optional text to parse palette object from.
    bg_color: Background color. Must match palette's background color, if given.
    is_sprite: Whether this is a sprite palette.
    """
    pal = None
    if palette_text:
      # If palette argument was passed, use that palette.
      try:
        parser = palette.PaletteParser()
        pal = parser.parse(palette_text)
      except errors.PaletteParseError as e:
        self._err.add(e)
        return
      if not bg_color is None and pal.bg_color != bg_color:
        self._err.add(errors.PaletteBackgroundColorConflictError(
          pal.bg_color, bg_color))
    else:
      # Make the palette from the color needs.
      guesser = guess_best_palette.GuessBestPalette()
      if not bg_color is None:
        guesser.set_bg_color(bg_color)
      if not is_sprite:
        color_sets = self._block_color_manifest.elems()
      else:
        color_sets = self.get_color_sets(self._color_manifest.elems())
      try:
        pal = guesser.guess_palette(color_sets)
      except errors.TooManyPalettesError as e:
        self._err.add(e)
    return pal

  def process_image(self, img, palette_text, bg_color, traversal,
                    is_sprite, is_locked_tiles):
    """Process an image, creating the ppu_memory necessary to display it.

    img: Pixel art image.
    palette_text: Optional string representing a palette to be parsed.
    bg_color: Background color of the image.
    traversal: Strategy for traversing the nametable.
    is_sprite: Whether the image is of sprites.
    is_locked_tiles: Whether tiles are locked into place. If so, do not
        merge duplicates, and only handle first 256 tiles.
    """
    self.load_image(img)
    num_blocks_y = NUM_BLOCKS_Y
    num_blocks_x = NUM_BLOCKS_X
    # Assign flags.
    self._ppu_memory.is_locked_tiles = is_locked_tiles
    self._ppu_memory.nt_width = NUM_BLOCKS_X * 2
    # If image is exactly 128x128 and uses locked tiles, treat it as though it
    # represents CHR memory.
    if self.image_x == self.image_y == SMALL_SQUARE and is_locked_tiles:
      num_blocks_y = NUM_BLOCKS_SMALL_SQUARE
      num_blocks_x = NUM_BLOCKS_SMALL_SQUARE
      self._ppu_memory.nt_width = NUM_BLOCKS_SMALL_SQUARE * 2
    # For each block, look at each tile and get their color needs and
    # dot profile. Save the corresponding ids in the artifact table.
    for block_y in xrange(num_blocks_y):
      for block_x in xrange(num_blocks_x):
        try:
          self.process_block(block_y, block_x, is_sprite)
        except errors.PaletteOverflowError as e:
          self.collect_error(e, block_y, block_x, 0, 0, is_block=True)
          continue
    if self._err.has():
      return
    pal = self.make_palette(palette_text, bg_color, is_sprite)
    if not pal:
      return
    # Find empty tile.
    empty_did = self._dot_manifest.get(chr(0) * 64)
    empty_cid = self._color_manifest.get(chr(pal.bg_color) + '\xff\xff\xff')
    if not is_sprite:
      # For each block, get the attribute aka the palette.
      for block_y in xrange(num_blocks_y):
        for block_x in xrange(num_blocks_x):
          y = block_y * 2
          x = block_x * 2
          (cid, did, bcid) = self._artifacts[y][x]
          block_color_needs = self._block_color_manifest.at(bcid)
          try:
            (pid, palette_option) = pal.select(block_color_needs)
          except IndexError:
            self._err.add(errors.PaletteNoChoiceError(y, x, block_color_needs))
            pid = 0
          self._ppu_memory.gfx_0.position_palette[block_y*2][block_x*2] = pid
    else:
      # For each tile, get the attribute aka the palette.
      for y in xrange(num_blocks_y*2):
        for x in xrange(num_blocks_x*2):
          (cid, did, bcid) = self._artifacts[y][x]
          color_needs = self._color_manifest.at(cid)
          for k in range(4):
            if color_needs[k] == 0xff:
              color_needs = color_needs[0:k]
              break
          color_needs = set(color_needs)
          try:
            (pid, palette_option) = pal.select(color_needs)
          except IndexError:
            self._err.add(errors.PaletteNoChoiceError(y, x, color_needs))
            pid = 0
          self._ppu_memory.gfx_0.position_palette[y][x] = pid
    if self._err.has():
      return
    # Traverse tiles in the artifact table, creating the chr and nametable.
    if traversal == 'horizontal':
      rows = num_blocks_y * 2
      cols = num_blocks_x * 2
      generator = ((y,x) for y in xrange(rows) for x in xrange(cols))
    elif traversal == 'block':
      generator = ((y*2+i,x*2+j) for y in xrange(num_blocks_y) for
                   x in xrange(num_blocks_x) for i in xrange(2) for
                   j in xrange(2))
    for (y,x) in generator:
      (cid, did, bcid) = self._artifacts[y][x]
      if not is_sprite:
        pid = self._ppu_memory.gfx_0.position_palette[(y / 2)*2][(x / 2)*2]
      else:
        pid = self._ppu_memory.gfx_0.position_palette[y][x]
      palette_option = pal.get(pid)
      color_needs = self._color_manifest.at(cid)
      try:
        dot_xlat = self.get_dot_xlat(color_needs, palette_option)
      except IndexError:
        raise
      # If there was an error in the tile, the dot_xlat will be empty. So
      # skip this entry.
      if dot_xlat:
        nt_num = self.get_nametable_num(dot_xlat, did, is_locked_tiles)
        self._ppu_memory.gfx_0.nametable[y][x] = nt_num
        if nt_num >= 0x100:
          self._err.add(errors.NametableOverflow(y, x, nt_num))
      if empty_cid == cid and empty_did == did:
        self._ppu_memory.empty_tile = nt_num
    # Store palette.
    if not is_sprite:
      self._ppu_memory.palette_nt = pal
    else:
      self._ppu_memory.palette_spr = pal
