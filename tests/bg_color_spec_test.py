import unittest

import context
from makechr import bg_color_spec


class BgColorSpecTests(unittest.TestCase):
  def test_bg_color_spec_simple(self):
    spec = bg_color_spec.build('01')
    self.assertEqual(spec.mask, None)
    self.assertEqual(spec.fill, 1)

  def test_bg_color_spec_pair(self):
    spec = bg_color_spec.build('01=02')
    self.assertEqual(spec.mask, 1)
    self.assertEqual(spec.fill, 2)

  def test_bg_color_spec_default(self):
    spec = bg_color_spec.default()
    self.assertEqual(spec.mask, None)
    self.assertEqual(spec.fill, None)


if __name__ == '__main__':
  unittest.main()
