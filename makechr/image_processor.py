import chr_data
import extract_indexed_image_palette
import errors
import guess_best_palette
import id_manifest
import itertools
import palette
import ppu_memory
import rgb
from constants import *


NULL = 0xff


class ImageProcessor(object):
  """Converts pixel art image into data structures in the PPU's memory."""

  def __init__(self):
    self._ppu_memory = ppu_memory.PpuMemory()
    self._chrdata_cache = {}
    self._color_manifest = id_manifest.IdManifest()
    self._dot_manifest = id_manifest.IdManifest()
    self._block_color_manifest = id_manifest.IdManifest()
    self._needs_provider = None
    self._test_only_auto_sprite_bg = False
    self._artifacts = [row[:] for row in
                       [[None]*(NUM_BLOCKS_X*2)]*(NUM_BLOCKS_Y*2)]
    self._flip_bits = [row[:] for row in
                       [[0]*(NUM_BLOCKS_X*2)]*(NUM_BLOCKS_Y*2)]
    self._err = errors.ErrorCollector()
    self.image_x = self.image_y = None

  def load_image(self, img):
    self.img = img
    (self.image_x, self.image_y) = self.img.size
    self.pixels = self.img.convert('RGB').load()

  def artifacts(self):
    return self._artifacts

  def ppu_memory(self):
    return self._ppu_memory

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
      for a,b in itertools.product(range(2),range(2)):
        self._artifacts[block_y * 2 + a][block_x * 2 + b] = [0, 0, 0]
    else:
      self._artifacts[block_y * 2 + i][block_x * 2 + j] = [0, 0, 0]

  def process_tile(self, tile_y, tile_x, subtile_y, subtile_x):
    """Process the tile and save artifact information.

    Process the tile to obtain its color needs and dot profile, verifying that
    the tile contains colors that match the system palette, and does not contain
    too many colors. This method is called many times for an image, so it
    contains a lot of micro-optimizations. The image should have already been
    loaded using self.load_image. Return the color_needs and dot_profile.

    tile_y: The y position of the tile, 0..31.
    tile_x: The x position of the tile, 0..29.
    subtile_y: Pixel y offset within the tile.
    subtile_x: Pixel x offset within the tile.
    """
    pixel_y = tile_y * TILE_SIZE + subtile_y
    pixel_x = tile_x * TILE_SIZE + subtile_x
    color_needs = bytearray([NULL, NULL, NULL, NULL])
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
        # position that is equal to NULL, otherwise append it to the end.
        for idx in xrange(4):
          if color_needs[idx] == nc:
            break
          if color_needs[idx] == NULL:
            color_needs[idx] = nc
            break
        else:
          raise errors.PaletteOverflowError(tile_y, tile_x)
        dot_profile[row + j] = idx
    return color_needs, dot_profile

  def process_block(self, block_y, block_x, is_sprite):
    """Process the individual tiles in the block.

    block_y: The y position of the block, 0..15.
    block_x: The x position of the block, 0..14.
    is_sprite: Whether this is sprite mode.
    """
    block_color_needs = bytearray([NULL, NULL, NULL, NULL])
    y = block_y * 2
    x = block_x * 2
    process_tile_func = self.process_tile
    combine_color_needs_func = self.combine_color_needs
    if is_sprite:
      combine_color_needs_func = self.null_func
    for i in xrange(2):
      for j in xrange(2):
        try:
          (color_needs, dot_profile) = process_tile_func(y + i, x + j, 0, 0)
        except (errors.PaletteOverflowError, errors.ColorNotAllowedError) as e:
          self.collect_error(e, block_y, block_x, i, j)
          continue
        cid = self._color_manifest.id(color_needs)
        did = self._dot_manifest.id(dot_profile)
        self._artifacts[y + i][x + j] = [cid, did, None]
        try:
          combine_color_needs_func(block_color_needs, color_needs)
        except errors.PaletteOverflowError as e:
          e.block_y = block_y
          e.block_x = block_x
          self.collect_error(e, block_y, block_x, i, j)
          return
    if not is_sprite:
      bcid = self._block_color_manifest.id(block_color_needs)
      self._artifacts[y][x][ARTIFACT_BCID] = bcid

  def combine_color_needs(self, target, source):
    """Combine by filling in null elements. Raise an error if full."""
    for a in source:
      if a == NULL:
        return
      for k, b in enumerate(target):
        if a == b:
          break
        elif b == NULL:
          target[k] = a
          break
      else:
        raise errors.PaletteOverflowError(is_block=True)

  def null_func(self, *args):
    pass

  def get_dot_xlat(self, color_needs, palette_option):
    """Create an xlat object to convert the color_needs to the palette.

    color_needs: The color_needs to convert.
    palette_option: The palette to target.
    """
    dot_xlat = []
    for c in color_needs:
      if c is NULL:
        continue
      for i,p in enumerate(palette_option):
        if c == p:
          dot_xlat.append(i)
          break
      else:
        raise IndexError
    return dot_xlat

  def store_chrdata(self, xlat, did, config):
    """Translate dots to make chr data, and save it. Cache results.

    xlat: Dot translator.
    did: Id for the dot_profile.
    config: Configuration containing ppu_memory flags.
    """
    if config.is_locked_tiles and self._ppu_memory.chr_page.is_full():
      return (0, 0)
    key = str([did] + xlat)
    if key in self._chrdata_cache:
      return self._chrdata_cache[key]
    tile = self.build_tile(xlat, did)
    if config.is_sprite and str(tile) in self._chrdata_cache:
      return self._chrdata_cache[str(tile)]
    # Add the tile to the chr collection.
    try:
      chr_num = self._ppu_memory.chr_page.add(tile)
    except errors.ChrPageFull:
      chr_num = len(self._chrdata_cache)
      self._chrdata_cache[key] = (0, 0x00)
      raise errors.NametableOverflow(chr_num)
    # Save in the cache.
    if config.is_sprite and not config.is_locked_tiles:
      horz_tile = tile.flip('h')
      vert_tile = tile.flip('v')
      spin_tile = tile.flip('vh')
      self._chrdata_cache[str(spin_tile)] = (chr_num, 0xc0)
      self._chrdata_cache[str(vert_tile)] = (chr_num, 0x80)
      self._chrdata_cache[str(horz_tile)] = (chr_num, 0x40)
      self._chrdata_cache[str(tile)]      = (chr_num, 0x00)
    elif not config.is_locked_tiles:
      self._chrdata_cache[key] = (chr_num, 0x00)
    return (chr_num, 0x00)

  def build_tile(self, xlat, did):
    """Lookup dot_profile, and translate it to create tile.

    xlat: Dot translator.
    did: Id for the dot profile.
    """
    dot_profile = self._dot_manifest.at(did)
    tile = chr_data.ChrTile()
    for row in xrange(8):
      for col in xrange(8):
        i = row * 8 + col
        val = xlat[dot_profile[i]]
        tile.put_pixel(row, col, val)
    return tile

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
        return None
      if not bg_color is None and pal.bg_color != bg_color:
        self._err.add(errors.PaletteBackgroundColorConflictError(
          pal.bg_color, bg_color))
        return None
      return pal
    if self.img.palette:
      # If the image uses indexed color, try to extract a palette.
      extractor = extract_indexed_image_palette.ExtractIndexedImagePalette(self)
      pal = extractor.extract_palette(self.img.palette, self.img.format)
      if pal:
        return pal
    # If sprite mode, and there's no bg color, we can figure it out based upon
    # how many empty tiles there need to be.
    if is_sprite and bg_color is None and not self._test_only_auto_sprite_bg:
      for color, num in self._needs_provider.counts():
        if num >= 0x40 and bg_color is None:
          bg_color = color
    # Make the palette from the color needs.
    guesser = guess_best_palette.GuessBestPalette()
    if not bg_color is None:
      guesser.set_bg_color(bg_color)
    color_sets = self._needs_provider.elems()
    try:
      pal = guesser.guess_palette(color_sets)
    except errors.TooManyPalettesError as e:
      self._err.add(e)
      return None
    return pal

  def process_to_artifacts(self, config):
    """Process the image and store data in the artifact table.

    For each block, look at each tile and get their color needs and
    dot profile. Save the ids in the artifact table.

    config: Configuration of ppu_memory
    """
    for block_y in xrange(self.blocks_y):
      for block_x in xrange(self.blocks_x):
        try:
          self.process_block(block_y, block_x, config.is_sprite)
        except errors.PaletteOverflowError as e:
          self.collect_error(e, block_y, block_x, 0, 0, is_block=True)
          continue
    self._needs_provider = self._block_color_manifest
    if config.is_sprite:
      self._needs_provider = self._color_manifest

  def make_colorization(self, pal, config):
    """Select colorization for each position in the image.

    pal: Palette for this image.
    config: Configuration of ppu_memory
    """
    if not config.is_sprite:
      # For each block, get the attribute aka the palette.
      for block_y in xrange(self.blocks_y):
        for block_x in xrange(self.blocks_x):
          y = block_y * 2
          x = block_x * 2
          (cid, did, bcid) = self._artifacts[y][x]
          color_needs = self._needs_provider.at(bcid)
          try:
            (pid, palette_option) = pal.select(color_needs)
          except IndexError:
            self._err.add(errors.PaletteNoChoiceError(y, x, color_needs))
            pid = 0
          for a,b in itertools.product(range(2),range(2)):
            self._ppu_memory.gfx_0.colorization[y + a][x + b] = pid
    else:
      # For each tile, get the attribute aka the palette.
      for y in xrange(self.blocks_y * 2):
        for x in xrange(self.blocks_x * 2):
          (cid, did, bcid) = self._artifacts[y][x]
          color_needs = self._needs_provider.at(cid)
          try:
            (pid, palette_option) = pal.select(color_needs)
          except IndexError:
            self._err.add(errors.PaletteNoChoiceError(y, x, color_needs))
            pid = 0
          self._ppu_memory.gfx_0.colorization[y][x] = pid

  def traverse_artifacts(self, traversal, pal, config):
    """Traverse the artifacts, building CHR and other ppu_memory data.

    traversal: Method of traversal
    pal: Palette for this image
    config: Configuration of ppu_memory
    """
    # Find empty tile.
    empty_did = self._dot_manifest.get(chr(0) * 64)
    empty_cid = self._color_manifest.get(chr(pal.bg_color) + chr(NULL) * 3)
    # Traverse tiles in the artifact table, creating the chr and nametable.
    if traversal == 'horizontal':
      generator = ((y,x) for y in xrange(self.blocks_y * 2) for
                   x in xrange(self.blocks_x * 2))
    elif traversal == 'block':
      generator = ((y*2+i,x*2+j) for y in xrange(self.blocks_y) for
                   x in xrange(self.blocks_x) for i in xrange(2) for
                   j in xrange(2))
    elif traversal == '8x16':
      raise RuntimeError('Should not be invoked outside of 8x16Processor')
    for (y,x) in generator:
      (cid, did, bcid) = self._artifacts[y][x]
      pid = self._ppu_memory.gfx_0.colorization[y][x]
      palette_option = pal.get(pid)
      color_needs = self._color_manifest.at(cid)
      if config.is_sprite and not config.is_locked_tiles:
        if empty_cid == cid and empty_did == did:
          self._ppu_memory.gfx_0.nametable[y][x] = 0x100
          self._ppu_memory.empty_tile = 0x100
          continue
      # Create a translator that can turn the dot_profile into a chr_tile.
      dot_xlat = self.get_dot_xlat(color_needs, palette_option)
      if not dot_xlat:
        continue
      # If there was an error in the tile, the dot_xlat will be empty. So
      # skip this entry.
      try:
        (chr_num, flip_bits) = self.store_chrdata(dot_xlat, did, config)
      except errors.NametableOverflow, e:
        self._err.add(errors.NametableOverflow(e.chr_num, y, x))
        chr_num = 0
      if config.is_sprite:
        self._flip_bits[y][x] = flip_bits
      self._ppu_memory.gfx_0.nametable[y][x] = chr_num
      if empty_cid == cid and empty_did == did:
        self._ppu_memory.empty_tile = chr_num

  def make_spritelist(self, traversal, pal, config):
    """Convert data from the nametable to create spritelist.

    traversal: Method of traversal
    """
    empty_did = self._dot_manifest.get(chr(0) * 64)
    empty_cid = self._color_manifest.get(chr(pal.bg_color) + chr(NULL) * 3)
    generator = ((y,x) for y in xrange(self.blocks_y * 2) for
                 x in xrange(self.blocks_x * 2))
    for (y,x) in generator:
      (cid, did, bcid) = self._artifacts[y][x]
      if empty_cid == cid and empty_did == did:
        continue
      tile = self._ppu_memory.gfx_0.nametable[y][x]
      if len(self._ppu_memory.spritelist) == 0x40:
        if not config.is_locked_tiles:
          self._err.add(errors.SpritelistOverflow(y, x))
        continue
      y_pos = y * 8 - 1 if y > 0 else 0
      x_pos = x * 8
      attr = self._ppu_memory.gfx_0.colorization[y][x] | self._flip_bits[y][x]
      self._ppu_memory.spritelist.append([y_pos, tile, attr, x_pos])

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
    self.blocks_y = NUM_BLOCKS_Y
    self.blocks_x = NUM_BLOCKS_X
    # Assign configuration.
    config = ppu_memory.PpuMemoryConfig(is_sprite=is_sprite,
                                        is_locked_tiles=is_locked_tiles)
    # TODO: Not being used anywhere.
    self._ppu_memory.nt_width = NUM_BLOCKS_X * 2
    # If image is exactly 128x128 and uses locked tiles, treat it as though it
    # represents CHR memory.
    if self.image_x == self.image_y == SMALL_SQUARE and config.is_locked_tiles:
      self.blocks_y = NUM_BLOCKS_SMALL_SQUARE
      self.blocks_x = NUM_BLOCKS_SMALL_SQUARE
      self._ppu_memory.nt_width = NUM_BLOCKS_SMALL_SQUARE * 2
    # In order to auto detect the background color, have to count color needs.
    if config.is_sprite and bg_color is None:
      self._color_manifest = id_manifest.CountingIdManifest()
    # Process each block and tile to build artifacts.
    self.process_to_artifacts(config)
    if self._err.has():
      return
    # Make the palette.
    pal = self.make_palette(palette_text, bg_color, config.is_sprite)
    if not pal:
      return
    # Make colorization for each block and tile.
    self.make_colorization(pal, config)
    if self._err.has():
      return
    # Traverse the artifacts, building chr and other ppu_memory.
    self.traverse_artifacts(traversal, pal, config)
    if self._err.has():
      return
    # Store palette, and build spritelist, is necessary.
    if not config.is_sprite:
      self._ppu_memory.palette_nt = pal
    else:
      self._ppu_memory.palette_spr = pal
      self.make_spritelist(traversal, pal, config)
