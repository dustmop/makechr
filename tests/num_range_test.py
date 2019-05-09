import unittest

import context
from makechr import num_range


class NumRangeTests(unittest.TestCase):
  def test_construct(self):
    r = num_range.NumRange(4, 9)
    self.assertEqual(r.p0, 4)
    self.assertEqual(r.p1, 9)

  def test_intersect_fully_left(self):
    a = num_range.NumRange(4, 9)
    b = num_range.NumRange(20, 23)
    self.assertEqual(a.intersect(b), None)

  def test_intersect_left_side(self):
    a = num_range.NumRange(4, 9)
    b = num_range.NumRange(7, 23)
    self.assertEqual(a.intersect(b), num_range.NumRange(7, 9))

  def test_intersect_within(self):
    a = num_range.NumRange(4, 9)
    b = num_range.NumRange(1, 23)
    self.assertEqual(a.intersect(b), num_range.NumRange(4, 9))

  def test_intersect_contains(self):
    a = num_range.NumRange(4, 9)
    b = num_range.NumRange(5, 7)
    self.assertEqual(a.intersect(b), num_range.NumRange(5, 7))

  def test_intersect_right_side(self):
    a = num_range.NumRange(4, 9)
    b = num_range.NumRange(5, 23)
    self.assertEqual(a.intersect(b), num_range.NumRange(5, 9))

  def test_intersect_fully_right(self):
    a = num_range.NumRange(4, 9)
    b = num_range.NumRange(1, 2)
    self.assertEqual(a.intersect(b), None)

  def test_intersect_one_point_left(self):
    a = num_range.NumRange(4, 9)
    b = num_range.NumRange(1, 4)
    self.assertEqual(a.intersect(b), 4)

  def test_intersect_one_point_right(self):
    a = num_range.NumRange(4, 9)
    b = num_range.NumRange(9, 23)
    self.assertEqual(a.intersect(b), 9)

  def test_intersect_inside_same_right(self):
    a = num_range.NumRange(4, 9)
    b = num_range.NumRange(6, 9)
    self.assertEqual(a.intersect(b), num_range.NumRange(6, 9))

  def test_intersect_outside_same_right(self):
    a = num_range.NumRange(4, 9)
    b = num_range.NumRange(1, 9)
    self.assertEqual(a.intersect(b), num_range.NumRange(4, 9))

  def test_intersect_inside_same_left(self):
    a = num_range.NumRange(4, 9)
    b = num_range.NumRange(4, 7)
    self.assertEqual(a.intersect(b), num_range.NumRange(4, 7))

  def test_intersect_outside_same_left(self):
    a = num_range.NumRange(4, 9)
    b = num_range.NumRange(4, 23)
    self.assertEqual(a.intersect(b), num_range.NumRange(4, 9))

  def test_intersect_exactly_same(self):
    a = num_range.NumRange(4, 9)
    b = num_range.NumRange(4, 9)
    self.assertEqual(a.intersect(b), num_range.NumRange(4, 9))

  def test_multi_range_combine(self):
    a = num_range.MultiRange([[5, 10], [20, 30]])
    b = num_range.NumRange(8, 16)
    self.assertEqual(a.add(b), num_range.MultiRange([[5,16], [20,30]]))

  def test_multi_range_between(self):
    a = num_range.MultiRange([[5, 10], [20, 30]])
    b = num_range.NumRange(13, 16)
    self.assertEqual(a.add(b), num_range.MultiRange([[5,10], [13,16], [20,30]]))

  def test_multi_range_before_first(self):
    a = num_range.MultiRange([[5, 10], [20, 30]])
    b = num_range.NumRange(2, 3)
    self.assertEqual(a.add(b), num_range.MultiRange([[2,3], [5,10], [20,30]]))

  def test_multi_range_after_last(self):
    a = num_range.MultiRange([[5, 10], [20, 30]])
    b = num_range.NumRange(60, 66)
    self.assertEqual(a.add(b), num_range.MultiRange([[5,10], [20,30], [60,66]]))

  def test_multi_range_combine_two(self):
    a = num_range.MultiRange([[5, 10], [20, 30]])
    b = num_range.NumRange(8, 22)
    self.assertEqual(a.add(b), num_range.MultiRange([[5,30]]))

  def test_multi_range_combine_many(self):
    a = num_range.MultiRange([[5, 10], [20, 30], [40, 50], [60, 70]])
    b = num_range.NumRange(25, 64)
    self.assertEqual(a.add(b), num_range.MultiRange([[5,10], [20,70]]))

  def test_multi_range_complment_left(self):
    a = num_range.MultiRange([[5, 10]])
    b = num_range.NumRange(2, 7)
    self.assertEqual(a.subtract_from(b), num_range.MultiRange([[2, 5]]))

  def test_multi_range_complment_right(self):
    a = num_range.MultiRange([[5, 10]])
    b = num_range.NumRange(7, 20)
    self.assertEqual(a.subtract_from(b), num_range.MultiRange([[10, 20]]))

  def test_multi_range_complment_middle(self):
    a = num_range.MultiRange([[5, 10], [20, 30]])
    b = num_range.NumRange(5, 30)
    self.assertEqual(a.subtract_from(b), num_range.MultiRange([[10, 20]]))

  def test_multi_range_complment_outside(self):
    a = num_range.MultiRange([[5, 10]])
    b = num_range.NumRange(2, 20)
    self.assertEqual(a.subtract_from(b), num_range.MultiRange([[2,5], [10,20]]))


if __name__ == '__main__':
  unittest.main()
