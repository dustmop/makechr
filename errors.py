class PaletteOverflowError(Exception):
  def __init__(self, elem_y, elem_x, is_block=False):
    self.elem_y = elem_y
    self.elem_x = elem_x
    self.is_block = is_block

  def __str__(self):
    elem_type = 'block' if self.is_block else 'tile'
    return '@ %s (%dy,%dx)' % (elem_type, self.elem_y, self.elem_x)


class ColorNotAllowedError(Exception):
  def __init__(self, pixel, tile_y, tile_x, y, x):
    self.pixel = pixel
    self.tile_y = tile_y
    self.tile_x = tile_x
    self.y = y
    self.x = x

  def __str__(self):
    return ('@ tile (%dy,%dx) and pixel (%dy,%dx) - "%02x,%02x,%02x"' %
            (self.tile_y, self.tile_x, self.y, self.x,
             self.pixel[0], self.pixel[1], self.pixel[2]))


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


class ErrorCollector(object):
  def __init__(self):
    self.e = []

  def add(self, error):
    self.e.append(error)

  def has(self):
    return len(self.e)

  def get(self):
    return self.e
