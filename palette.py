class Palette(object):
  def __init__(self):
    self.pals = []

  def __str__(self):
    return ('P|' +
            '|'.join(['-'.join(['%02x' % c for c in row]) for row in self.pals])
            + '|')

  def add(self, p):
    self.pals.append(p)


