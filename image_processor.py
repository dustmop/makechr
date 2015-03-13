import binary_output
import chr_tile
import errors
import guess_best_palette
import id_manifest
import rgb
from constants import *


# TODO: Try different image libraries
# TODO: Performance test
# TODO: Use actual command-line parsing

class ImageProcessor(object):

  # pixel_to_nescolor
  #
  # Given an rgb pixel, in the form (red, green, blue, *unused), from
  # PIL/pillow, find the corresponding index in the NES system palette that
  # most closely matches that color. RGB_XLAT makes this fast by caching
  # searches, and finding answers with a dictionary lookup. If the color cannot
  # be converted, return -1.
  #
  # pixel: An RGB color.
  def pixel_to_nescolor(self, pixel):
    # Note: If we convert to python3, use the (r, g, b, *unused) syntax.
    (r, g, b) = (pixel[0], pixel[1], pixel[2])
    color_num = r * 256 * 256 + g * 256 + b
    nc = rgb.RGB_XLAT.get(color_num)
    if not nc is None:
      return nc
    # Resolve color.
    found_nc = -1
    found_diff = float('infinity')
    for i,color_value in enumerate(rgb.RGB_COLORS):
      diff_r = abs(r - color_value / (256 * 256))
      diff_g = abs(g - (color_value / 256) % 256)
      diff_b = abs(b - color_value % 256)
      diff = diff_r + diff_g + diff_b
      if diff < found_diff:
        found_nc = i
        found_diff = diff
    if found_diff > rgb.COLOR_TOLERANCE:
      return -1
    rgb.RGB_XLAT[color_num] = found_nc
    return found_nc

  # add_nescolor_to_needs
  #
  # Add a nescolor to a list of needed nescolors. The needs array must be
  # at least length 4, with unused entries set to None.
  #
  # nc: A nescolor index, integer 0..63.
  # needs: An array of at least length 4, with unused entries set to None.
  def add_nescolor_to_needs(self, nc, needs):
    for i in xrange(4):
      if needs[i] == nc:
        return i
      if needs[i] is None:
        needs[i] = nc
        return i
    needs.append(nc)
    return len(needs) - 1

  # process_tile
  #
  # Process the tile to obtain its color needs and dot profile, verifying that
  # the tile contains colors that match the system palette, and does not contain
  # too many colors.
  #
  # img: The full pixel art image.
  # tile_y: The y position of the tile, 0..31.
  # tile_x: The x position of the tile, 0..29.
  # Returns the color_needs and dot_profile.
  def process_tile(self, img, tile_y, tile_x):
    (image_x, image_y) = img.size
    pixel_y = tile_y * TILE_SIZE
    pixel_x = tile_x * TILE_SIZE
    # Check if this tile overruns the image.
    if pixel_y + TILE_SIZE > image_y or pixel_x + TILE_SIZE > image_x:
      return None, None
    color_needs = [None] * 4
    dot_profile = [None] * (TILE_SIZE * TILE_SIZE)
    raw_pixels = img.load()
    for i in xrange(TILE_SIZE):
      for j in xrange(TILE_SIZE):
        y = pixel_y + i
        x = pixel_x + j
        p = raw_pixels[x, y]
        nc = self.pixel_to_nescolor(p)
        if nc == -1:
          raise errors.ColorNotAllowedError(p, tile_y, tile_x, i, j)
        idx = self.add_nescolor_to_needs(nc, color_needs)
        dot_profile[i * TILE_SIZE + j] = idx
    if len(color_needs) > 4:
      raise errors.PaletteOverflowError(tile_y, tile_x)
    return color_needs, dot_profile

  # process_block
  #
  # Process the individual tiles in the block.
  #
  # img: The full pixel art image.
  # block_y: The y position of the block, 0..15.
  # block_x: The x position of the block, 0..14.
  def process_block(self, img, block_y, block_x):
    block_color_needs = set([])
    y = block_y * 2
    x = block_x * 2
    for i in xrange(2):
      for j in xrange(2):
        (color_needs, dot_profile) = self.process_tile(img, y + i, x + j)
        cid = self._color_manifest.id(color_needs)
        did = self._dot_manifest.id(dot_profile)
        self._artifacts[y + i][x + j] = [cid, did, None, None]
        block_color_needs |= set(color_needs)
    bcid = self._block_color_manifest.id(block_color_needs)
    self._artifacts[y][x][ARTIFACT_BCID] = bcid

  def get_dot_xlat(self, color_needs, palette_option):
    dot_xlat = []
    for c in color_needs:
      if c is None:
        continue
      for i,p in enumerate(palette_option):
        if c == p:
          dot_xlat.append(i)
          break
      else:
        raise IndexError
    return dot_xlat

  def get_nametable_num(self, xlat, did):
    key = str([did] + xlat)
    if not key in self._nametable_cache:
      dot_profile = self._dot_manifest.get(did)
      tile = chr_tile.ChrTile()
      for row in xrange(8):
        for col in xrange(8):
          i = row * 8 + col
          val = xlat[dot_profile[i]]
          tile.set(val, col, row)
      nt_num = len(self._chr_data)
      self._chr_data.append(tile)
      self._nametable_cache[key] = nt_num
    return self._nametable_cache[key]

  def process_image(self, img):
    self._nametable_cache = {}
    self._chr_data = []
    self._output = binary_output.BinaryOutput()
    self._color_manifest = id_manifest.IdManifest()
    self._dot_manifest = id_manifest.IdManifest()
    self._block_color_manifest = id_manifest.IdManifest()
    self._artifacts = [row[:] for row in
                       [[None]*(NUM_BLOCKS_X*2)]*(NUM_BLOCKS_Y*2)]
    # For each block, look at each tile and get their color needs and
    # dot profile. Save the corresponding ids in the artifact table.
    for block_y in xrange(NUM_BLOCKS_Y):
      for block_x in xrange(NUM_BLOCKS_X):
        self.process_block(img, block_y, block_x)
    # Make the palette from the color needs.
    guesser = guess_best_palette.GuessBestPalette()
    self._palette = guesser.make_palette(self._block_color_manifest.elems())
    # For each block, get the attribute aka the palette.
    for block_y in xrange(NUM_BLOCKS_Y):
      for block_x in xrange(NUM_BLOCKS_X):
        y = block_y * 2
        x = block_x * 2
        (cid, did, bcid, unused) = self._artifacts[y][x]
        block_color_needs = self._block_color_manifest.get(bcid)
        (pid, palette_option) = self._palette.select(block_color_needs)
        # TODO: Maybe better to get palette per block instead of assigning it
        # to each tile?
        self._artifacts[y][x][ARTIFACT_PID] = pid
        self._artifacts[y][x+1][ARTIFACT_PID] = pid
        self._artifacts[y+1][x][ARTIFACT_PID] = pid
        self._artifacts[y+1][x+1][ARTIFACT_PID] = pid
    # For each tile in the artifact table, create the chr and nametable.
    for y in xrange(NUM_BLOCKS_Y * 2):
      for x in xrange(NUM_BLOCKS_X * 2):
        (cid, did, pid, unused) = self._artifacts[y][x]
        palette_option = self._palette.get(pid)
        color_needs = self._color_manifest.get(cid)
        dot_xlat = self.get_dot_xlat(color_needs, palette_option)
        nt_num = self.get_nametable_num(dot_xlat, did)
        self._artifacts[y][x][ARTIFACT_NT] = nt_num
    # Output.
    self._output.save_nametable('nametable.dat', self._artifacts)
    self._output.save_chr('chr.dat', self._chr_data)
    self._output.save_palette('palette.dat', self._palette)
    self._output.save_attribute('attribute.dat', self._artifacts)
    print('Number of dot-profiles: {0}'.format(self._dot_manifest.size()))
    print('Number of tiles: {0}'.format(len(self._chr_data)))
    print('Palette: {0}'.format(self._palette))
