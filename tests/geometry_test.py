import unittest

import context
import geometry, errors, num_range
from direction_constants import *

class GeometryTests(unittest.TestCase):
  def test_point(self):
    p = geometry.Point(10, 23)
    self.assertEqual('%s' % p, '#<Point y=10 x=23>')

    q = p.move_point(DIR_UP, 4)
    self.assertEqual('%s' % q, '#<Point y=6 x=23>')
    self.assertEqual(q.distance_from(p), -4)

    q = p.move_point(DIR_DOWN, 4)
    self.assertEqual('%s' % q, '#<Point y=14 x=23>')
    self.assertEqual(q.distance_from(p), 4)

    q = p.move_point(DIR_LEFT, 4)
    self.assertEqual('%s' % q, '#<Point y=10 x=19>')
    self.assertEqual(q.distance_from(p), -4)

    q = p.move_point(DIR_RIGHT, 4)
    self.assertEqual('%s' % q, '#<Point y=10 x=27>')
    self.assertEqual(q.distance_from(p), 4)

    q = geometry.Point(15, 22)
    self.assertRaises(errors.GeometryError, lambda: q.distance_from(p))

    self.assertFalse(p == q)
    q = geometry.Point(10, 23)
    self.assertTrue(p == q)

  def test_vertex(self):
    v = geometry.Vertex('reflex', 65, 47)
    self.assertEqual('%s' % v, '#<Vertex kind=reflex y=65 x=47 idx=None>')
    self.assertFalse(v.is_convex)

    v.mark_terminal()
    self.assertEqual('%s' % v,
                     '#<Vertex kind=reflex y=65 x=47 idx=None terminal=true>')

    v = geometry.Vertex('convex', 82, 31)
    self.assertEqual('%s' % v, '#<Vertex kind=convex y=82 x=31 idx=None>')
    self.assertTrue(v.is_convex)

    v.mark_terminal()
    self.assertEqual('%s' % v,
                     '#<Vertex kind=convex y=82 x=31 idx=None terminal=true>')

    f = lambda: geometry.Vertex('other', 90, 54)
    self.assertRaises(errors.GeometryError, f)

  def test_edge(self):
    e = geometry.Edge(DIR_DOWN, 15, 4, 15, 32)
    self.assertEqual('%s' % e, '#<Edge facing=down y=15 x0=4 x1=32>')
    self.assertEqual(e.length, 28)
    self.assertEqual('%s' % e.get_endpoints(),
                     '[#<Point y=15 x=4>, #<Point y=15 x=32>]')
    self.assertEqual('%s' % e.dim_to_range(), '#<Range p0=4 p1=32>')

    f = geometry.Edge(DIR_RIGHT, 29, 58, 45, 58)
    self.assertEqual('%s' % f, '#<Edge facing=right y0=29 y1=45 x=58>')
    self.assertEqual(f.length, 16)
    self.assertEqual('%s' % f.get_endpoints(),
                     '[#<Point y=29 x=58>, #<Point y=45 x=58>]')
    self.assertEqual('%s' % f.dim_to_range(), '#<Range p0=29 p1=45>')

    self.assertEqual('%s' % e.calc_uncovered(),
                     '#<Edge facing=down y=15 x0=4 x1=32>')
    self.assertFalse(e.done)

    e.mark_done(num_range.NumRange(4, 10))
    self.assertEqual('%s' % e.calc_uncovered(),
                     '#<Edge facing=down y=15 x0=10 x1=32>')
    self.assertFalse(e.done)

    e.mark_done(num_range.NumRange(25, 32))
    self.assertEqual('%s' % e.calc_uncovered(),
                     '#<Edge facing=down y=15 x0=10 x1=25>')
    self.assertFalse(e.done)

    e.mark_done(num_range.NumRange(10, 25))
    self.assertEqual('%s' % e.calc_uncovered(), 'None')
    self.assertTrue(e.done)

  def test_rectangle(self):
    r = geometry.Rectangle(top=30, left=44, bot=58, right=73)
    self.assertEqual('%s' % r, '#<Rectangle top=30 left=44 bot=58 right=73>')

    self.assertTrue(r.exclusively_inside(34, 56))
    self.assertTrue(r.exclusively_inside(52, 71))
    self.assertFalse(r.exclusively_inside(52, 73))
    self.assertFalse(r.exclusively_inside(30, 71))
    self.assertFalse(r.exclusively_inside(88, 99))

    self.assertEqual('%s' % r.get_side(DIR_UP),
                     '#<Edge facing=up y=30 x0=44 x1=73>')
    self.assertEqual('%s' % r.get_side(DIR_RIGHT),
                     '#<Edge facing=right y0=30 y1=58 x=73>')
    self.assertEqual('%s' % r.get_side(DIR_DOWN),
                     '#<Edge facing=down y=58 x0=44 x1=73>')
    self.assertEqual('%s' % r.get_side(DIR_LEFT),
                     '#<Edge facing=left y0=30 y1=58 x=44>')

    self.assertEqual(r.width, 29)
    self.assertEqual(r.height, 28)


if __name__ == '__main__':
  unittest.main()
