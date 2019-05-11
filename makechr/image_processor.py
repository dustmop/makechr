import chr_data
import collections
import extract_indexed_image_palette
import errors
import guess_best_palette
import id_manifest
import itertools
import math
import os
import palette
import ppu_memory
import sys
import rgb
import wrapped_image_palette
from constants import *


if sys.version_info < (3,0):
  range = xrange


class ImageProcessor(object):
  """Converts pixel art image into data structures in the PPU's memory."""

  def __init__(self):
    self.initialize()
    # A flag only used by tests, whether sprites auto detect background color.
    self._test_only_auto_sprite_bg = False

  def initialize(self):
    self._ppu_memory = ppu_memory.PpuMemory()
    self._chrdata_cache = {}
    self._color_manifest = id_manifest.IdManifest()
    self._dot_manifest = id_manifest.IdManifest()
    self._block_color_manifest = id_manifest.IdManifest()
    self._needs_provider = None
    self._artifacts = None
    self._flip_bits = None
    self._err = errors.ErrorCollector()
    self.image_x = self.image_y = None

  def load_image(self, img):
    self.img = img
    self.pixels = self.img.convert('RGB').load()
    (self.image_x, self.image_y) = self.img.size
    self.blocks_y = int(math.ceil(float(self.image_y) / 16))
    self.blocks_x = int(math.ceil(float(self.image_x) / 16))
    # Calculate number of screens and allocate space for ppu memory.
    self.screen_y = int(math.ceil(float(self.blocks_y) / 16))
    self.screen_x = int(math.ceil(float(self.blocks_x) / 16))
    size_x = NUM_TILES_X * self.screen_x
    size_y = NUM_TILES_Y * self.screen_y
    self._artifacts = [row[:] for row in [[None] * size_x] * size_y]
    self._flip_bits = [row[:] for row in [[None] * size_x] * size_y]
    self._ppu_memory.allocate_num_pages(self.screen_y * self.screen_x)
    # Set size of nametable for each screen.
    for y in range(self.screen_y):
      for x in range(self.screen_x):
        size_y, size_x = 0, 0
        if y == self.screen_y - 1:
          size_y = (self.blocks_y % 15) * 2
        if x == self.screen_x - 1:
          size_x = (self.blocks_x % 16) * 2
        if size_y == 0:
          size_y = 30
        if size_x == 0:
          size_x = 32
        n = y * self.screen_x + x
        self._ppu_memory.gfx[n].nt_y = size_y
        self._ppu_memory.gfx[n].nt_x = size_x

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
      diff_r = abs(r - allow_val // (256 * 256))
      diff_g = abs(g - (allow_val // 256) % 256)
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

  def get_nes_color(self, y, x):
    """Get the nes color corresponding to the pixel at position y,x."""

    p = self.pixels[x, y]
    color_val = (p[0] << 16) + (p[1] << 8) + p[2]
    if color_val in rgb.RGB_XLAT:
      return rgb.RGB_XLAT[color_val]
    else:
      nc = self.components_to_nescolor(p[0], p[1], p[2])
      if nc == -1:
        raise errors.CouldntConvertRGB(p, y/8, x/8, y%8, x%8)
      return nc

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

  def process_tile(self, tile_y, tile_x, subtile_y=0, subtile_x=0):
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
    for i in range(TILE_SIZE):
      row = i * TILE_SIZE
      for j in range(TILE_SIZE):
        # Inlined call to get_nes_color(pixel_y, pixel_x) to get nc.
        p = ps[pixel_x + j, pixel_y + i]
        color_val = (p[0] << 16) + (p[1] << 8) + p[2]
        if color_val in xlat:
          nc = xlat[color_val]
        else:
          nc = components_to_nescolor_func(p[0], p[1], p[2])
          if nc == -1:
            raise errors.CouldntConvertRGB(p, tile_y, tile_x, i, j)
        # Add the nescolor 'nc' to the 'color_needs'. Insert it into the first
        # position that is equal to NULL, otherwise raise an error. Loop is
        # unrolled for performance.
        while True:
          idx = 0
          if color_needs[idx] == nc:
            break
          elif color_needs[idx] == NULL:
            color_needs[idx] = nc
            break
          idx = 1
          if color_needs[idx] == nc:
            break
          elif color_needs[idx] == NULL:
            color_needs[idx] = nc
            break
          idx = 2
          if color_needs[idx] == nc:
            break
          elif color_needs[idx] == NULL:
            color_needs[idx] = nc
            break
          idx = 3
          if color_needs[idx] == nc:
            break
          elif color_needs[idx] == NULL:
            color_needs[idx] = nc
            break
          idx = self.tile_palette_fault(tile_y, tile_x)
          break
        dot_profile[row + j] = idx
    return color_needs, dot_profile

  def tile_palette_fault(self, tile_y, tile_x):
    raise errors.PaletteOverflowError(tile_y, tile_x)

  def process_block(self, block_y, block_x, bg_mask, bg_fill, is_sprite):
    """Process the individual tiles in the block.

    block_y: The y position of the block, 0..15.
    block_x: The x position of the block, 0..14.
    bg_mask: Background color mask, if mask is being used.
    bg_fill: Background color fill.
    is_sprite: Whether this is sprite mode.
    """
    block_color_needs = bytearray([NULL, NULL, NULL, NULL])
    y = block_y * 2
    x = block_x * 2
    process_tile_func = self.process_tile
    combine_color_needs_func = self.combine_color_needs
    if is_sprite:
      combine_color_needs_func = self.null_func
    if bg_mask:
      process_tile_func = (
        lambda y,x: self.filter_process_tile(y, x, bg_mask, bg_fill))
    for i in range(2):
      for j in range(2):
        try:
          (color_needs, dot_profile) = process_tile_func(y + i, x + j)
        except (errors.PaletteOverflowError, errors.CouldntConvertRGB) as e:
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

  def filter_process_tile(self, tile_y, tile_x, bg_mask, bg_fill):
    (color_needs, dot_profile) = self.process_tile(tile_y, tile_x)
    for i in range(len(color_needs)):
      if color_needs[i] == bg_mask:
        color_needs[i] = bg_fill
    return (color_needs, dot_profile)

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
        raise errors.PalettesUnsuitable(color_needs, palette_option)
    return dot_xlat

  def store_chrdata(self, xlat, did, config):
    """Translate dots to make chr data, and save it. Cache results.

    xlat: Dot translator.
    did: Id for the dot_profile.
    config: Configuration containing ppu_memory flags.
    """
    if config.is_locked_tiles and self._ppu_memory.chr_set.is_full():
      return (0, 0)
    key = str([did] + xlat)
    if key in self._chrdata_cache:
      return self._chrdata_cache[key]
    tile = self.build_tile(xlat, did)
    if config.is_sprite and str(tile) in self._chrdata_cache:
      return self._chrdata_cache[str(tile)]
    # Add the tile to the chr collection.
    try:
      chr_num = self._ppu_memory.chr_set.add(tile)
    except errors.ChrPageFull:
      chr_num = len(self._chrdata_cache)
      self._chrdata_cache[key] = (0, 0x00)
      raise errors.NametableOverflow(chr_num)
    # Save in the cache.
    if (config.is_sprite and not config.is_locked_tiles and
        not config.lock_sprite_flips):
      self.assign_tile_flips(tile, [chr_num], self._chrdata_cache)
    elif not config.is_locked_tiles:
      self._chrdata_cache[key] = (chr_num, 0x00)
    return (chr_num, 0x00)

  def assign_tile_flips(self, tile, value_list, storage):
    """Flip tile each way, generate keys and store them in the storage.

    tile: ChrTile object that can be flipped.
    value_list: Values in a list to be stored in the storage.
    storage: A dictionary to store values.
    """
    storage[str(tile.flip('vh'))] = tuple(value_list + [0xc0])
    storage[str(tile.flip('v'))]  = tuple(value_list + [0x80])
    storage[str(tile.flip('h'))]  = tuple(value_list + [0x40])
    storage[str(tile)]            = tuple(value_list + [0x00])

  def build_tile(self, xlat, did):
    """Lookup dot_profile, and translate it to create tile.

    xlat: Dot translator.
    did: Id for the dot profile.
    """
    dot_profile = self._dot_manifest.at(did)
    tile = chr_data.ChrTile()
    for row in range(8):
      for col in range(8):
        i = row * 8 + col
        val = xlat[dot_profile[i]]
        tile.put_pixel(row, col, val)
    return tile

  def parse_palette(self, palette_text, bg_color):
    """Parse the palette either from command-line flag, or indexed image.

    palette_text: Optional text to parse palette object from.
    bg_color: Background color. Must match palette's background color, if given.
    """
    pal = None
    if palette_text:
      # If palette argument was passed, parse it.
      try:
        if palette_text == '+':
          # Attempt to extract the palette from the image, see below.
          pass
        elif palette_text == '-':
          # Do not attempt to extract the palette.
          return None
        elif palette_text.startswith('P/'):
          # Literal palette string.
          parser = palette.PaletteParser()
          pal = parser.parse(palette_text)
        elif os.path.isfile(palette_text):
          # File containing a palette.
          reader = palette.PaletteFileReader()
          pal = reader.read(palette_text)
        else:
          raise errors.PaletteParseError('Unknown palette "%s"' % palette_text)
      except errors.PaletteParseError as e:
        self._err.add(e)
        return None
      if pal:
        if bg_color is not None and pal.bg_color != bg_color:
          self._err.add(errors.PaletteBackgroundColorConflictError(
            pal.bg_color, bg_color))
          return None
        return pal
    # If image uses indexed color, attempt to extract the palette.
    if self.img.palette:
      extractor = extract_indexed_image_palette.ExtractIndexedImagePalette(self)
      try:
        w = wrapped_image_palette.WrappedImagePalette.from_image(self.img)
        pal = extractor.extract_palette(w)
      except errors.PaletteExtractionError as e:
        if palette_text is not None:
          self._err.add(e)
        return None
      if pal:
        return pal
    return None

  def make_palette(self, bg_color, is_sprite):
    """Construct the palette object from color_needs.

    bg_color: Background color.
    is_sprite: Whether this is a sprite palette.
    """
    pal = None
    # If sprite mode, and there's no bg color, we can figure it out based upon
    # how many empty tiles there need to be.
    if is_sprite and bg_color is None and not self._test_only_auto_sprite_bg:
      for color, num in self._needs_provider.counts():
        if num >= 0x40 and bg_color is None:
          bg_color = color
    # Make the palette from the color needs.
    guesser = guess_best_palette.GuessBestPalette()
    if bg_color is not None:
      guesser.set_bg_color(bg_color)
    color_sets = self._needs_provider.elems()
    try:
      pal = guesser.guess_palette(color_sets)
    except (errors.PaletteTooManySubsets, errors.TooManyPalettesError) as e:
      self._err.add(e)
      return None
    return pal

  def is_subset_of_one_of(self, needle, haystack):
    needle = set(needle)
    for elem in haystack:
      if needle <= set(elem):
        return True
    return False

  def maybe_find_palette_subset_errors(self):
    e = self._err.find_type(errors.PaletteTooManySubsets)
    if not e:
      return
    colors = e.colors
    to_merge = e.to_merge
    for block_y in range(self.blocks_y):
      for block_x in range(self.blocks_x):
        y = block_y * 2
        x = block_x * 2
        bcid = self._artifacts[y][x][ARTIFACT_BCID]
        block_color_needs = self._block_color_manifest.at(bcid)
        if self.is_subset_of_one_of(block_color_needs, e.colors):
          continue
        if self.is_subset_of_one_of(block_color_needs, e.to_merge):
          e.list_blocks.append([block_y, block_x])

  def process_to_artifacts(self, bg_mask, bg_fill, config):
    """Process the image and store data in the artifact table.

    For each block, look at each tile and get their color needs and
    dot profile. Save the ids in the artifact table.

    bg_mask: Background color mask, if mask is used.
    bg_fill: Background color fill.
    config: Configuration of ppu_memory
    """
    for block_y in range(self.blocks_y):
      for block_x in range(self.blocks_x):
        try:
          self.process_block(block_y, block_x, bg_mask, bg_fill,
                             config.is_sprite)
        except errors.PaletteOverflowError as e:
          print('palette error')
          self.collect_error(e, block_y, block_x, 0, 0, is_block=True)
          continue
    self._needs_provider = self._block_color_manifest
    if config.is_sprite:
      self._needs_provider = self._color_manifest

  def replace_mask_with_fill(self, bg_color_mask, bg_color_fill):
    """Replace the mask color by the fill color in the color manifest."""
    if bg_color_mask:
      for i in range(len(self._color_manifest)):
        colors = self._color_manifest.at(i)
        for j in range(len(colors)):
          if colors[j] == bg_color_mask:
            colors[j] = bg_color_fill

  def make_colorization(self, pal, config):
    """Select colorization for each position in the image.

    pal: Palette for this image.
    config: Configuration of ppu_memory
    """
    for g, gfx in enumerate(self._ppu_memory.gfx):
      nt_y, nt_x = (gfx.nt_y, gfx.nt_x)
      page_y = (g // self.screen_x) * nt_y
      page_x = (g  % self.screen_x) * nt_x
      if not config.is_sprite:
        # For each block, get the attribute aka the palette.
        for block_x in range(nt_x // 2):
          for block_y in range(nt_y // 2):
            y = block_y * 2
            x = block_x * 2
            (cid, did, bcid) = self._artifacts[y + page_y][x + page_x]
            color_needs = self._needs_provider.at(bcid)
            try:
              (pid, palette_option) = pal.select(color_needs)
            except IndexError:
              self._err.add(errors.PaletteNoChoiceError(y, x, color_needs))
              pid = 0
            for a,b in itertools.product(range(2),range(2)):
              gfx.colorization[y + a][x + b] = pid
      else:
        # For each tile, get the attribute aka the palette.
        for x in range(nt_x):
          for y in range(nt_y):
            (cid, did, bcid) = self._artifacts[y + page_y][x + page_x]
            color_needs = self._needs_provider.at(cid)
            try:
              (pid, palette_option) = pal.select(color_needs)
            except IndexError:
              self._err.add(errors.PaletteNoChoiceError(y, x, color_needs))
              pid = 0
            gfx.colorization[y][x] = pid

  def traverse_artifacts(self, traversal, pal, config):
    """Traverse the artifacts, building CHR and other ppu_memory data.

    traversal: Method of traversal
    pal: Palette for this image
    config: Configuration of ppu_memory
    """
    # Find empty tile.
    empty_did = self._dot_manifest.get(chr(0) * 64)
    empty_cid = self._color_manifest.get(chr(pal.bg_color) + chr(NULL) * 3)
    screen_y = screen_x = 0
    for g, gfx in enumerate(self._ppu_memory.gfx):
      nt_y, nt_x = (gfx.nt_y, gfx.nt_x)
      page_y = (g // self.screen_x) * 30
      page_x = (g  % self.screen_x) * 32
      # Traverse tiles in the artifact table, creating the chr and nametable.
      if traversal == 'horizontal':
        generator = ((y,x) for y in range(nt_y) for x in range(nt_x))
      elif traversal == 'vertical':
        generator = ((y,x) for x in range(nt_x) for y in range(nt_y))
      elif traversal == 'block':
        generator = ((y*2+i,x*2+j) for y in range(nt_y // 2) for
                     x in range(nt_x // 2) for i in range(2) for
                     j in range(2))
      elif traversal == '8x16':
        raise errors.UnknownLogicFailure('traverse using subclassed processor')
      for (y,x) in generator:
        (cid, did, bcid) = self._artifacts[y + page_y][x + page_x]
        pid = gfx.colorization[y][x]
        palette_option = pal.get(pid)
        color_needs = self._color_manifest.at(cid)
        if config.is_sprite and not config.is_locked_tiles:
          if empty_cid == cid and empty_did == did:
            gfx.nametable[y][x] = 0x100
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
        except errors.NametableOverflow as e:
          self._err.add(errors.NametableOverflow(e.chr_num, y, x))
          chr_num = 0
        if config.is_sprite:
          self._flip_bits[y + page_y][x + page_x] = flip_bits
        gfx.nametable[y][x] = chr_num
        if empty_cid == cid and empty_did == did:
          self._ppu_memory.empty_tile = chr_num

  def make_spritelist(self, traversal, pal, config):
    """Convert data from the nametable to create spritelist.

    traversal: Method of traversal
    """
    empty_did = self._dot_manifest.get(chr(0) * 64)
    empty_cid = self._color_manifest.get(chr(pal.bg_color) + chr(NULL) * 3)
    generator = ((y,x) for y in range(self.blocks_y * 2) for
                 x in range(self.blocks_x * 2))
    for (y,x) in generator:
      (cid, did, bcid) = self._artifacts[y][x]
      if empty_cid == cid and empty_did == did:
        continue
      tile = self._ppu_memory.gfx[0].nametable[y][x]
      if not config.allow_overflow or not 's' in config.allow_overflow:
        if len(self._ppu_memory.spritelist) >= 0x40:
          if not config.is_locked_tiles:
            self._err.add(errors.SpritelistOverflow(y, x))
          continue
      y_pos = y * 8 - 1 if y > 0 else 0
      x_pos = x * 8
      attr = self._ppu_memory.gfx[0].colorization[y][x] | self._flip_bits[y][x]
      self._ppu_memory.spritelist.append([y_pos, tile, attr, x_pos])

  def process_image(self, img, palette_text, bg_color_mask, bg_color_fill,
                    traversal, is_sprite, is_locked_tiles, lock_sprite_flips,
                    allow_overflow):
    """Process an image, creating the ppu_memory necessary to display it.

    img: Pixel art image.
    palette_text: Optional string representing a palette to be parsed.
    bg_color_mask: Background color mask, if a mask is being used.
    bg_color_fill: Background color fill.
    traversal: Strategy for traversing the nametable.
    is_sprite: Whether the image is of sprites.
    is_locked_tiles: Whether tiles are locked into place. If so, do not
        merge duplicates, and only handle first 256 tiles.
    lock_sprite_flips: Whether to only lock sprite flip bits.
    allow_overflow: Characters representing components. Only 'c' and 's'
        are supported.
    """
    self.initialize()
    self.load_image(img)
    # Assign configuration.
    config = ppu_memory.PpuMemoryConfig(is_sprite=is_sprite,
                                        is_locked_tiles=is_locked_tiles,
                                        lock_sprite_flips=lock_sprite_flips,
                                        allow_overflow=allow_overflow)
    if 'c' in config.allow_overflow:
      self._ppu_memory.upgrade_chr_set_to_bank()
    # Parse the palette if provided.
    pal = None
    if palette_text or self.img.palette:
      pal = self.parse_palette(palette_text, bg_color_fill)
    # In order to auto detect the background color, have to count color needs.
    # Counting is slower, so don't do it by default.
    if config.is_sprite and bg_color_fill is None:
      self._color_manifest = id_manifest.CountingIdManifest()
    # Process each block and tile to build artifacts.
    self.process_to_artifacts(bg_color_mask, bg_color_fill, config)
    if self._err.has():
      return
    # Make the palette, if it doesn't already exist.
    if not pal:
      pal = self.make_palette(bg_color_fill, config.is_sprite)
    if not pal:
      self.maybe_find_palette_subset_errors()
      return
    if not config.is_sprite:
      self._ppu_memory.palette_nt = pal
    else:
      self._ppu_memory.palette_spr = pal
    # Replace mask with fill.
    self.replace_mask_with_fill(bg_color_mask, bg_color_fill)
    # Make colorization for each block and tile.
    self.make_colorization(pal, config)
    if self._err.has():
      return
    # Traverse the artifacts, building chr and other ppu_memory.
    self.traverse_artifacts(traversal, pal, config)
    if self._err.has():
      return
    # Build spritelist if necessary.
    if config.is_sprite:
      self.make_spritelist(traversal, pal, config)
