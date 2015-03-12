class PaletteError(StandardError):
  def __init__(self, msg):
    self.msg = msg

  def __str__(self):
    return self.msg


class Palette(object):
  def __init__(self):
    self.bg_color = None
    self.pals = []
    self.pal_as_sets = []

  def __str__(self):
    return ('P/' +
            '/'.join(['-'.join(['%02x' % c for c in row]) for row in self.pals])
            + '/')

  def set_bg_color(self, bg_color):
    self.bg_color = bg_color

  def add(self, p):
    if not self.bg_color in p:
      raise PaletteError('Background color not found in PaletteOption')
    p = [self.bg_color] + [c for c in p if c != self.bg_color]
    self.pals.append(p)
    self.pal_as_sets.append(set(p))

  def select(self, color_needs):
    want = set([c for c in color_needs if not c is None])
    for i,p in enumerate(self.pal_as_sets):
      if want <= p:
        break
    else:
      raise IndexError
    return (i, self.pals[i])
