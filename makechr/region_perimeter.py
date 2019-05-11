import errors
import geometry
import math
import num_range
from direction_constants import *


INFINITY = 9999


class RegionPerimeter(object):
  def __init__(self, init_y, init_x):
    self.edges = []
    self.vertices = []
    self.min_y = self.max_y = self.start_y = self.curr_y = init_y
    self.min_x = self.max_x = self.start_x = self.curr_x = init_x
    self.rects = []
    self.count = 0

  def __str__(self):
    accum = []
    for v in self.vertices:
      accum.append('y%s,x%s' % (v.y, v.x))
    return '#<RegionPerimeter %s points=[%s]>' % (len(accum), ' '.join(accum))

  def __repr__(self):
    return self.__str__()

  def add(self, dir, point_y, point_x, next_dir):
    self.count += 1
    if self.count >= 128:
      raise errors.AlgorithmError('loop detected at y=%s, x=%s' %
                                  (point_y, point_x))
    # Adjust
    if dir == DIR_DOWN:
      point_x += 1
    if dir == DIR_LEFT:
      point_y += 1
    if next_dir == DIR_DOWN:
      point_x += 1
    elif next_dir == DIR_LEFT:
      point_y += 1
    # Edge
    edge = geometry.Edge(rotate_dir_cw(dir), self.curr_y, self.curr_x,
                         point_y, point_x)
    self.edges.append(edge)
    # Vertex
    kind = 'convex' if next_dir == rotate_dir_cw(dir) else 'reflex'
    self.vertices.append(geometry.Vertex(kind, point_y, point_x,
                                         len(self.vertices)))
    # Border
    if point_y < self.min_y:
      self.min_y = point_y
    if point_y > self.max_y:
      self.max_y = point_y
    if point_x < self.min_x:
      self.min_x = point_x
    if point_x > self.max_x:
      self.max_x = point_x
    # Done?
    self.curr_y = point_y
    self.curr_x = point_x
    if point_y == self.start_y and point_x == self.start_x:
      first = self.vertices[-1]
      self.vertices = [first] + self.vertices[:-1]
      return True

  def contains(self, y, x):
    return (self.min_y <= y < self.max_y) and (self.min_x <= x < self.max_x)

  def get_edges(self, params):
    return [self.edges[p] for p in params]

  def get_vertices(self, params):
    return [self.vertices[p] for p in params]

  def get_opposite_edge(self, edge):
    facing = opposite_dir(edge.facing)
    min_dist = INFINITY
    min_index = None
    for i, e in enumerate(self.edges):
      if e.facing != facing:
        continue
      if e.not_in_range_of(edge):
        continue
      dist = e.distance_from(edge)
      if dist < 0:
        continue
      if dist < min_dist:
        min_dist = dist
        min_index = i
    return self.edges[min_index]

  def make_rectangle(self, edges):
    all_y = set()
    all_x = set()
    for e in edges:
      all_y.add(e.y0)
      all_y.add(e.y1)
      all_x.add(e.x0)
      all_x.add(e.x1)
    ys = sorted(list(all_y))
    xs = sorted(list(all_x))
    return geometry.Rectangle(ys[0], xs[0], ys[1], xs[1])

  def make_rectangle_for_tab(self, main, adjacent, opposite):
    one_len = adjacent[0].length
    two_len = adjacent[1].length
    length = min(one_len, two_len)
    length = int(math.ceil(float(length)/8)*8)
    dist = main.distance_from(opposite)
    if length > dist:
      length = dist
    if main.facing == DIR_DOWN:
      return geometry.Rectangle(main.y0, main.x0, main.y0 + length, main.x1)
    if main.facing == DIR_LEFT:
      return geometry.Rectangle(main.y0, main.x0 - length, main.y1, main.x0)
    if main.facing == DIR_UP:
      return geometry.Rectangle(main.y0 - length, main.x0, main.y0, main.x1)
    if main.facing == DIR_RIGHT:
      return geometry.Rectangle(main.y0, main.x0, main.y1, main.x0 + length)

  def find_overlapping_edges(self, rect):
    overlaps = []
    # Top, facing down
    line = geometry.Edge(DIR_DOWN, rect.top, rect.left, rect.top, rect.right)
    overlaps += self._find_matches(DIR_DOWN, line)
    # Right, facing left
    line = geometry.Edge(DIR_LEFT, rect.top, rect.right, rect.bot, rect.right)
    overlaps += self._find_matches(DIR_LEFT, line)
    # Bottom, facing up
    line = geometry.Edge(DIR_UP, rect.bot, rect.left, rect.bot, rect.right)
    overlaps += self._find_matches(DIR_UP, line)
    # Left, facing right
    line = geometry.Edge(DIR_RIGHT, rect.top, rect.left, rect.bot, rect.left)
    overlaps += self._find_matches(DIR_RIGHT, line)
    return overlaps

  def find_overlapping_vertices(self, rect):
    overlaps = []
    # Top, facing down
    line = geometry.Edge(DIR_DOWN, rect.top, rect.left, rect.top, rect.right)
    overlaps += self._find_vertices(line)
    # Right, facing left
    line = geometry.Edge(DIR_LEFT, rect.top, rect.right, rect.bot, rect.right)
    overlaps += self._find_vertices(line)
    # Bottom, facing up
    line = geometry.Edge(DIR_UP, rect.bot, rect.left, rect.bot, rect.right)
    overlaps += self._find_vertices(line)
    # Left, facing right
    line = geometry.Edge(DIR_RIGHT, rect.top, rect.left, rect.bot, rect.left)
    overlaps += self._find_vertices(line)
    return overlaps

  def _find_matches(self, dir, line):
    result = []
    for e in self.edges:
      if e.facing != dir:
        continue
      if line.fully_overlap(e):
        result.append([e, e.dim_to_range()])
        continue
      amount = line.partially_overlap(e)
      if isinstance(amount, num_range.NumRange):
        result.append([e, amount])
    return result

  def _find_vertices(self, line):
    result = []
    for v in self.vertices:
      if line.overlaps_point(v):
        result.append(v)
    return result

  def push_as_far_as_available(self, edge):
    # Get closet edge
    dir = edge.facing
    min_dist = INFINITY
    answer = None
    for e in self.edges:
      if e.facing != opposite_dir(dir):
        continue
      if e.not_in_range_of(edge):
        continue
      dist = e.distance_from(edge)
      if dist < 0:
        continue
      if dist < min_dist:
        min_dist = dist
        answer = e
    # Collect other rectangles
    accum = []
    for r in self.rects:
      side = r.get_side(opposite_dir(dir))
      dist = edge.distance_from(side)
      if dist < -7: # rectangles that we're already inside of
        continue
      if side.partially_in_range_of(edge):
        accum.append([dist, side])
    # Sort them by distance
    accum.sort()
    # Find when we reach coverage
    coverage = num_range.MultiRange()
    for dist, other in accum:
      coverage.add(other.dim_to_range())
      if coverage.fully_overlap(edge.dim_to_range()):
        if dist < min_dist:
          min_dist = dist
          answer = other
    if answer is None:
      return edge
    if edge.facing in [DIR_UP, DIR_DOWN]:
      answer = geometry.Edge(edge.facing, answer.y0, edge.x0,
                             answer.y0, edge.x1)
    else:
      answer = geometry.Edge(edge.facing, edge.y0, answer.x0,
                             edge.y1, answer.x0)
    return answer

  def put_rect(self, rect):
    self.rects.append(rect)
