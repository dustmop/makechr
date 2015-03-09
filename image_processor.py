import errors
import guess_best_palette
import rgb


# TODO: Try different image libraries
# TODO: Performance test
# TODO: Use actual command-line parsing

WIDTH = 256
HEIGHT = 240
BLOCK_SIZE = 16
TILE_SIZE = 8
NUM_BLOCKS_X = WIDTH / BLOCK_SIZE
NUM_BLOCKS_Y = HEIGHT / BLOCK_SIZE


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
    tile_y = block_y * 2
    tile_x = block_x * 2
    for i in xrange(2):
      for j in xrange(2):
        (color_needs, dot_profile) = self.process_tile(img, tile_y + i,
                                                       tile_x + j)
        key = str(color_needs)
        if key in self._color_manifest:
          cid = self._color_manifest[key]
        else:
          cid = len(self._color_manifest)
          self._color_manifest[key] = cid
        key = str(dot_profile)
        if key in self._dot_manifest:
          did = self._dot_manifest[key]
        else:
          did = len(self._dot_manifest)
          self._dot_manifest[key] = did
        self._artifacts[tile_y + i][tile_x + j] = (cid, did)

  def process_image(self, img):
    self._color_manifest = {}
    self._dot_manifest = {}
    self._artifacts = [[None] * (NUM_BLOCKS_X * 2)] * (NUM_BLOCKS_Y * 2)
    for y in xrange(NUM_BLOCKS_Y):
      for x in xrange(NUM_BLOCKS_X):
        self.process_block(img, y, x)
    guesser = guess_best_palette.GuessBestPalette()
    self._palette = guesser.make_palette(self._color_manifest)
    print('Number of dot-profiles: {0}'.format(len(self._dot_manifest)))
    print('Palette: {0}'.format(self._palette))
