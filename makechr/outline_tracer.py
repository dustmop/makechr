import errors
import region_perimeter
from direction_constants import *
import sys


class OutlineTracer(object):
  def __init__(self, height, width, is_clear_func):
    self.height = height
    self.width = width
    self.is_clear_func = is_clear_func

  def find_regions(self):
    regions = []
    for y in xrange(self.height):
      for x in xrange(self.width):
        if self.is_in_region(regions, y, x):
          continue
        if self.is_clear_func(y, x):
          continue
        regions.append(self.create_new_region(y, x))
    return regions

  def is_in_region(self, regions, y, x):
    for r in regions:
      if r.contains(y, x):
        return True
    return False

  def create_new_region(self, y, x):
    try:
      return self.contour_trace(y, x)
    except errors.AlgorithmError as e:
      print(e)
      sys.exit(1)

  def contour_trace(self, y, x):
    region = region_perimeter.RegionPerimeter(y, x)
    curr_dir = DIR_RIGHT
    curr_y = y
    curr_x = x
    while True:
      next_dir, y, x = self.get_move(curr_dir, curr_y, curr_x)
      if next_dir == curr_dir:
        curr_y = y
        curr_x = x
        continue
      if region.add(curr_dir, curr_y, curr_x, next_dir):
        break
      curr_y = y
      curr_x = x
      curr_dir = next_dir
    return region

  def get_move(self, dir, y, x):
    m = self.turn_left(dir, y, x)
    if m:
      return m[0], m[1], m[2]
    m = self.go_forward(dir, y, x)
    if m:
      return m[0], m[1], m[2]
    m = self.turn_right(dir, y, x)
    if m:
      return m[0], m[1], m[2]
    raise errors.AlgorithmError('Stuck, cannot move at %sy, %sx' % (y, x))

  def turn_left(self, dir, y, x):
    dir = rotate_dir_counter_cw(dir)
    next_y, next_x = self.move_at(dir, y, x)
    if self.is_clear_func(next_y, next_x):
      return None
    return dir, next_y, next_x

  def turn_right(self, dir, y, x):
    dir = rotate_dir_cw(dir)
    next_y, next_x = self.move_at(dir, y, x)
    if self.is_clear_func(next_y, next_x):
      return None
    return dir, next_y, next_x

  def go_forward(self, dir, y, x):
    next_y, next_x = self.move_at(dir, y, x)
    if self.is_clear_func(next_y, next_x):
      return None
    return dir, next_y, next_x

  def move_at(self, dir, y, x):
    if dir == DIR_UP:
      return y - 1, x
    elif dir == DIR_RIGHT:
      return y, x + 1
    elif dir == DIR_DOWN:
      return y + 1, x
    elif dir == DIR_LEFT:
      return y, x - 1
