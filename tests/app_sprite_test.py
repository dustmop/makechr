import general_app_test_util
import unittest

from PIL import Image

import context
from makechr import bg_color_spec


class AppSpriteTests(general_app_test_util.GeneralAppTests):
  def test_output_sprite(self):
    """Sprite mode."""
    img = Image.open('testdata/reticule.png')
    self.args.bg_color = bg_color_spec.build('30')
    self.args.is_sprite = True
    self.process_image(img)
    self.create_output()
    self.golden_file_prefix = 'reticule'
    self.assert_output_result('chr')
    self.assert_not_exist('nametable')
    self.assert_output_result('palette', '-sprite')
    self.assert_not_exist('attribute')
    self.assert_output_result('spritelist')

  def test_output_sprite_as_nametable(self):
    """Some images can be either nametable or sprites."""
    img = Image.open('testdata/reticule.png')
    self.args.bg_color = bg_color_spec.build('30')
    self.args.order = 1
    self.process_image(img)
    self.create_output()
    self.golden_file_prefix = 'reticule'
    self.assert_output_result('chr', '-as-nametable')
    self.assert_output_result('nametable')
    self.assert_output_result('palette')
    self.assert_output_result('attribute')
    self.assert_not_exist('spritelist')

  def test_output_sprite_auto_bg_color(self):
    """In sprite mode the bg color can be auto detected."""
    img = Image.open('testdata/reticule.png')
    self.args.is_sprite = True
    self.process_image(img)
    self.create_output()
    self.golden_file_prefix = 'reticule'
    self.assert_output_result('chr')
    self.assert_not_exist('nametable')
    self.assert_output_result('palette', '-sprite')
    self.assert_not_exist('attribute')
    self.assert_output_result('spritelist')
    # Without this functionality, the derived palette won't have the right
    # background color, which will cause spritelist overflow.
    self.process_image(img, auto_sprite_bg=True)
    self.assertTrue(self.err.has())
    es = self.err.get()
    self.assertEqual(len(es), 1)
    msg = '{0} {1}'.format(type(es[0]).__name__, es[0])
    self.assertEqual(msg, 'SpritelistOverflow at tile (2y,0x)')

  def test_output_sprite_more_colors(self):
    """Sprite mode for image that must use sprites, due to palette."""
    img = Image.open('testdata/reticule-more.png')
    self.args.bg_color = bg_color_spec.build('30')
    self.args.is_sprite = True
    self.process_image(img)
    self.create_output()
    self.golden_file_prefix = 'reticule'
    self.assert_output_result('chr', '-more')
    self.assert_not_exist('nametable')
    self.assert_output_result('palette', '-more')
    self.assert_not_exist('attribute')
    self.assert_output_result('spritelist', '-more')

  def test_output_sprite_more_colors_as_nametable(self):
    """Nametable mode for image that must use sprites, throw error."""
    img = Image.open('testdata/reticule-more.png')
    self.args.bg_color = bg_color_spec.build('30')
    self.process_image(img)
    self.assertTrue(self.err.has())
    errs = self.err.get()
    expect_errors = ['PaletteOverflowError @ block (0y,0x)',
                     'PaletteOverflowError @ block (0y,1x)',
                     'PaletteOverflowError @ block (1y,0x)',
                     'PaletteOverflowError @ block (1y,1x)']
    actual_errors = ['%s %s' % (type(e).__name__, str(e)) for e in errs]
    self.assertEqual(actual_errors, expect_errors)

  def test_output_free_sprite_traversal(self):
    """Sprite mode using free traversal."""
    img = Image.open('testdata/free-sprites.png')
    self.args.bg_color = bg_color_spec.build('00=30')
    self.args.is_sprite = True
    self.args.traversal = 'free'
    self.process_image(img)
    self.create_output()
    self.golden_file_prefix = 'free-sprites'
    self.assert_output_result('chr')
    self.assert_not_exist('nametable')
    self.assert_output_result('palette')
    self.assert_not_exist('attribute')
    self.assert_output_result('spritelist')

  def test_error_for_too_many_sprites(self):
    """If there are too many sprites, throw error."""
    img = Image.open('testdata/implied-bg-color.png')
    self.args.is_sprite = True
    self.process_image(img, auto_sprite_bg=False)
    self.assertTrue(self.err.has())
    es = self.err.get()
    self.assertEqual(len(es), 1)
    msg = '{0} {1}'.format(type(es[0]).__name__, es[0])
    self.assertEqual(msg, 'SpritelistOverflow at tile (2y,7x)')



if __name__ == '__main__':
  unittest.main()
