import collections
from PIL import Image
import sys

# TODO: Multiple files
# TODO: Try different image libraries
# TODO: Performance test
# TODO: Use actual command-line parsing

WIDTH = 256
HEIGHT = 256
BLOCK_SIZE = 16
TILE_SIZE = 8
NUM_BLOCKS_X = WIDTH / BLOCK_SIZE
NUM_BLOCKS_Y = HEIGHT / BLOCK_SIZE

COLOR_TOLERANCE = 64


# From: http://www.thealmightyguru.com/Games/Hacking/Wiki/index.php?title=NES_Palette
                # 00        10        20        30
RGB_COLORS = [[0x7c7c7c, 0xbcbcbc, 0xf8f8f8, 0xfcfcfc], # gray
              [0x0000fc, 0x0078f8, 0x3cbcfc, 0xa4e4fc], # blue
              [0x0000bc, 0x0058f8, 0x6888fc, 0xb8b8f8], # blue dark
              [0x4428bc, 0x6844fc, 0x9878f8, 0xd8b8f8], # purple
              [0x940084, 0xd800cc, 0xf878f8, 0xf8b8f8], # pink
              [0xa80020, 0xe40058, 0xf85898, 0xf8a4c0], # red
              [0xa81000, 0xf83800, 0xf87858, 0xf0d0b0], # orange
              [0x881400, 0xe45c10, 0xfca044, 0xfce0a8], # orange dark
              [0x503000, 0xac7c00, 0xf8b800, 0xf8d878], # yellow
              [0x007800, 0x00b800, 0xb8f818, 0xd8f878], # green light
              [0x006800, 0x00a800, 0x58d854, 0xb8f8b8], # green
              [0x005800, 0x00a844, 0x58f898, 0xb8f8d8], # green dark
              [0x004058, 0x008888, 0x00e8d8, 0x00fcfc], # blue green
              [0x000000, 0x2c2c2c, 0x787878, 0xf8d8f8], # gray dark
              [0x000000, 0x000000, 0x000000, 0x000000], # black 1
              [0x000000, 0x000000, 0x000000, 0x000000], # black 2
              ]



def transpose(matrix):
  return [list(k) for k in zip(*matrix)]


def flatten(matrix):
  return [e for sublist in matrix for e in sublist]


def to_lookup_table(elems):
  answer = {}
  for i,val in enumerate(elems):
    answer[val] = i
  # Set black.
  answer[0] = 0xf
  return answer


RGB_COLORS = flatten(transpose(RGB_COLORS))
RGB_XLAT = to_lookup_table(RGB_COLORS)


class TooManyColorsError(Exception):
  def __init__(self, tile_y, tile_x):
    self.tile_y = tile_y
    self.tile_x = tile_x

  def __str__(self):
    return repr('@ tile (%dy,%dx)' % (self.tile_y, self.tile_x))


class ColorNotAllowedError(Exception):
  def __init__(self, pixel, tile_y, tile_x, y, x):
    self.pixel = pixel
    self.tile_y = tile_y
    self.tile_x = tile_x
    self.y = y
    self.x = x

  def __str__(self):
    return repr('%x %x %x @ tile (%dy,%dx) and pixel (%dy,%dx)' %
                (self.pixel[0], self.pixel[1], self.pixel[2],
                 self.tile_y, self.tile_x, self.y, self.x))


# pixel_to_nescolor
#
# Given an rgb pixel, in the form (red, green, blue, *unused), from PIL/pillow,
# find the corresponding index in the NES system palette that most closely
# matches that color. RGB_XLAT makes this fast by caching searches, and finding
# answers with a dictionary lookup. If the color cannot be converted, return -1.
#
# pixel: An RGB color.
def pixel_to_nescolor(pixel):
  # Note: If we convert to python3, use the (r, g, b, *unused) syntax.
  (r, g, b) = (pixel[0], pixel[1], pixel[2])
  color_num = r * 256 * 256 + g * 256 + b
  nc = RGB_XLAT.get(color_num)
  if not nc is None:
    return nc
  # Resolve color.
  found_nc = -1
  found_diff = float('infinity')
  for i,rgb in enumerate(RGB_COLORS):
    diff_r = abs(r - rgb / (256 * 256))
    diff_g = abs(g - (rgb / 256) % 256)
    diff_b = abs(b - rgb % 256)
    diff = diff_r + diff_g + diff_b
    if diff < found_diff:
      found_nc = i
      found_diff = diff
  if found_diff > COLOR_TOLERANCE:
    return -1
  RGB_XLAT[color_num] = found_nc
  return found_nc


# add_nescolor_to_needs
#
# Add a nescolor to a list of needed nescolors. The needs array must be
# at least length 4, with unused entries set to None.
#
# nc: A nescolor index, integer 0..63.
# needs: An array of at least length 4, with unused entries set to None.
def add_nescolor_to_needs(nc, needs):
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
def process_tile(img, tile_y, tile_x):
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
      nc = pixel_to_nescolor(p)
      if nc == -1:
        raise ColorNotAllowedError(p, tile_y, tile_x, i, j)
      idx = add_nescolor_to_needs(nc, color_needs)
      dot_profile[i * TILE_SIZE + j] = idx
  if len(color_needs) > 4:
    raise TooManyColorsError(tile_y, tile_x)
  return color_needs, dot_profile


# process_block
#
# Process the individual tiles in the block.
#
# img: The full pixel art image.
# block_y: The y position of the block, 0..15.
# block_x: The x position of the block, 0..14.
# profile_tally: A map from each dot_profile to how many times it has appeared.
def process_block(img, block_y, block_x, profile_tally):
  tile_y = block_y * 2
  tile_x = block_x * 2
  for i in xrange(2):
    for j in xrange(2):
      (color_needs, dot_profile) = process_tile(img, tile_y + i, tile_x + j)
      profile_tally[str(dot_profile)] += 1


def process_image(img):
  profile_tally = collections.defaultdict(int)
  for y in xrange(NUM_BLOCKS_Y):
    for x in xrange(NUM_BLOCKS_X):
      process_block(img, y, x, profile_tally)
  print('Number of dot-profiles: {0}'.format(len(profile_tally)))


def run():
  filename = sys.argv[1]
  img = Image.open(filename)
  process_image(img)


if __name__ == '__main__':
  run()
