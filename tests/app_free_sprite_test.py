import general_app_test_util
import unittest

from PIL import Image

import context
from makechr import app, bg_color_spec


class AppFreeSpriteTests(general_app_test_util.GeneralAppTests):
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

  def test_output_free_sprite_t_traversal(self):
    """Sprite mode using free tranversal and T shaped regions."""
    img = Image.open('testdata/free-sprites-t.png')
    self.args.bg_color = bg_color_spec.build('00=30')
    self.args.is_sprite = True
    self.args.traversal = 'free'
    self.process_image(img)
    self.create_output()
    self.golden_file_prefix = 'free-sprites-t'
    self.assert_output_result('chr')
    self.assert_not_exist('nametable')
    self.assert_output_result('palette')
    self.assert_not_exist('attribute')
    self.assert_output_result('spritelist')

  def test_output_free_sprite_multi_traversal(self):
    """Sprite mode using free traversal and regions are taller than one tile."""
    img = Image.open('testdata/free-sprites-multi.png')
    self.args.bg_color = bg_color_spec.build('00=30')
    self.args.is_sprite = True
    self.args.traversal = 'free'
    self.process_image(img)
    self.create_output()
    self.golden_file_prefix = 'free-sprites'
    self.assert_output_result('chr', '-multi')
    self.assert_not_exist('nametable')
    self.assert_output_result('palette')
    self.assert_not_exist('attribute')
    self.assert_output_result('spritelist', '-multi')

  def test_output_free_sprite_colors_traversal(self):
    """Sprite mode using free traversal and colors in regions."""
    img = Image.open('testdata/free-sprites-colors.png')
    self.args.bg_color = bg_color_spec.build('00=30')
    self.args.is_sprite = True
    self.args.traversal = 'free'
    self.process_image(img)
    self.create_output()
    self.golden_file_prefix = 'free-sprites-colors'
    self.assert_output_result('chr')
    self.assert_not_exist('nametable')
    self.assert_output_result('palette')
    self.assert_not_exist('attribute')
    self.assert_output_result('spritelist')

  def test_output_free_sprite_multi_8x16_traversal(self):
    """Sprite mode using free traversal and 8x16 sprites."""
    img = Image.open('testdata/free-sprites-multi.png')
    self.args.bg_color = bg_color_spec.build('00=30')
    self.args.is_sprite = True
    self.args.traversal = 'free-8x16'
    self.process_image(img)
    self.create_output()
    self.golden_file_prefix = 'free-sprites-8x16'
    self.assert_output_result('chr')
    self.assert_not_exist('nametable')
    self.assert_output_result('palette')
    self.assert_not_exist('attribute')
    self.assert_output_result('spritelist')

  def test_output_free_sprite_colors_8x16_traversal(self):
    """Sprite mode using free traversal, palette is decided based on pair."""
    img = Image.open('testdata/free-sprites-colors.png')
    self.args.bg_color = bg_color_spec.build('00=30')
    self.args.is_sprite = True
    self.args.traversal = 'free-8x16'
    self.process_image(img)
    self.create_output()
    self.golden_file_prefix = 'free-sprites-8x16-colors'
    self.assert_output_result('chr')
    self.assert_not_exist('nametable')
    self.assert_output_result('palette')
    self.assert_not_exist('attribute')
    self.assert_output_result('spritelist')

  def test_output_free_sprite_colors_locked_8x16_traversal(self):
    """Sprite mode using free traversal, locked flag disables flip bits."""
    img = Image.open('testdata/free-sprites-colors.png')
    self.args.bg_color = bg_color_spec.build('00=30')
    self.args.is_sprite = True
    self.args.is_locked_tiles = True
    self.args.traversal = 'free-8x16'
    self.process_image(img)
    self.create_output()
    self.golden_file_prefix = 'free-sprites-8x16-colors'
    self.assert_output_result('chr', '-locked')
    self.assert_not_exist('nametable')
    self.assert_output_result('palette')
    self.assert_not_exist('attribute')
    self.assert_output_result('spritelist', '-locked')

  def test_view_for_free_sprite_traversal(self):
    """View for the zones in free sprite traversal."""
    img = Image.open('testdata/free-sprites.png')
    self.args.bg_color = bg_color_spec.build('00=30')
    self.args.is_sprite = True
    self.args.traversal = 'free'
    self.args.clear_views()
    self.args.free_zone_view = self.args.tmppng('free-zone')
    self.process_image(img)
    a = app.Application()
    a.create_views(self.ppu_memory, self.args, img)
    self.golden_file_prefix = 'free-zone'
    self.assert_file_eq(self.args.free_zone_view, self.golden('view', 'png'))

  def test_view_for_free_sprite_t_traversal(self):
    """View for the zones in free sprites with T shaped regions."""
    img = Image.open('testdata/free-sprites-t.png')
    self.args.bg_color = bg_color_spec.build('00=30')
    self.args.is_sprite = True
    self.args.traversal = 'free'
    self.args.clear_views()
    self.args.free_zone_view = self.args.tmppng('free-zone-t')
    self.process_image(img)
    a = app.Application()
    a.create_views(self.ppu_memory, self.args, img)
    self.golden_file_prefix = 'free-zone-t'
    self.assert_file_eq(self.args.free_zone_view, self.golden('view', 'png'))

  def test_view_for_free_sprite_multi_traversal(self):
    """View for the zones in free sprites with multiple sprites per zone."""
    img = Image.open('testdata/free-sprites-multi.png')
    self.args.bg_color = bg_color_spec.build('00=30')
    self.args.is_sprite = True
    self.args.traversal = 'free'
    self.args.clear_views()
    self.args.free_zone_view = self.args.tmppng('free-zone-multi')
    self.process_image(img)
    a = app.Application()
    a.create_views(self.ppu_memory, self.args, img)
    self.golden_file_prefix = 'free-zone-multi'
    self.assert_file_eq(self.args.free_zone_view, self.golden('view', 'png'))

  def test_view_for_free_sprite_colors_traversal(self):
    """View for the zones in free sprites with complex colors."""
    img = Image.open('testdata/free-sprites-colors.png')
    self.args.bg_color = bg_color_spec.build('00=30')
    self.args.is_sprite = True
    self.args.traversal = 'free'
    self.args.clear_views()
    self.args.free_zone_view = self.args.tmppng('free-zone-colors')
    self.process_image(img)
    a = app.Application()
    a.create_views(self.ppu_memory, self.args, img)
    self.golden_file_prefix = 'free-zone-colors'
    self.assert_file_eq(self.args.free_zone_view, self.golden('view', 'png'))

  def test_view_for_free_sprite_hard(self):
    """View for the zones in free sprites with hard areas."""
    img = Image.open('testdata/free-sprites-hard.png')
    self.args.bg_color = bg_color_spec.build('00=30')
    self.args.is_sprite = True
    self.args.traversal = 'free'
    self.args.clear_views()
    self.args.free_zone_view = self.args.tmppng('free-zone-hard')
    self.process_image(img)
    a = app.Application()
    a.create_views(self.ppu_memory, self.args, img)
    self.golden_file_prefix = 'free-zone-hard'
    self.assert_file_eq(self.args.free_zone_view, self.golden('view', 'png'))


if __name__ == '__main__':
  unittest.main()
