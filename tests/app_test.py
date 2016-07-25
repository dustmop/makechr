import unittest

import context
from makechr import app, image_processor, view_renderer

import filecmp
import os
from PIL import Image
import tempfile


class MockArgs(object):
  def __init__(self):
    self.dir = tempfile.mkdtemp()
    self.palette_view = self.tmppng('pal')
    self.colorization_view = self.tmppng('color')
    self.reuse_view = self.tmppng('reuse')
    self.nametable_view = self.tmppng('nt')
    self.chr_view = self.tmppng('chr')
    self.grid_view = self.tmppng('grid')
    self.bg_color = None
    self.is_sprite = False
    self.is_locked_tiles = False
    self.order = None
    self.compile = None
    self.output = self.tmpfile('actual-%s.dat')

  def tmppng(self, name):
    return os.path.join(self.dir, 'actual-%s.png' % name)

  def tmpfile(self, template):
    return os.path.join(self.dir, template)


class AppTests(unittest.TestCase):
  def setUp(self):
    self.args = MockArgs()
    self.golden_file_prefix = 'full-image'
    self.traversal = 'horizontal'

  def process_image(self, img, palette_text=None):
    self.processor = image_processor.ImageProcessor()
    self.processor.process_image(img, palette_text, self.args.bg_color,
                                 self.traversal, self.args.is_sprite,
                                 self.args.is_locked_tiles)
    self.ppu_memory = self.processor.ppu_memory()
    self.err = self.processor.err()

  def create_output(self):
    a = app.Application()
    a.create_output(self.ppu_memory, self.args, self.traversal)

  def test_views(self):
    img = Image.open('testdata/full-image.png')
    self.process_image(img)
    a = app.Application()
    a.create_views(self.ppu_memory, self.processor, self.args, img)
    self.assert_file_eq(self.args.palette_view, self.golden('pal', 'png'))
    self.assert_file_eq(self.args.colorization_view,
                        self.golden('color', 'png'))
    self.assert_file_eq(self.args.reuse_view, self.golden('reuse', 'png'))
    self.assert_file_eq(self.args.nametable_view, self.golden('nt', 'png'))
    self.assert_file_eq(self.args.chr_view, self.golden('chr', 'png'))
    self.assert_file_eq(self.args.grid_view, self.golden('grid', 'png'))

  def test_output(self):
    img = Image.open('testdata/full-image.png')
    self.process_image(img)
    self.create_output()
    self.assert_output_result('chr')
    self.assert_output_result('nametable')
    self.assert_output_result('palette')
    self.assert_output_result('attribute')

  def test_output_for_bottom_attributes(self):
    img = Image.open('testdata/full-image-bottom-attr.png')
    self.process_image(img)
    self.create_output()
    self.assert_output_result('chr')
    self.assert_output_result('nametable', golden_suffix='-bottom-attr')
    self.assert_output_result('palette')
    self.assert_output_result('attribute', golden_suffix='-bottom-attr')

  def test_output_implied_bg_color(self):
    img = Image.open('testdata/implied-bg-color.png')
    self.process_image(img)
    self.create_output()
    self.golden_file_prefix = 'implied-bg-color'
    self.assert_output_result('chr')
    self.assert_output_result('nametable')
    self.assert_output_result('palette')
    self.assert_output_result('attribute')

  def test_output_uses_safe_black(self):
    img = Image.open('testdata/safe-black.png')
    self.process_image(img)
    self.create_output()
    self.golden_file_prefix = 'safe-black'
    self.assert_output_result('palette')

  def test_output_combines_color_with_background(self):
    img = Image.open('testdata/combine-colors.png')
    self.args.bg_color = 0x0f
    self.process_image(img)
    self.create_output()
    self.golden_file_prefix = 'combine-colors'
    self.assert_output_result('chr')
    self.assert_output_result('nametable')
    self.assert_output_result('palette')
    self.assert_output_result('attribute')

  def test_output_for_locked_tiles(self):
    img = Image.open('testdata/full-image.png')
    self.args.is_locked_tiles = True
    self.process_image(img)
    self.create_output()
    self.assert_output_result('chr', golden_suffix='-locked-tiles')
    self.assert_not_exist('nametable')
    self.assert_output_result('palette')
    self.assert_output_result('attribute')

  def test_output_for_locked_tiles_small_square(self):
    img = Image.open('testdata/full-image-small-square.png')
    self.args.is_locked_tiles = True
    self.process_image(img)
    self.create_output()
    self.assert_output_result('chr', golden_suffix='-small-square')
    self.assert_not_exist('nametable')
    self.assert_output_result('palette')
    self.assert_output_result('attribute')

  def test_output_from_memory_dump(self):
    memfile = 'testdata/full-image-mem.bin'
    a = app.Application()
    a.read_memory(memfile, self.args)
    self.assert_output_result('chr')
    self.assert_output_result('nametable')
    self.assert_output_result('palette')
    self.assert_output_result('attribute')

  def test_output_order1(self):
    img = Image.open('testdata/full-image.png')
    self.args.order = 1
    self.process_image(img)
    self.create_output()
    self.assert_output_result('chr', golden_suffix='-order1')
    self.assert_output_result('nametable')
    self.assert_output_result('palette')
    self.assert_output_result('attribute')

  def test_output_traverse_block(self):
    img = Image.open('testdata/full-image.png')
    self.traversal='block'
    self.process_image(img)
    self.create_output()
    self.assert_output_result('chr', golden_suffix='-traverse-block')
    self.assert_output_result('nametable', golden_suffix='-traverse-block')
    self.assert_output_result('palette')
    self.assert_output_result('attribute')

  def test_output_palette(self):
    img = Image.open('testdata/full-image.png')
    palette_text = 'P/30-38-16-01/30-19-16-16/'
    self.process_image(img, palette_text=palette_text)
    self.create_output()
    self.assert_output_result('chr')
    self.assert_output_result('nametable')
    self.assert_output_result('palette', golden_suffix='-explicit-text')
    self.assert_output_result('attribute')

  def test_output_background_color(self):
    img = Image.open('testdata/full-image.png')
    self.args.bg_color = 0x16
    self.process_image(img)
    self.create_output()
    self.assert_output_result('chr', golden_suffix='-bg-color')
    self.assert_output_result('nametable', golden_suffix='-bg-color')
    self.assert_output_result('palette', golden_suffix='-bg-color')
    self.assert_output_result('attribute')

  def test_error_background_color_conflict(self):
    img = Image.open('testdata/full-image.png')
    palette_text = 'P/30-38-16-01/30-19-01-01/'
    self.args.bg_color = 1
    self.process_image(img, palette_text=palette_text)
    self.assertTrue(self.err.has())
    es = self.err.get()
    for e in es:
      msg = '{0} {1}'.format(type(e).__name__, e)
      self.assertEqual(msg, ('PaletteBackgroundColorConflictError between '
                             'palette /30/ <> bg color /1/'))

  def test_error_palette_no_choice(self):
    img = Image.open('testdata/full-image.png')
    palette_text = 'P/30-38-16-01/'
    self.process_image(img, palette_text=palette_text)
    self.assertTrue(self.err.has())
    es = self.err.get()
    for e in es:
      msg = '{0} {1}'.format(type(e).__name__, e)
      self.assertEqual(msg, 'PaletteNoChoiceError at (2y,4x)')

  def test_error_too_many_tiles(self):
    img = Image.open('testdata/257tiles.png')
    self.process_image(img)
    self.assertTrue(self.err.has())
    es = self.err.get()
    for e in es:
      msg = '{0} {1}'.format(type(e).__name__, e)
      self.assertEqual(msg, 'NametableOverflow $100 @ tile (8y,0x)')

  def test_output_sprite(self):
    img = Image.open('testdata/reticule.png')
    self.args.bg_color = 0x30
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
    img = Image.open('testdata/reticule.png')
    self.args.bg_color = 0x30
    self.args.order = 1
    self.process_image(img)
    self.create_output()
    self.golden_file_prefix = 'reticule'
    self.assert_output_result('chr')
    self.assert_output_result('nametable')
    self.assert_output_result('palette')
    self.assert_output_result('attribute')
    self.assert_not_exist('spritelist')

  def test_output_sprite_more_colors(self):
    img = Image.open('testdata/reticule-more.png')
    self.args.bg_color = 0x30
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
    img = Image.open('testdata/reticule-more.png')
    self.args.bg_color = 0x30
    self.process_image(img)
    self.assertTrue(self.err.has())
    errs = self.err.get()
    expect_errors = ['PaletteOverflowError @ block (0y,0x)',
                     'PaletteOverflowError @ block (0y,1x)',
                     'PaletteOverflowError @ block (1y,0x)',
                     'PaletteOverflowError @ block (1y,1x)']
    actual_errors = ['%s %s' % (type(e).__name__, str(e)) for e in errs]
    self.assertEqual(actual_errors, expect_errors)

  def test_output_valiant(self):
    img = Image.open('testdata/full-image.png')
    self.process_image(img)
    self.args.output = self.args.tmpfile('full-image.o')
    self.create_output()
    self.assert_file_eq(self.args.output, self.golden(None, 'o'))

  def test_error(self):
    img = Image.open('testdata/full-image-with-error.png')
    self.process_image(img)
    self.args.error_outfile = self.args.tmppng('error')
    self.create_output()
    self.assertTrue(self.err.has())
    errs = self.err.get()
    expect_errors = ['PaletteOverflowError @ block (1y,3x)',
                     'PaletteOverflowError @ tile (2y,10x)',
                     ('ColorNotAllowedError @ tile (4y,1x) and ' +
                      'pixel (1y,2x) - "ff,ff,00"')]
    actual_errors = ['%s %s' % (type(e).__name__, str(e)) for e in errs]
    self.assertEqual(actual_errors, expect_errors)
    renderer = view_renderer.ViewRenderer()
    renderer.create_error_view(self.args.error_outfile, img, errs)
    self.assert_file_eq(self.args.error_outfile,
                        'testdata/errors-full-image.png')

  def test_output_valiant_for_offset_image(self):
    img = Image.open('testdata/offset-image.png')
    palette_text = 'P/30-30-30-30/30-01-38-16/'
    self.process_image(img, palette_text=palette_text)
    self.args.output = self.args.tmpfile('offset-image.o')
    self.create_output()
    self.golden_file_prefix = 'offset-image'
    self.assert_file_eq(self.args.output, self.golden('normal', 'o'))

  def test_output_valiant_for_offset_image_locked(self):
    img = Image.open('testdata/offset-image.png')
    palette_text = 'P/30-30-30-30/30-01-38-16/'
    self.args.is_locked_tiles = True
    self.process_image(img, palette_text=palette_text)
    self.args.output = self.args.tmpfile('offset-image.o')
    self.create_output()
    self.golden_file_prefix = 'offset-image'
    self.assert_file_eq(self.args.output, self.golden('locked', 'o'))

  def test_output_valiant_order1(self):
    img = Image.open('testdata/full-image.png')
    self.process_image(img)
    self.args.order = 1
    self.args.output = self.args.tmpfile('full-image.o')
    self.create_output()
    self.assert_file_eq(self.args.output, self.golden('order1', 'o'))

  def test_output_valiant_traverse_block(self):
    img = Image.open('testdata/full-image.png')
    self.traversal='block'
    self.process_image(img)
    self.args.output = self.args.tmpfile('full-image.o')
    self.create_output()
    self.assert_file_eq(self.args.output, self.golden('traverse-block', 'o'))

  def test_output_valiant_background_color(self):
    img = Image.open('testdata/full-image.png')
    self.args.bg_color = 0x16
    self.process_image(img)
    self.args.output = self.args.tmpfile('full-image.o')
    self.create_output()
    self.assert_file_eq(self.args.output, self.golden('bg-color', 'o'))

  def test_output_valiant_sprite(self):
    img = Image.open('testdata/reticule.png')
    self.args.bg_color = 0x30
    self.args.is_sprite = True
    self.process_image(img)
    self.args.output = self.args.tmpfile('reticule.o')
    self.create_output()
    self.golden_file_prefix = 'reticule'
    self.assert_file_eq(self.args.output, self.golden(None, 'o'))

  def test_output_valiant_sprite_more(self):
    img = Image.open('testdata/reticule-more.png')
    self.args.bg_color = 0x30
    self.args.is_sprite = True
    self.process_image(img)
    self.args.output = self.args.tmpfile('reticule-more.o')
    self.create_output()
    self.golden_file_prefix = 'reticule-more'
    self.assert_file_eq(self.args.output, self.golden(None, 'o'))

  def assert_output_result(self, name, golden_suffix=''):
    actual_file = self.args.output % name
    expect_file = self.golden(name + golden_suffix, 'dat')
    self.assert_file_eq(actual_file, expect_file)

  def assert_not_exist(self, name):
    missing_file = self.args.output % name
    self.assertFalse(os.path.exists(missing_file))

  def golden(self, name, ext):
    if name:
      return 'testdata/%s-%s.%s' % (self.golden_file_prefix, name, ext)
    else:
      return 'testdata/%s.%s' % (self.golden_file_prefix, ext)

  def assert_file_eq(self, actual_file, expect_file):
    self.assertTrue(filecmp.cmp(actual_file, expect_file, shallow=False),
                    "Files did not match actual:%s expect:%s" % (
        actual_file, expect_file))


if __name__ == '__main__':
  unittest.main()
