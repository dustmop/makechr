import general_app_test_util
import unittest

from PIL import Image

import context
from makechr import app, view_renderer


class AppBinTests(general_app_test_util.GeneralAppTests):
  def test_views(self):
    """Create views of the input."""
    img = Image.open('testdata/full-image.png')
    self.process_image(img)
    a = app.Application()
    a.create_views(self.ppu_memory, self.args, img)
    self.assert_file_eq(self.args.palette_view, self.golden('pal', 'png'))
    self.assert_file_eq(self.args.colorization_view,
                        self.golden('color', 'png'))
    self.assert_file_eq(self.args.reuse_view, self.golden('reuse', 'png'))
    self.assert_file_eq(self.args.nametable_view, self.golden('nt', 'png'))
    self.assert_file_eq(self.args.chr_view, self.golden('chr', 'png'))
    self.assert_file_eq(self.args.grid_view, self.golden('grid', 'png'))

  def test_views_legacy(self):
    """Create views of the input, using legacy views."""
    img = Image.open('testdata/full-image.png')
    self.args.use_legacy_views = True
    self.process_image(img)
    a = app.Application()
    a.create_views(self.ppu_memory, self.args, img)
    self.assert_file_eq(self.args.palette_view,
                        self.golden('pal-legacy', 'png'))
    self.assert_file_eq(self.args.colorization_view,
                        self.golden('color-legacy', 'png'))
    self.assert_file_eq(self.args.reuse_view,
                        self.golden('reuse-legacy', 'png'))
    self.assert_file_eq(self.args.nametable_view,
                        self.golden('nt-legacy', 'png'))
    self.assert_file_eq(self.args.chr_view,
                        self.golden('chr-legacy', 'png'))
    self.assert_file_eq(self.args.grid_view,
                        self.golden('grid', 'png'))

  def test_output(self):
    """Basic usage."""
    img = Image.open('testdata/full-image.png')
    self.process_image(img)
    self.create_output()
    self.assert_output_result('chr')
    self.assert_output_result('palette')
    self.assert_output_result('nametable')
    self.assert_output_result('attribute')
    self.assert_not_exist('nametable1')
    self.assert_not_exist('attribute1')

  def test_output_for_bottom_attributes(self):
    """Make sure bottom row attributes work correctly."""
    img = Image.open('testdata/full-image-bottom-attr.png')
    self.process_image(img)
    self.create_output()
    self.assert_output_result('chr')
    self.assert_output_result('palette')
    self.assert_output_result('nametable', golden_suffix='-bottom-attr')
    self.assert_output_result('attribute', golden_suffix='-bottom-attr')
    self.assert_not_exist('nametable1')
    self.assert_not_exist('attribute1')

  def test_output_implied_bg_color(self):
    """Background color is derived by palette guesser."""
    img = Image.open('testdata/implied-bg-color.png')
    self.process_image(img)
    self.create_output()
    self.golden_file_prefix = 'implied-bg-color'
    self.assert_output_result('chr')
    self.assert_output_result('palette')
    self.assert_output_result('nametable')
    self.assert_output_result('attribute')
    self.assert_not_exist('nametable1')
    self.assert_not_exist('attribute1')

  def test_output_uses_safe_black(self):
    """Dangerous black is turned into safe black."""
    img = Image.open('testdata/safe-black.png')
    self.process_image(img)
    self.create_output()
    self.golden_file_prefix = 'safe-black'
    self.assert_output_result('palette')

  def test_output_for_locked_tiles(self):
    """Locked tiles option keeps tiles where they appear in the input."""
    img = Image.open('testdata/full-image.png')
    self.args.is_locked_tiles = True
    self.process_image(img)
    self.create_output()
    self.assert_output_result('chr', golden_suffix='-locked-tiles')
    self.assert_output_result('palette')
    self.assert_not_exist('nametable')
    self.assert_output_result('attribute')
    self.assert_not_exist('nametable1')
    self.assert_not_exist('attribute1')

  def test_output_for_locked_tiles_small_square(self):
    """Locked tiles with a 128x128 input image works specially."""
    img = Image.open('testdata/full-image-small-square.png')
    self.args.is_locked_tiles = True
    self.process_image(img)
    self.create_output()
    self.assert_output_result('chr', golden_suffix='-small-square')
    self.assert_output_result('palette')
    self.assert_not_exist('nametable')
    self.assert_output_result('attribute')
    self.assert_not_exist('nametable1')
    self.assert_not_exist('attribute1')

  def test_output_from_memory_dump(self):
    """Memory can be imported then split into components."""
    memfile = 'testdata/full-image-mem.bin'
    a = app.Application()
    a.read_memory(memfile, 'ram', self.args)
    self.assert_output_result('chr')
    self.assert_output_result('palette')
    self.assert_output_result('nametable')
    self.assert_output_result('attribute')
    self.assert_not_exist('nametable1')
    self.assert_not_exist('attribute1')

  def test_output_order1(self):
    """Order option changes how binaries are stored."""
    img = Image.open('testdata/full-image.png')
    self.args.order = 1
    self.process_image(img)
    self.create_output()
    self.assert_output_result('chr', golden_suffix='-order1')
    self.assert_output_result('palette')
    self.assert_output_result('nametable')
    self.assert_output_result('attribute')
    self.assert_not_exist('nametable1')
    self.assert_not_exist('attribute1')

  def test_output_traverse_block(self):
    """Traversal by block changes the way CHR and nametables are created."""
    img = Image.open('testdata/full-image.png')
    self.args.traversal = 'block'
    self.process_image(img)
    self.create_output()
    self.assert_output_result('chr', golden_suffix='-traverse-block')
    self.assert_output_result('palette')
    self.assert_output_result('nametable', golden_suffix='-traverse-block')
    self.assert_output_result('attribute')
    self.assert_not_exist('nametable1')
    self.assert_not_exist('attribute1')

  def test_output_traverse_vertical(self):
    """Travere vertically to change the way CHR and nametables are created."""
    img = Image.open('testdata/full-image.png')
    self.args.traversal = 'vertical'
    self.process_image(img)
    self.create_output()
    self.assert_output_result('chr', golden_suffix='-traverse-vertical')
    self.assert_output_result('palette')
    self.assert_output_result('nametable', golden_suffix='-traverse-vertical')
    self.assert_output_result('attribute')
    self.assert_not_exist('nametable1')
    self.assert_not_exist('attribute1')

  def test_output_allow_chr_overflow(self):
    """Allow chr overflow so that it uses second page in the bank."""
    img = Image.open('testdata/257tiles.png')
    self.args.allow_overflow = ['c']
    self.process_image(img)
    self.create_output()
    self.golden_file_prefix = '257tiles'
    self.assert_output_result('chr')
    self.assert_output_result('palette')
    self.assert_output_result('nametable')
    self.assert_output_result('attribute')
    self.assert_not_exist('nametable1')
    self.assert_not_exist('attribute1')

  def test_output_double_wide_nametable(self):
    """Image with double width nametable."""
    img = Image.open('testdata/double-image.png')
    self.process_image(img)
    self.create_output()
    self.golden_file_prefix = 'double-image'
    self.assert_output_result('chr')
    # TODO: Palette has background color 1.
    self.assert_output_result('palette')
    self.assert_output_result('nametable')
    self.assert_output_result('nametable1')
    self.assert_output_result('attribute')
    self.assert_output_result('attribute1')

  def test_error_too_many_tiles(self):
    """If there are more tiles than can fit in CHR, throw error."""
    img = Image.open('testdata/257tiles.png')
    self.process_image(img)
    self.assertTrue(self.err.has())
    es = self.err.get()
    self.assertEqual(len(es), 1)
    msg = '{0} {1}'.format(type(es[0]).__name__, es[0])
    self.assertEqual(msg, 'NametableOverflow 256 at tile (8y,0x)')

  def test_error_even_more_tiles(self):
    """If there are too many tiles, report how many are needed as an error."""
    img = Image.open('testdata/276tiles.png')
    self.process_image(img)
    self.assertTrue(self.err.has())
    es = self.err.get()
    self.assertEqual(len(es), 1)
    msg = '{0} {1}'.format(type(es[0]).__name__, es[0])
    self.assertEqual(msg, 'NametableOverflow 275 at tile (8y,0x)')

  def test_error_image(self):
    """Multiple errors, as an image."""
    img = Image.open('testdata/full-image-with-error.png')
    self.process_image(img)
    self.args.error_outfile = self.args.tmppng('error')
    self.create_output()
    self.assertTrue(self.err.has())
    errs = self.err.get()
    expect_errors = ['PaletteOverflowError @ block (1y,3x)',
                     'PaletteOverflowError @ tile (2y,10x)',
                     ('CouldntConvertRGB : R ff, G ff, B 00' +
                      ' @ tile (4y,1x) / pixel (33y,10x)')]
    actual_errors = ['%s %s' % (type(e).__name__, str(e)) for e in errs]
    self.assertEqual(actual_errors, expect_errors)
    renderer = view_renderer.ViewRenderer()
    renderer.create_error_view(self.args.error_outfile, img, errs)
    self.assert_file_eq(self.args.error_outfile,
                        'testdata/errors-full-image.png')

  def test_error_image_small_square(self):
    """Multiple errors, with a 128x128 image, outputs correctly."""
    img = Image.open('testdata/full-image-small-square-with-error.png')
    self.process_image(img)
    self.args.error_outfile = self.args.tmppng('error')
    self.create_output()
    self.assertTrue(self.err.has())
    errs = self.err.get()
    expect_errors = ['PaletteOverflowError @ block (1y,3x)',
                     'PaletteOverflowError @ tile (2y,10x)',
                     ('CouldntConvertRGB : R ff, G ff, B 00' +
                      ' @ tile (4y,1x) / pixel (33y,10x)')]
    actual_errors = ['%s %s' % (type(e).__name__, str(e)) for e in errs]
    self.assertEqual(actual_errors, expect_errors)
    renderer = view_renderer.ViewRenderer()
    renderer.create_error_view(self.args.error_outfile, img, errs)
    self.assert_file_eq(self.args.error_outfile,
                        'testdata/errors-full-image-small-square.png')


if __name__ == '__main__':
  unittest.main()
