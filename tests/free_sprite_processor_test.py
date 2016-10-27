import unittest

import context
from makechr import errors, free_sprite_processor


class FreeSpriteProcessorTests(unittest.TestCase):
  def setUp(self):
    self.processor = free_sprite_processor.FreeSpriteProcessor()
    self.processor._making = []
    self.processor._built = []

  def add_making(self, top, left, right):
    zone = free_sprite_processor.Zone(top, left, right)
    self.processor._making.append(zone)
    self.processor._previous = [
      free_sprite_processor.Span(left=left, right=right)]

  def insert_span(self, y, left, right):
    span = free_sprite_processor.Span(left, right)
    self.processor._combine_spans(y, [span])

  def making_string(self):
    return str(self.processor._making)

  def built_string(self):
    return str(self.processor._built)

  def test_edge_same_as_region(self):
    # Edge and region have equal sides, extend region one pixel below.
    # |..rrrr........|
    # |..eeee........|
    self.add_making(top=3, left=40, right=48)
    self.insert_span(y=6,  left=40, right=48)
    self.assertEqual(self.making_string(), '[<Zone T=3 L=40 R=48>]')
    self.assertEqual(self.built_string(), '[]')

  def test_edge_after_region(self):
    # Edge is to the right of this region, look at the next one.
    # |..rrrr.???????|
    # |........eeee..|
    self.add_making(top=3, left=40, right=48)
    self.insert_span(y=6,  left=51, right=59)
    self.assertEqual(self.making_string(), '[<Zone T=6 L=51 R=59>]')
    self.assertEqual(self.built_string(), '[<Zone T=3 L=40 R=48 B=6>]')

  def test_edge_before_region(self):
    # Edge is before this region, insert it. This makes a new corner.
    # |.......rrrr...|
    # |..Ceee........|
    self.add_making(top=3, left=40, right=48)
    self.insert_span(y=6,  left=12, right=18)
    self.assertEqual(self.making_string(), '[<Zone T=6 L=12 R=18>]')
    self.assertEqual(self.built_string(), '[<Zone T=3 L=40 R=48 B=6>]')

  def test_edge_bigger_on_left_but_same_on_right(self):
    # Corner created by a partially overlapping edge.
    # |....rrrr......|
    # |..Ceeeee......|
    self.add_making(top=3, left=40, right=48)
    self.insert_span(y=6,  left=38, right=48)
    self.assertEqual(self.making_string(),
                     '[<Zone T=6 L=38 R=<Span L=40 R=48>>, '
                     '<Zone T=3 L=40 R=48>]')
    self.assertEqual(self.built_string(), '[]')

  def test_edge_same_on_left_but_smaller_on_right(self):
    # |..rrrrrr......|
    # |..eeee........|
    self.add_making(top=3, left=40, right=54)
    self.insert_span(y=6,  left=40, right=48)
    self.assertEqual(self.making_string(), '[<Zone T=6 L=40 R=48>]')
    self.assertEqual(self.built_string(), '[<Zone T=3 L=40 R=54 B=6>]')

  def test_edge_same_on_left_but_bigger_on_right(self):
    # Region expands to the right, implying a corner inside the region.
    # |..rrrr........|
    # |..eeeCeee.....|
    self.add_making(top=3, left=40, right=48)
    self.insert_span(y=6,  left=40, right=54)
    self.assertEqual(self.making_string(),
                     '[<Zone T=3 L=40 R=48>, '
                     '<Zone T=6 L=<Span L=40 R=48> R=54>]')
    self.assertEqual(self.built_string(), '[]')

  def test_edge_smaller_on_left_but_same_on_right(self):
    # |..rrrrrr......|
    # |....eeee......|
    self.add_making(top=3, left=40, right=48)
    self.insert_span(y=6,  left=38, right=48)
    self.assertEqual(self.making_string(),
                     '[<Zone T=6 L=38 R=<Span L=40 R=48>>, '
                     '<Zone T=3 L=40 R=48>]')
    self.assertEqual(self.built_string(), '[]')

  def test_edge_smaller_on_left_and_also_smaller_on_right(self):
    # Entire region shifts to the left, creating a new corner.
    # |....rrrr......|
    # |..Ceee........|
    self.add_making(top=3, left=40, right=48)
    self.insert_span(y=6,  left=38, right=46)
    self.assertEqual(self.making_string(),
                     '[<Zone T=6 L=38 R=46>, <Zone T=6 L=38 R=40>]')
    self.assertEqual(self.built_string(), '[<Zone T=3 L=40 R=48 B=6>]')


if __name__ == '__main__':
  unittest.main()
