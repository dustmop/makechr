class PaletteError(StandardError):
  def __init__(self, msg):
    self.msg = msg

  def __str__(self):
    return self.msg


class Palette(object):
  def __init__(self):
    self.bg_color = None
    self.pals = []

  def __str__(self):
    return ('P|' +
            '|'.join(['-'.join(['%02x' % c for c in row]) for row in self.pals])
            + '|')

  def set_bg_color(self, bg_color):
    self.bg_color = bg_color

  def add(self, p):
    if not self.bg_color in p:
      raise PaletteError('Background color not found in PaletteOption')
    self.pals.append([self.bg_color] + [c for c in p if c != self.bg_color])


