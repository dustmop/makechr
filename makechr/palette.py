import errors
import string


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
    self.pal_as_sets = []
    for p in self.pals:
      p[0] = self.bg_color
      self.pal_as_sets.append(set(p))

  def add(self, p):
    if self.bg_color is None:
      raise errors.PaletteBackgroundColorMissingError()
    elif p[0] == 0:
      pass
    elif self.bg_color != p[0]:
      raise errors.PaletteBackgroundColorConflictError(p[0], self.bg_color)
    p = [self.bg_color] + p[1:]
    self.pals.append(p)
    self.pal_as_sets.append(set(p))

  def select(self, color_needs):
    want = set([c for c in color_needs if not c is 0xff])
    for i,p in enumerate(self.pal_as_sets):
      if want <= p:
        break
    else:
      raise IndexError
    return (i, self.pals[i])

  def get(self, i):
    if i < len(self.pals):
      return self.pals[i]

  def to_bytes(self):
    bytes = bytearray()
    for p in self.pals:
      bytes += bytearray(p)
    return bytes


class PaletteParser(object):
  def parse(self, text):
    self.i = 0
    self.text = text
    self.fetch_literal('P') or self.die('Expected: "P"')
    self.fetch_literal('/') or self.die('Expected: "/"')
    pal = Palette()
    for n in xrange(4):
      row = []
      val = self.fetch_hex()
      if val is None:
        break
      row.append(val)
      pal.set_bg_color(val)
      for q in xrange(3):
        if not self.fetch_literal('-'):
          break
        val = self.fetch_hex()
        if val is None:
          self.die('Invalid hex value')
        row.append(val)
      self.fetch_literal('/') or self.die('Expected: "/"')
      pal.add(row)
    self.fetch_done() or self.die('Expected: end of input')
    return pal

  def fetch_literal(self, want):
    if self.i >= len(self.text):
      return False
    if self.text[self.i] == want:
      self.i += 1
      return True
    return False

  def fetch_hex(self):
    if self.i + 1 >= len(self.text):
      return None
    if not self.text[self.i] in string.hexdigits:
      return None
    if not self.text[self.i + 1] in string.hexdigits:
      return None
    val = int(self.text[self.i:self.i + 2], 16)
    self.i += 2
    return val

  def fetch_done(self):
    return self.i >= len(self.text)

  def die(self, msg):
    raise errors.PaletteParseError(self.text, self.i, msg)
