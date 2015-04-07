import unittest

import errors
from PIL import Image
import image_processor


class TileTests(unittest.TestCase):
  def test_process_tile_solid(self):
    img = Image.open('testdata/blue-tile.png')
    processor = image_processor.ImageProcessor()
    processor.load_image(img)
    (color_needs, dot_profile) = processor.process_tile(0, 0)
    self.assertEqual(color_needs, [2, None, None, None])
    self.assertEqual(dot_profile, [0] * 64)

  def test_process_tile_two_colors(self):
    expected_dot_profile = ([0] * 4 + [1] * 8 + [0] * 4) * 4
    img = Image.open('testdata/blue-and-red-tile.png')
    processor = image_processor.ImageProcessor()
    processor.load_image(img)
    (color_needs, dot_profile) = processor.process_tile(0, 0)
    self.assertEqual(color_needs, [2, 7, None, None])
    self.assertEqual(dot_profile, expected_dot_profile)
    img = Image.open('testdata/red-and-blue-tile.png')
    processor = image_processor.ImageProcessor()
    processor.load_image(img)
    (color_needs, dot_profile) = processor.process_tile(0, 0)
    self.assertEqual(color_needs, [7, 2, None, None])
    self.assertEqual(dot_profile, expected_dot_profile)

  def test_process_tile_all_four_colors(self):
    img = Image.open('testdata/gradiant-tile.png')
    processor = image_processor.ImageProcessor()
    processor.load_image(img)
    (color_needs, dot_profile) = processor.process_tile(0, 0)
    self.assertEqual(color_needs, [2, 33, 42, 11])
    self.assertEqual(dot_profile, [0, 0, 0, 0, 1, 1, 1, 1,
                                   0, 0, 0, 1, 1, 1, 1, 2,
                                   0, 0, 1, 1, 1, 1, 2, 2,
                                   0, 1, 1, 1, 1, 2, 2, 2,
                                   1, 1, 1, 1, 2, 2, 2, 2,
                                   1, 1, 1, 2, 2, 2, 2, 3,
                                   1, 1, 2, 2, 2, 2, 3, 3,
                                   1, 2, 2, 2, 2, 3, 3, 3])

  def test_process_tile_error_color_not_allowed(self):
    img = Image.open('testdata/color-not-allowed-tile.png')
    processor = image_processor.ImageProcessor()
    processor.load_image(img)
    with self.assertRaises(errors.ColorNotAllowedError):
      processor.process_tile(0, 0)

  def test_process_tile_error_palette_overflow(self):
    img = Image.open('testdata/palette-overflow-tile.png')
    processor = image_processor.ImageProcessor()
    processor.load_image(img)
    with self.assertRaises(errors.PaletteOverflowError):
      processor.process_tile(0, 0)


if __name__ == '__main__':
  unittest.main()
