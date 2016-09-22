import general_app_test_util
import unittest

from PIL import Image

import context
from makechr import bg_color_spec


class AppValiantTests(general_app_test_util.GeneralAppTests):
  def test_output_valiant(self):
    """Basic usage, outputting to valiant file."""
    img = Image.open('testdata/full-image.png')
    self.process_image(img)
    self.args.output = self.args.tmpfile('full-image.o')
    self.create_output()
    self.assert_file_eq(self.args.output, self.golden(None, 'o'))

  def test_output_valiant_for_offset_image(self):
    """Valiant file with data only in the center."""
    img = Image.open('testdata/offset-image.png')
    palette_text = 'P/30-30-30-30/30-01-38-16/'
    self.process_image(img, palette_text=palette_text)
    self.args.output = self.args.tmpfile('offset-image.o')
    self.create_output()
    self.golden_file_prefix = 'offset-image'
    self.assert_file_eq(self.args.output, self.golden('normal', 'o'))

  def test_output_valiant_for_offset_image_locked(self):
    """Valiant file with locked tiles option."""
    img = Image.open('testdata/offset-image.png')
    palette_text = 'P/30-30-30-30/30-01-38-16/'
    self.args.is_locked_tiles = True
    self.process_image(img, palette_text=palette_text)
    self.args.output = self.args.tmpfile('offset-image.o')
    self.create_output()
    self.golden_file_prefix = 'offset-image'
    self.assert_file_eq(self.args.output, self.golden('locked', 'o'))

  def test_output_valiant_order1(self):
    """Valiant file with order option."""
    img = Image.open('testdata/full-image.png')
    self.process_image(img)
    self.args.order = 1
    self.args.output = self.args.tmpfile('full-image.o')
    self.create_output()
    self.assert_file_eq(self.args.output, self.golden('order1', 'o'))

  def test_output_valiant_traverse_block(self):
    """Valiant file with block traversal option."""
    img = Image.open('testdata/full-image.png')
    self.args.traversal = 'block'
    self.process_image(img)
    self.args.output = self.args.tmpfile('full-image.o')
    self.create_output()
    self.assert_file_eq(self.args.output, self.golden('traverse-block', 'o'))

  def test_output_valiant_background_color(self):
    """Valiant file with background color."""
    img = Image.open('testdata/full-image.png')
    self.args.bg_color = bg_color_spec.build('16')
    self.process_image(img)
    self.args.output = self.args.tmpfile('full-image.o')
    self.create_output()
    self.assert_file_eq(self.args.output, self.golden('bg-color', 'o'))

  def test_output_valiant_sprite(self):
    """Valiant file for sprites with background color."""
    img = Image.open('testdata/reticule.png')
    self.args.bg_color = bg_color_spec.build('30')
    self.args.is_sprite = True
    self.process_image(img)
    self.args.output = self.args.tmpfile('reticule.o')
    self.create_output()
    self.golden_file_prefix = 'reticule'
    self.assert_file_eq(self.args.output, self.golden(None, 'o'))

  def test_output_valiant_sprite_more(self):
    """Valiant file for sprites with more colors and background color."""
    img = Image.open('testdata/reticule-more.png')
    self.args.bg_color = bg_color_spec.build('30')
    self.args.is_sprite = True
    self.process_image(img)
    self.args.output = self.args.tmpfile('reticule-more.o')
    self.create_output()
    self.golden_file_prefix = 'reticule-more'
    self.assert_file_eq(self.args.output, self.golden(None, 'o'))


if __name__ == '__main__':
  unittest.main()
