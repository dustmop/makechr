import general_app_test_util
import unittest

from PIL import Image

import context
from makechr import app, bg_color_spec


class AppSpriteTests(general_app_test_util.GeneralAppTests):
  def test_views_sprite(self):
    """Create views for a sprite image."""
    img = Image.open('testdata/reticule.png')
    self.args.bg_color = bg_color_spec.build('30')
    self.args.is_sprite = True
    self.args.nametable_view = None
    self.args.colorization_view = None
    self.process_image(img)
    a = app.Application()
    a.create_views(self.ppu_memory, self.args, img)
    self.golden_file_prefix = 'reticule'
    self.assert_file_eq(self.args.palette_view, self.golden('pal-view', 'png'))
    self.assert_file_eq(self.args.reuse_view, self.golden('reuse-view', 'png'))
    self.assert_file_eq(self.args.chr_view, self.golden('chr-view', 'png'))
    self.assert_file_eq(self.args.grid_view, self.golden('grid-view', 'png'))

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

  def test_output_sprite_locked_tiles(self):
    """Sprite mode with locked tiles."""
    img = Image.open('testdata/reticule.png')
    self.args.is_sprite = True
    self.args.is_locked_tiles = True
    self.process_image(img)
    self.create_output()
    self.golden_file_prefix = 'reticule'
    self.assert_output_result('chr', '-locked')
    self.assert_not_exist('nametable')
    self.assert_output_result('palette', '-sprite')
    self.assert_not_exist('attribute')
    self.assert_output_result('spritelist', '-locked')

  def test_output_sprite_8x16(self):
    """Sprite mode with 8x16 sprites."""
    img = Image.open('testdata/reticule.png')
    self.args.is_sprite = True
    self.args.traversal = '8x16'
    self.process_image(img)
    self.create_output()
    self.golden_file_prefix = 'reticule'
    self.assert_output_result('chr', '-8x16')
    self.assert_not_exist('nametable')
    self.assert_output_result('palette', '-sprite')
    self.assert_not_exist('attribute')
    self.assert_output_result('spritelist', '-8x16')

  def test_output_sprite_8x16_with_blanks(self):
    """Sprite mode with 8x16 sprites, which contains some empty tiles."""
    img = Image.open('testdata/full-image.png')
    self.args.is_sprite = True
    self.args.traversal = '8x16'
    self.process_image(img)
    self.create_output()
    self.golden_file_prefix = 'full-image'
    self.assert_output_result('chr', '-8x16')
    self.assert_not_exist('nametable')
    self.assert_output_result('palette', '-sprite')
    self.assert_not_exist('attribute')
    self.assert_output_result('spritelist', '-8x16')

  def test_output_sprite_locked_tiles_and_8x16(self):
    """Sprite mode with 8x16 sprites and locked_tiles."""
    img = Image.open('testdata/reticule.png')
    self.args.is_sprite = True
    self.args.is_locked_tiles = True
    self.args.traversal = '8x16'
    self.process_image(img)
    self.create_output()
    self.golden_file_prefix = 'reticule'
    self.assert_output_result('chr', '-locked-8x16')
    self.assert_not_exist('nametable')
    self.assert_output_result('palette', '-sprite')
    self.assert_not_exist('attribute')
    self.assert_output_result('spritelist', '-locked-8x16')

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
