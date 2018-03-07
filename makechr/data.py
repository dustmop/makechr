class Span(object):
  """Span has a start side on the left, and finish side on the right."""

  def __init__(self, left=None, right=None):
    self.left = left
    self.right = right

  def same_as(self, other):
    return self.left == other.left and self.right == other.right

  def fully_left(self, other):
    return self.right <= other.left

  def fully_right(self, other):
    return self.left >= other.right

  def contains(self, num):
    return self.left <= num <= self.right

  def overlap(self, other):
    return (self.contains(other.left) or self.contains(other.right) or
            other.contains(self.left) or other.contains(self.right))

  def __repr__(self):
    return '<Span L=%s R=%s>' % (self.left, self.right)

  def __cmp__(self, other):
    if self.left < other.left:
      return -1
    if self.right < other.right:
      return -1
    if self.left > other.left:
      return 1
    if self.right > other.right:
      return 1
    return 0


class Zone(Span):
  """A rectangle which contains 4 sides. May have ambiguous sides."""

  def __init__(self, left=None, right=None, top=None, bottom=None,
               maybe_left=None, maybe_right=None):
    Span.__init__(self, left, right)
    self.top = top
    self.bottom = bottom
    self.maybe_left = maybe_left
    self.maybe_right = maybe_right

  def each_sprite(self, is_tall):
    width = 8
    height = 16 if is_tall else 8
    y = self.top
    while y < self.bottom:
      x = self.left
      while x < self.right:
        yield y,x
        if is_tall:
          yield y+8,x
        x += width
        if 0 < self.right - x < width:
          x = self.right - width
      y += height
      if 0 < self.bottom - y < height:
        y = self.bottom - height

  def rect(self):
    return [self.left, self.top, self.right-1, self.bottom-1]

  def __repr__(self):
    maybe_bottom = ''
    if self.bottom is not None:
      maybe_bottom = ' B=%s' % self.bottom
    return ('<Zone L=%s R=%s T=%s%s>' % (
      [self.left, self.maybe_left] if self.maybe_left else self.left,
      [self.maybe_right, self.right] if self.maybe_right else self.right,
      self.top, maybe_bottom))


class Region(Span):
  """A span which also contains a list of zones."""

  def __init__(self, left, right):
    Span.__init__(self, left, right)
    self.zones = []

  @staticmethod
  def make_from(y, span):
    make = Region(span.left, span.right)
    make.zones.append(Zone(left=span.left, right=span.right, top=y))
    return make

  def __repr__(self):
    return '<Region L=%s R=%s>' % (self.left, self.right)

