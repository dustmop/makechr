import errors
import geometry
import math
from direction_constants import *


# TODO: Add documentation to how methods work, add more tests.

class RectilinearCoverage(object):
  def calc(self, regions):
    self.classify = []
    rescue_me = False
    for i, r in enumerate(regions):
      if not rescue_me:
        self.create_coverage(r)
      else:
        try:
          self.create_coverage(r)
        except RuntimeError as e:
          print e
        except IndexError as e:
          print e

  def create_coverage(self, region):
    # Starting from the first vertex, look back to see if the previous two
    # vertices were convex (count) or concave (anti).
    count = 0
    anti = 0
    penul = region.vertices[-2]
    final = region.vertices[-1]
    if penul.is_convex:
      count += 1
      anti = 0
    else:
      count = 0
      anti += 1
    if final.is_convex:
      count += 1
      anti = 0
    else:
      count = 0
      anti += 1
    # Classify the verticies.
    # Complete: 3 convex in a row, forcing a region.
    #
    #  +----+
    #  |====|
    #  |====.--x
    #  +--.====:
    #     |====:
    #     x::::
    #
    # Tab: 2 convex, surrounded by concave vertices.
    #
    #     +----+
    #     |====|
    #     |====.--x
    #  x--.=======:
    #  :==========:
    #
    # Anti-knob: two concave verticies in a row.
    #
    #    :x    x:
    #   :=|    |=:
    #   :=.----.=:
    #   :========:
    #   :========:
    #
    job_complete = []
    job_tab = []
    job_antiknob = []
    for i, v in enumerate(region.vertices):
      if v.is_convex:
        anti = 0
        count += 1
        if count >= 3:
          job_complete.append(i - 1)
      else:
        if count == 2:
          job_tab.append(i - 2)
        count = 0
        anti += 1
        if anti >= 2:
          job_antiknob.append(i - 1)
    self.classify.append([job_complete, job_tab, job_antiknob])
    # 3-somes
    for job in job_complete:
      edges = region.get_edges([job - 1, job])
      rect = region.make_rectangle(edges)
      found = False
      for v in region.vertices:
        if rect.exclusively_inside(v.y, v.x):
          found = True
          break
      if found:
        continue
      for edge, amount in region.find_overlapping_edges(rect):
        edge.mark_done(amount)
      self.collect_rectangle(region, rect, 0)
      for vertex in region.find_overlapping_vertices(rect):
        if not vertex.is_convex:
          vertex.mark_terminal()
    # Tabs
    for job in job_tab:
      main_edge = region.get_edges([job])[0]
      prev_vertex = region.vertices[job - 1]
      prev_dist = main_edge.distance_from(prev_vertex)
      next_vertex = region.vertices[job + 2]
      next_dist = main_edge.distance_from(next_vertex)
      adjacent_edges = region.get_edges([job - 1, job + 1])
      opposite_edge = region.get_opposite_edge(main_edge)
      opposite_dist = main_edge.distance_from(opposite_edge)
      #
      prev_dist = int(math.ceil(float(prev_dist)/8)*8)
      next_dist = int(math.ceil(float(next_dist)/8)*8)
      # If tab includes a terminal vertex, that vertex came from a 3-some.
      # Make a rectangle that reaches up to that terminal vertex. Otherwise,
      # make the rectangle that goes as long as the shortest adjacent edge.
      if prev_vertex.terminal and prev_dist < opposite_dist and prev_dist >= 8:
        side_edge = self.edge_of_length(adjacent_edges[0], main_edge, prev_dist)
        rect = region.make_rectangle([main_edge, side_edge])
      elif next_vertex.terminal and next_dist < opposite_dist and next_dist >=8:
        side_edge = self.edge_of_length(adjacent_edges[1], main_edge, next_dist)
        rect = region.make_rectangle([main_edge, side_edge])
      else:
        rect = region.make_rectangle_for_tab(main_edge, adjacent_edges,
                                             opposite_edge)
      for edge, amount in region.find_overlapping_edges(rect):
        edge.mark_done(amount)
      self.collect_rectangle(region, rect, 1)
    # Anti-knobs
    for job in job_antiknob:
      main_edge = region.get_edges([job])[0]
      if main_edge.done:
        continue
      # Get endpoints, if any are *not* terminal, extend them til intersect.
      endpoints = region.get_vertices([job, job + 1])
      expand_edge = geometry.Edge.from_endpoints(main_edge.facing, endpoints)
      rect = self.antiknob_edge_to_maximal_rect(region, expand_edge)
      if rect.width < 8 or rect.height < 8:
        continue
      for edge, amount in region.find_overlapping_edges(rect):
        edge.mark_done(amount)
      self.collect_rectangle(region, rect, 2)
    # Edges that remain
    # TODO: What edges are incomplete?
    for phase in xrange(2):
      for e in region.edges:
        if e.done:
          continue
        try:
          segment = e.calc_uncovered()
        except RuntimeError, e:
          segment = None
        if not segment:
          continue
        if phase == 0:
          # Get corners and turn those into rectangles.
          corner = self.does_segment_have_corner(region, segment)
          if not corner:
            continue
          rect = self.corner_to_uncovered_rect(region, corner)
        else:
          # Unfinished edge, assume it has a pair.
          if segment.length < 8:
            segment = self.expand_lower_dim(segment, 8 - segment.length)
          oppose = region.get_opposite_edge(segment)
          if oppose.done:
            continue
          # Expand segment so it matches the size of the union with oppose.
          segment = segment.stretch_so_it_looks_like(oppose.calc_uncovered())
          side = segment.rotated_edge_til(oppose)
          rect = region.make_rectangle([segment, side])
        for edge, amount in region.find_overlapping_edges(rect):
          edge.mark_done(amount)
        self.collect_rectangle(region, rect, 3)

  # Copy `start`, such that it collides with `term`, and is of length `size`
  def edge_of_length(self, start, term, size):
    match = start.common_endpoint(term)
    other = start.different_endpoint(match)
    curr = match.distance_from(other)
    if curr < 0:
      curr = -curr
    change = other.move_point(term.facing, size - curr)
    return geometry.Edge.from_endpoints(start.facing, [match, change])

  def side_between(self, first, second, rotate_clockwise):
    if first.facing != opposite_dir(second.facing):
      raise errors.AlgorithmError('Side direction mismatch!')
    if rotate_clockwise:
      dir = rotate_dir_cw(first.facing)
    else:
      dir = rotate_dir_counter_cw(first.facing)
    if first.facing in DIR_UP:
      #    +---+
      # cc |   | rc
      #    |   |
      #    |   |
      y0, y1 = first.y0, second.y0
      if rotate_clockwise:
        # right-hand side from the top and bottom
        x0 = x1 = first.x1
      else:
        # left-hand side from the top and bottom
        x0 = x1 = first.x0
    elif first.facing == DIR_RIGHT:
      x0, x1 = second.x0, first.x0
      if rotate_clockwise:
        # bottom side from the right and left
        y0 = y1 = first.y1
      else:
        # top side from the right and left
        y0 = y1 = first.y0
    elif first.facing == DIR_DOWN:
      #    |   |
      #    |   |
      # rc |   | cc
      #    +---+
      y0, y1 = second.y0, first.y0
      if rotate_clockwise:
        # left-hand side from the bottom and top
        x0 = x1 = first.x0
      else:
        # right-hand side from the bottom and top
        x0 = x1 = first.x1
    elif first.facing == DIR_LEFT:
      x0, x1 = first.x0, second.x0
      if rotate_clockwise:
        # bottom side from the right and left
        y0 = y1 = first.y0
      else:
        # top side from the right and left
        y0 = y1 = first.y1
    return geometry.Edge(dir, y0, x0, y1, x1)

  def antiknob_edge_to_maximal_rect(self, region, edge):
    far = region.push_as_far_as_available(edge)
    near = edge.clone()
    near.facing = opposite_dir(near.facing)
    one = self.side_between(near, far, True)
    two = self.side_between(near, far, False)
    one = region.push_as_far_as_available(one)
    two = region.push_as_far_as_available(two)
    push = self.side_between(one, two, True)
    push = region.push_as_far_as_available(push)
    orth = one.extend_until(push)
    return region.make_rectangle([orth, push])

  def does_segment_have_corner(self, region, segment):
    (e0, e1) = segment.get_endpoints()
    for i, v in enumerate(region.vertices):
      if v.kind != 'convex':
        continue
      if v == e0:
        return (i, e0)
      if v == e1:
        return (i, e1)
    return None

  def corner_to_uncovered_rect(self, region, pair):
    # TODO: Actual implementation.
    (i, point) = pair
    start = region.edges[i - 1]
    end   = region.edges[i]
    b = point.move_point(start.facing, 8)
    a = point.move_point(end.facing, 8)
    #
    first = geometry.Edge.from_endpoints(start.facing, [a, point])
    second = geometry.Edge.from_endpoints(end.facing, [b, point])
    return region.make_rectangle([first, second])

  def expand_lower_dim(self, s, dist):
    if s.facing in [DIR_UP, DIR_DOWN]:
      return geometry.Edge(s.facing, s.y0, s.x0, s.y0, s.x1 + dist)
    else:
      return geometry.Edge(s.facing, s.y0, s.x0, s.y1 + dist, s.x0)

  def collect_rectangle(self, region, rect, count):
    rect.count = count
    region.put_rect(rect)
