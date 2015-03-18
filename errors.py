class PaletteOverflowError(Exception):
  def __init__(self, tile_y, tile_x):
    self.tile_y = tile_y
    self.tile_x = tile_x

  def __str__(self):
    return '@ tile (%dy,%dx)' % (self.tile_y, self.tile_x)


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
  def __init__(self, colors):
    self.colors = colors

  def __str__(self):
    accum = []
    for row in self.colors:
      p = '-'.join(['%02x' % c for c in row])
      accum.append(p)
    return '/'.join(accum)


class ErrorCollector(object):
  def __init__(self):
    self.e = []

  def add(self, error):
    self.e.append(error)

  def has(self):
    return len(self.e)

  def get(self):
    return self.e
