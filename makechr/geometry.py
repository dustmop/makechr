import errors
import num_range
from direction_constants import *


class Point(object):
  def __init__(self, y, x):
    self.y = y
    self.x = x

  def __eq__(self, other):
    return self.y == other.y and self.x == other.x

  def __str__(self):
    return '#<Point y=%s x=%s>' % (self.y, self.x)

  def __repr__(self):
    return self.__str__()

  def move_point(self, dir, dist):
    if dir == DIR_UP:
      return Point(self.y - dist, self.x)
    elif dir == DIR_RIGHT:
      return Point(self.y, self.x + dist)
    elif dir == DIR_DOWN:
      return Point(self.y + dist, self.x)
    elif dir == DIR_LEFT:
      return Point(self.y, self.x - dist)

  def distance_from(self, other):
    if self.y == other.y:
      return self.x - other.x
    elif self.x == other.x:
      return self.y - other.y
    raise errors.GeometryError('points not in line with each other')


class Vertex(Point):
  def __init__(self, kind, y, x, idx=None):
    Point.__init__(self, y, x)
    if kind not in ['reflex', 'convex']:
      raise errors.GeometryError('invalid vertex type: "%s"' % kind)
    self.kind = kind
    self.idx = idx
    self.terminal = False

  @property
  def is_convex(self):
    return self.kind == 'convex'

  def mark_terminal(self):
    self.terminal = True

  def __str__(self):
    terminal_txt = ''
    if self.terminal:
      terminal_txt = ' terminal=true'
    return '#<Vertex kind=%s y=%s x=%s idx=%s%s>' % (
      self.kind, self.y, self.x, self.idx, terminal_txt)

  def __repr__(self):
    return self.__str__()


class Edge(object):
  def __init__(self, facing, y0, x0, y1, x1):
    self.done = False
    if y0 > y1:
      y0, y1 = y1, y0
    if x0 > x1:
      x0, x1 = x1, x0
    self.facing = facing
    if facing in [DIR_UP, DIR_DOWN]:
      if y0 != y1:
        raise errors.GeometryError('edge facing up/down needs same Y value')
      self.y0 = y0
      self.y1 = y0
      self.x0 = x0
      self.x1 = x1
    else:
      if x0 != x1:
        raise errors.GeometryError('edge facing left/right needs same X value')
      self.x0 = x0
      self.x1 = x0
      self.y0 = y0
      self.y1 = y1
    self.cover = None

  def clone(self):
    return Edge(self.facing, self.y0, self.x0, self.y1, self.x1)

  @staticmethod
  def from_endpoints(facing, endpoints):
    p0 = endpoints[0]
    p1 = endpoints[1]
    return Edge(facing, p0.y, p0.x, p1.y, p1.x)

  def mark_done(self, amount):
    if self.done:
      return
    if self.cover is None:
      self.cover = num_range.MultiRange()
    self.cover.add(amount)
    if self.cover == self.dim_to_range():
      self.done = True

  def calc_uncovered(self):
    if self.cover is None:
      return self
    r = self.cover.subtract_from(self.dim_to_range()).to_single_range()
    if r is None:
      return r
    if self.facing in [DIR_UP, DIR_DOWN]:
      return Edge(self.facing, self.y0, r.p0, self.y0, r.p1)
    else:
      return Edge(self.facing, r.p0, self.x0, r.p1, self.x0)

  @property
  def length(self):
    if self.facing in [DIR_UP, DIR_DOWN]:
      return self.x1 - self.x0
    else:
      return self.y1 - self.y0

  def get_endpoints(self):
    if self.facing in [DIR_DOWN, DIR_UP]:
      return [Point(self.y0, self.x0), Point(self.y0, self.x1)]
    else:
      return [Point(self.y0, self.x0), Point(self.y1, self.x0)]

  def x_to_range(self):
    return num_range.NumRange(self.x0, self.x1)

  def y_to_range(self):
    return num_range.NumRange(self.y0, self.y1)

  def dim_to_range(self):
    if self.facing in [DIR_UP, DIR_DOWN]:
      return self.x_to_range()
    else:
      return self.y_to_range()

  def __str__(self):
    if self.facing in [DIR_UP, DIR_DOWN]:
      cover = (' cover=%s' % (self.cover,)) if self.cover else ''
      return '#<Edge facing=%s y=%s x0=%s x1=%s%s>' % (
        self.facing, self.y0, self.x0, self.x1, cover)
    else:
      cover = (' cover=%s' % (self.cover,)) if self.cover else ''
      return '#<Edge facing=%s y0=%s y1=%s x=%s%s>' % (
        self.facing, self.y0, self.y1, self.x0, cover)

  def __repr__(self):
    return self.__str__()


class Rectangle(object):
  def __init__(self, top, left, bot, right):
    self.top = top
    self.left = left
    self.bot = bot
    self.right = right

  def exclusively_inside(self, y, x):
    return self.top < y < self.bot and self.left < x < self.right

  def get_side(self, d):
    if d == DIR_UP:
      return Edge(d, self.top, self.left, self.top, self.right)
    elif d == DIR_RIGHT:
      return Edge(d, self.top, self.right, self.bot, self.right)
    elif d == DIR_DOWN:
      return Edge(d, self.bot, self.left, self.bot, self.right)
    elif d == DIR_LEFT:
      return Edge(d, self.top, self.left, self.bot, self.left)

  @property
  def width(self):
    return self.right - self.left

  @property
  def height(self):
    return self.bot - self.top

  def __str__(self):
    return '#<Rectangle top=%s left=%s bot=%s right=%s>' % (
      self.top, self.left, self.bot, self.right)

  def __repr__(self):
    return self.__str__()
