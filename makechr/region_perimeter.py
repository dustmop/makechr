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
    self.count = 0

  def __str__(self):
    return '#<RegionPerimeter edges=%s vertices=%s points=%s>' % (
      len(self.edges), len(self.vertices), self.vertices)

  def __repr__(self):
    return self.__str__()

  def add(self, dir, point_y, point_x, next_dir):
    self.count += 1
    if self.count >= 128:
      raise errors.AlgorithmError('loop detected')
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
    return (self.min_y <= y <= self.max_y) and (self.min_x <= x <= self.max_x)
