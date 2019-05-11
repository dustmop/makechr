class CommandLineArgError(Exception):
  def __init__(self, msg):
    self.msg = msg

  def __str__(self):
    return self.msg


class PaletteOverflowError(Exception):
  def __init__(self, elem_y=None, elem_x=None, is_block=False):
    if is_block:
      self.block_y = elem_y
      self.block_x = elem_x
      self.tile_y = None
      self.tile_x = None
      self.pixel_y = None
      self.pixel_x = None
    else:
      self.block_y = None
      self.block_x = None
      self.tile_y = elem_y
      self.tile_x = elem_x
      self.pixel_y = None
      self.pixel_x = None

  def __str__(self):
    if self.pixel_y is not None and self.pixel_x is not None:
      return '@ pixel (%dy,%dx)' % (self.pixel_y, self.pixel_x)
    elif self.block_y is not None and self.block_x is not None:
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
    return 'between palette /%02x/ <> bg color /%02x/' % (
      self.pal_color, self.bg_color)


class PaletteBackgroundFillColorSeemsWrong(Exception):
  def __init__(self, bg_seems, bg_fill):
    self.bg_seems = bg_seems
    self.bg_fill = bg_fill

  def __str__(self):
    return 'Background color seems to be /%02x/, but bg_fill is /%02x/' % (
      self.bg_seems, self.bg_fill)


class PaletteInconsistentError(Exception):
  def __init__(self, color_1, color_2):
    self.color_1 = color_1
    self.color_2 = color_2

  def __str__(self):
    return 'Background colors don\'t match %s <> %s' % (
      self.color_1, self.color_2)


class PaletteNoChoiceError(Exception):
  def __init__(self, tile_y, tile_x, color_needs):
    self.tile_y = tile_y
    self.tile_x = tile_x
    self.color_needs = color_needs

  def __str__(self):
    needs = '-'.join(['%02x' % e for e in self.color_needs])
    return 'at (%dy,%dx) for %s' % (self.tile_y, self.tile_x, needs)


class PalettesUnsuitable(Exception):
  def __init__(self, color_needs, palette_option):
    self.needs = ','.join(['$%02x' % e for e in color_needs])
    self.option = '/'.join(['$%02x' % e for e in palette_option])

  def __str__(self):
    return 'needs=%s option=%s' % (self.needs, self.option)


class PaletteParseError(Exception):
  def __init__(self, input, i, msg):
    self.input = input
    self.i = i
    self.msg = msg

  def __str__(self):
    text = (self.msg + (' at position %d\n"' % self.i) +
            self.input + '"\n ' + (' ' * self.i) + '^')
    return text


class PaletteExtractionError(Exception):
  def __init__(self, msg):
    self.msg = msg

  def __str__(self):
    return self.msg + '.\n  Disable extraction using the flag "-p -"'


class CouldntConvertRGB(Exception):
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
    text = (': R %02x, G %02x, B %02x @ tile (%dy,%dx) / pixel (%dy,%dx)' %
            (self.pixel[0], self.pixel[1], self.pixel[2],
             self.tile_y, self.tile_x,
             self.tile_y * 8 + self.y, self.tile_x * 8 + self.x))
    if self.count > 1:
      text = text + ' (%d times)' % self.count
    return text


class PaletteTooManySubsets(Exception):
  def __init__(self, colors, to_merge=None):
    self.colors = colors
    self.to_merge = to_merge
    self.list_blocks = []

  def to_text(self, colors):
    return ','.join(['-'.join(['%02x' % c for c in row]) for row in colors])

  def __str__(self):
    text = self.to_text(self.colors)
    if self.to_merge:
      text = ('- valid: ' + text + '\n' +
              'subsets that can\'t be merged: [' +
              self.to_text(self.to_merge) + ']')
    return text


class TooManyPalettesError(Exception):
  pass


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


class UnknownLogicFailure(Exception):
  def __init__(self, text):
    self.text = text

  def __str__(self):
    return 'UnknownLogicFailure: "%s"' % self.text


class UnknownMemoryKind(Exception):
  def __init__(self, text):
    self.text = text

  def __str__(self):
    return 'UnknownMemoryType: "%s"' % self.text


class NametableOverflow(Exception):
  def __init__(self, chr_num, tile_y=0, tile_x=0):
    self.chr_num = chr_num
    self.tile_y = tile_y
    self.tile_x = tile_x

  def __str__(self):
    return '%d at tile (%dy,%dx)' % (self.chr_num, self.tile_y, self.tile_x)


class ChrPageFull(Exception):
  pass


class SpritelistOverflow(Exception):
  def __init__(self, tile_y=0, tile_x=0):
    self.tile_y = tile_y
    self.tile_x = tile_x

  def __str__(self):
    return 'at tile (%dy,%dx)' % (self.tile_y, self.tile_x)


class NametableNotFoundError(Exception):
  def __init__(self, name):
    self.name = name

  def __str__(self):
    return 'Not found: "%s"' % self.name


class MakepalBorderNotFound(Exception):
  pass


class MakepalInvalidFormat(Exception):
  pass


class GeometryError(Exception):
  def __init__(self, msg):
    self.msg = msg

  def __str__(self):
    return 'GeometryError: %s' % self.msg


class AlgorithmError(Exception):
  def __init__(self, msg):
    self.msg = msg

  def __str__(self):
    return 'AlgorithmError: %s' % self.msg


class ErrorCollector(object):
  def __init__(self):
    self.errs = []
    self.dup = []
    self.color_not_allowed_dups = {}
    self.nametable_overflow_idx = None
    self.spritelist_overflow_idx = None

  def add(self, error):
    if isinstance(error, CouldntConvertRGB):
      c = error.get_color()
      if c in self.color_not_allowed_dups:
        idx = self.color_not_allowed_dups[c]
        self.errs[idx].count += 1
        self.dup.append(error)
        return
      self.color_not_allowed_dups[c] = len(self.errs)
    if isinstance(error, NametableOverflow):
      if self.nametable_overflow_idx is None:
        self.nametable_overflow_idx = len(self.errs)
      else:
        idx = self.nametable_overflow_idx
        self.errs[idx].chr_num = error.chr_num
        return
    if isinstance(error, SpritelistOverflow):
      if self.spritelist_overflow_idx is None:
        self.spritelist_overflow_idx = len(self.errs)
      else:
        return
    self.errs.append(error)

  def has(self):
    return len(self.errs)

  def get(self, include_dups=False):
    if include_dups:
      return self.errs + self.dup
    return self.errs

  def find(self, y, x):
    if y is None or x is None:
      return None
    for e in self.errs:
      if hasattr(e, 'tile_y') and hasattr(e, 'tile_x'):
        tile_y, tile_x = getattr(e, 'tile_y'), getattr(e, 'tile_x')
        if y == tile_y and x == tile_x:
          return e
      if hasattr(e, 'block_y') and hasattr(e, 'block_x'):
        block_y, block_x = getattr(e, 'block_y'), getattr(e, 'block_x')
        if y / 2 == block_y and x / 2 == block_x:
          return e
      if hasattr(e, 'list_blocks'):
        for block_y, block_x in getattr(e, 'list_blocks'):
          if y / 2 == block_y and x / 2 == block_x:
            return e
    return None

  def find_type(self, t):
    for e in self.errs:
      if type(e) is t:
        return e
    return None
