class CommandLineArgError(Exception):
  def __init__(self, msg):
    self.msg = msg

  def __str__(self):
    return self.msg


class PaletteOverflowError(Exception):
  def __init__(self, elem_y, elem_x, is_block=False):
    if is_block:
      self.block_y = elem_y
      self.block_x = elem_x
      self.tile_y = None
      self.tile_x = None
    else:
      self.block_y = None
      self.block_x = None
      self.tile_y = elem_y
      self.tile_x = elem_x

  def __str__(self):
    if self.block_y and self.block_x:
      return '@ block (%dy,%dx)' % (self.block_y, self.block_x)
    else:
      return '@ tile (%dy,%dx)' % (self.tile_y, self.tile_x)


class PaletteBackgroundColorMissingError(Exception):
  def __str__(self):
    return 'Background color not set on palette'


class PaletteBackgroundColorConflictError(Exception):
  def __init__(self, pal_color, bg_color):
    self.pal_color = pal_color
    self.bg_color = bg_color

  def __str__(self):
    return 'between palette /%x/ <> bg color /%x/' % (
      self.pal_color, self.bg_color)


class PaletteInconsistentError(Exception):
  def __init__(self, color_1, color_2):
    self.color_1 = color_1
    self.color_2 = color_2

  def __str__(self):
    return 'Background colors don\'t match %s <> %s' % (
      self.color_1, self.color_2)


class PaletteParseError(Exception):
  def __init__(self, input, i, msg):
    self.input = input
    self.i = i
    self.msg = msg

  def __str__(self):
    text = (self.msg + (' at position %d\n"' % self.i) +
            self.input + '"\n ' + (' ' * self.i) + '^')
    return text


class ColorNotAllowedError(Exception):
  def __init__(self, pixel, tile_y, tile_x, y, x):
    self.pixel = pixel
    self.tile_y = tile_y
    self.tile_x = tile_x
    self.y = y
    self.x = x
    self.count = 1

  def get_color(self):
    return self.pixel[0] * 256 * 256 + self.pixel[1] * 256 + self.pixel[2]

  def __str__(self):
    text = ('@ tile (%dy,%dx) and pixel (%dy,%dx) - "%02x,%02x,%02x"' %
            (self.tile_y, self.tile_x, self.y, self.x,
             self.pixel[0], self.pixel[1], self.pixel[2]))
    if self.count > 1:
      text = text + ' (%d times)' % self.count
    return text


class TooManyPalettesError(Exception):
  def __init__(self, colors, to_merge=None):
    self.colors = colors
    self.to_merge = to_merge

  def to_text(self, colors):
    return '/'.join(['-'.join(['%02x' % c for c in row]) for row in colors])

  def __str__(self):
    text = self.to_text(self.colors)
    if self.to_merge:
      text = text + ',MERGE={' + self.to_text(self.to_merge) + '}'
    return text


class FileFormatError(Exception):
  def __init__(self, actual, size):
    self.actual = actual
    self.size = size

  def __str__(self):
    if self.size:
      return 'FileFormatError: Expected size %d but got %d' % (
        self.size, self.actual)
    else:
      return 'FileFormatError'


class UnknownStrategy(Exception):
  def __init__(self, text):
    self.text = text

  def __str__(self):
    return 'UnknownStrategy: "%s"' % self.text


class ErrorCollector(object):
  def __init__(self):
    self.e = []
    self.dup = []
    self.color_not_allowed_dups = {}

  def add(self, error):
    if isinstance(error, ColorNotAllowedError):
      c = error.get_color()
      if c in self.color_not_allowed_dups:
        idx = self.color_not_allowed_dups[c]
        self.e[idx].count += 1
        self.dup.append(error)
        return
      self.color_not_allowed_dups[c] = len(self.e)
    self.e.append(error)

  def has(self):
    return len(self.e)

  def get(self, include_dups=False):
    if include_dups:
      return self.e + self.dup
    return self.e
