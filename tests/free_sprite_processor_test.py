import unittest

import context
import data, errors, free_sprite_processor


class FreeSpriteProcessorTests(unittest.TestCase):
  def setUp(self):
    self.processor = free_sprite_processor.FreeSpriteProcessor(None)
    self._built = None

  def add_region(self, top, left, right):
    region = data.Region(left=left, right=right)
    region.zones.append(data.Zone(left=left, right=right, top=top))
    self.processor._regions.append(region)

  def set_zones(self, index, zones):
    self.processor._regions[index].zones = zones

  def insert_span(self, y, left, right):
    span = data.Span(left, right)
    self._built = self.processor._combine_spans(y, [span])

  def regions(self):
    return str(self.processor._regions)

  def zones(self):
    accum = ''
    for region in self.processor._regions:
      accum += str(region.zones)
    return accum

  def built(self):
    return str(self._built)

  def test_edge_new(self):
    # |..............|
    # |..eeee........|
    self.insert_span(y=6,  left=40, right=48)
    self.assertEqual(self.regions(), '[<Region L=40 R=48>]')
    self.assertEqual(self.zones(), '[<Zone L=40 R=48 T=6>]')
    self.assertEqual(self.built(), '[]')

  def test_edge_same_as_region(self):
    # Edge and region have equal sides, extend region one pixel below.
    # |..rrrr........|
    # |..eeee........|
    self.add_region(top=3, left=40, right=48)
    self.insert_span(y=6,  left=40, right=48)
    self.assertEqual(self.regions(), '[<Region L=40 R=48>]')
    self.assertEqual(self.zones(), '[<Zone L=40 R=48 T=3>]')
    self.assertEqual(self.built(), '[]')

  def test_edge_after_region(self):
    # Edge is to the right of this region, look at the next one.
    # |..rrrr.???????|
    # |........eeee..|
    self.add_region(top=3, left=40, right=48)
    self.insert_span(y=6,  left=51, right=59)
    self.assertEqual(self.regions(), '[<Region L=51 R=59>]')
    self.assertEqual(self.zones(), '[<Zone L=51 R=59 T=6>]')
    self.assertEqual(self.built(), '[<Zone L=40 R=48 T=3 B=6>]')

  def test_edge_before_region(self):
    # Edge is before this region, insert it. This makes a new corner.
    # |.......rrrr...|
    # |..Ceee........|
    self.add_region(top=3, left=40, right=48)
    self.insert_span(y=6,  left=12, right=18)
    self.assertEqual(self.regions(), '[<Region L=12 R=18>]')
    self.assertEqual(self.zones(), '[<Zone L=12 R=18 T=6>]')
    self.assertEqual(self.built(), '[<Zone L=40 R=48 T=3 B=6>]')

  def test_edge_bigger_on_left_but_same_on_right(self):
    # Corner created by a partially overlapping edge.
    # |....rrrr......|
    # |..Ceeeee......|
    self.add_region(top=3, left=40, right=48)
    self.insert_span(y=6,  left=38, right=48)
    self.assertEqual(self.regions(), '[<Region L=38 R=48>]')
    self.assertEqual(self.zones(),
                     '[<Zone L=38 R=[40, 48] T=6>,'
                     ' <Zone L=40 R=48 T=3>]')
    self.assertEqual(self.built(), '[]')

  def test_edge_same_on_left_but_smaller_on_right(self):
    # |..rrrrrr......|
    # |..eeee........|
    self.add_region(top=3, left=40, right=54)
    self.set_zones(0, [data.Zone(left=46, right=54, top=1),
                       data.Zone(left=40, right=54, top=3, maybe_right=46)])
    self.assertEqual(self.regions(), '[<Region L=40 R=54>]')
    self.assertEqual(self.zones(),
                     '[<Zone L=46 R=54 T=1>,'
                     ' <Zone L=40 R=[46, 54] T=3>]')
    self.insert_span(y=6,  left=40, right=48)
    self.assertEqual(self.regions(), '[<Region L=40 R=48>]')
    self.assertEqual(self.zones(), '[<Zone L=40 R=[46, 48] T=3>]')
    self.assertEqual(self.built(), '[<Zone L=46 R=54 T=1 B=6>]')

  def test_edge_same_on_left_but_bigger_on_right(self):
    # Region expands to the right, implying a corner inside the region.
    # |..rrrr........|
    # |..eeeCeee.....|
    self.add_region(top=3, left=40, right=48)
    self.insert_span(y=6,  left=40, right=54)
    self.assertEqual(self.regions(), '[<Region L=40 R=54>]')
    self.assertEqual(self.zones(),
                     '[<Zone L=[40, 48] R=54 T=6>,'
                     ' <Zone L=40 R=48 T=3>]')
    self.assertEqual(self.built(), '[]')

  def test_edge_smaller_on_left_but_same_on_right(self):
    # |..rrrrrr......|
    # |....eeee......|
    self.add_region(top=3, left=40, right=56)
    self.set_zones(0, [data.Zone(left=40, right=52, top=1),
                       data.Zone(left=40, right=56, top=3, maybe_left=52)])
    self.assertEqual(self.regions(), '[<Region L=40 R=56>]')
    self.assertEqual(self.zones(),
                     '[<Zone L=40 R=52 T=1>,'
                     ' <Zone L=[40, 52] R=56 T=3>]')
    self.insert_span(y=6,  left=44, right=56)
    self.assertEqual(self.regions(), '[<Region L=44 R=56>]')
    self.assertEqual(self.zones(), '[<Zone L=[44, 52] R=56 T=3>]')
    self.assertEqual(self.built(), '[<Zone L=40 R=52 T=1 B=6>]')

  def test_edge_smaller_on_left_and_also_smaller_on_right(self):
    # Entire region shifts to the left, creating a new corner.
    # |....rrrr......|
    # |..Ceee........|
    self.add_region(top=3, left=40, right=48)
    self.insert_span(y=6,  left=38, right=46)
    self.assertEqual(self.regions(),
                     '[<Region L=38 R=46>]')
    self.assertEqual(self.built(), '[<Zone L=40 R=48 T=3 B=6>]')

  def test_t_pattern(self):
    self.add_region(top=3, left=40, right=48)
    self.insert_span(y=11, left=40, right=56)
    self.assertEqual(self.regions(), '[<Region L=40 R=56>]')
    self.assertEqual(self.zones(),
                     '[<Zone L=[40, 48] R=56 T=11>,'
                     ' <Zone L=40 R=48 T=3>]')
    self.insert_span(y=19, left=40, right=48)
    self.assertEqual(self.regions(), '[<Region L=40 R=48>]')
    self.assertEqual(self.zones(), '[<Zone L=40 R=48 T=3>]')
    self.assertEqual(self.built(), '[<Zone L=48 R=56 T=11 B=19>]')

  def test_merge_with_l(self):
    self.add_region(top=3, left=16, right=24)
    self.add_region(top=3, left=28, right=36)
    self.insert_span(y=6,  left=16, right=36)
    self.assertEqual(self.regions(), '[<Region L=16 R=36>]')
    self.assertEqual(self.zones(),
                     '[<Zone L=16 R=24 T=3>,'
                     ' <Zone L=28 R=36 T=3>,'
                     ' <Zone L=[16, 24] R=[28, 36] T=6>]')
    self.assertEqual(self.built(), '[]')


if __name__ == '__main__':
  unittest.main()
