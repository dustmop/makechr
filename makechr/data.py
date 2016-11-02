class Span(object):
  """Span represents a start side on the left, and finish side on the right."""

  def __init__(self, left, right):
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


class Zone(object):
  """A rectangle which contains 4 sides. May have ambiguous sides."""

  def __init__(self, top=None, left=None, right=None, bottom=None,
               left_range=None, right_range=None):
    self.top = top
    self.left = left
    self.right = right
    self.bottom = bottom
    self.left_range = left_range
    self.right_range = right_range

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
    if not self.bottom is None:
      maybe_bottom = ' B=%s' % self.bottom
    return ('<Zone T=%s L=%s R=%s%s>' % (
      self.top, self.left_range or self.left, self.right_range or self.right,
      maybe_bottom))
