import unittest

import app
import filecmp
import image_processor
import os
from PIL import Image
import tempfile
import view_renderer


class MockArgs(object):
  def __init__(self):
    self.dir = tempfile.mkdtemp()
    self.palette_view = self.tmppng('pal')
    self.colorization_view = self.tmppng('color')
    self.reuse_view = self.tmppng('reuse')
    self.nametable_view = self.tmppng('nt')
    self.chr_view = self.tmppng('chr')
    self.grid_view = self.tmppng('grid')
    self.is_locked_tiles = False
    self.order = None
    self.compile = None
    self.output = self.tmpfile('full-image-%s.dat')

  def tmppng(self, name):
    return os.path.join(self.dir, 'full-image-%s.png' % name)

  def tmpfile(self, template):
    return os.path.join(self.dir, template)


class AppTests(unittest.TestCase):
  def setUp(self):
    self.args = MockArgs()
    self.golden_file_prefix = 'full-image'

  def test_views(self):
    img = Image.open('testdata/full-image.png')
    processor = image_processor.ImageProcessor()
    processor.process_image(img, None, None, False)
    a = app.Application()
    a.create_views(processor.ppu_memory(), processor, self.args, img)
    self.assert_file_eq(self.args.palette_view, self.golden('pal', 'png'))
    self.assert_file_eq(self.args.colorization_view,
                        self.golden('color', 'png'))
    self.assert_file_eq(self.args.reuse_view, self.golden('reuse', 'png'))
    self.assert_file_eq(self.args.nametable_view, self.golden('nt', 'png'))
    self.assert_file_eq(self.args.chr_view, self.golden('chr', 'png'))
    self.assert_file_eq(self.args.grid_view, self.golden('grid', 'png'))

  def test_output(self):
    img = Image.open('testdata/full-image.png')
    processor = image_processor.ImageProcessor()
    processor.process_image(img, None, None, False)
    a = app.Application()
    a.create_output(processor.ppu_memory(), self.args)
    self.assert_output_result('chr')
    self.assert_output_result('nametable')
    self.assert_output_result('palette')
    self.assert_output_result('attribute')

  def test_output_for_bottom_attributes(self):
    img = Image.open('testdata/full-image-bottom-attr.png')
    processor = image_processor.ImageProcessor()
    processor.process_image(img, None, None, False)
    a = app.Application()
    a.create_output(processor.ppu_memory(), self.args)
    self.assert_output_result('chr')
    self.assert_output_result('nametable', golden_suffix='-bottom-attr')
    self.assert_output_result('palette')
    self.assert_output_result('attribute', golden_suffix='-bottom-attr')

  def test_output_implied_bg_color(self):
    img = Image.open('testdata/implied-bg-color.png')
    processor = image_processor.ImageProcessor()
    processor.process_image(img, None, None, False)
    a = app.Application()
    a.create_output(processor.ppu_memory(), self.args)
    self.golden_file_prefix = 'implied-bg-color'
    self.assert_output_result('chr')
    self.assert_output_result('nametable')
    self.assert_output_result('palette')
    self.assert_output_result('attribute')

  def test_output_for_locked_tiles(self):
    img = Image.open('testdata/full-image.png')
    processor = image_processor.ImageProcessor()
    self.args.is_locked_tiles = True
    processor.process_image(img, None, None, self.args.is_locked_tiles)
    a = app.Application()
    a.create_output(processor.ppu_memory(), self.args)
    self.assert_output_result('chr', golden_suffix='-locked-tiles')
    self.assert_not_exist('nametable')
    self.assert_output_result('palette')
    self.assert_output_result('attribute')

  def test_output_for_locked_tiles_small_square(self):
    img = Image.open('testdata/full-image-small-square.png')
    processor = image_processor.ImageProcessor()
    self.args.is_locked_tiles = True
    processor.process_image(img, None, None, self.args.is_locked_tiles)
    a = app.Application()
    a.create_output(processor.ppu_memory(), self.args)
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
    processor = image_processor.ImageProcessor()
    processor.process_image(img, None, None, False)
    self.args.order = 1
    a = app.Application()
    a.create_output(processor.ppu_memory(), self.args)
    self.assert_output_result('chr', golden_suffix='-order1')
    self.assert_output_result('nametable')
    self.assert_output_result('palette')
    self.assert_output_result('attribute')

  def test_output_palette(self):
    img = Image.open('testdata/full-image.png')
    palette_text = 'P/30-38-16-01/30-19-01-01/'
    processor = image_processor.ImageProcessor()
    processor.process_image(img, palette_text, None, False)
    a = app.Application()
    a.create_output(processor.ppu_memory(), self.args)
    self.assert_output_result('chr')
    self.assert_output_result('nametable')
    self.assert_output_result('palette', golden_suffix='-explicit-text')
    self.assert_output_result('attribute')

  def test_output_background_color(self):
    img = Image.open('testdata/full-image.png')
    processor = image_processor.ImageProcessor()
    processor.process_image(img, None, 1, False)
    a = app.Application()
    a.create_output(processor.ppu_memory(), self.args)
    self.assert_output_result('chr', golden_suffix='-bg-color')
    self.assert_output_result('nametable', golden_suffix='-bg-color')
    self.assert_output_result('palette', golden_suffix='-bg-color')
    self.assert_output_result('attribute')

  def test_output_background_color_conflict(self):
    img = Image.open('testdata/full-image.png')
    palette_text = 'P/30-38-16-01/30-19-01-01/'
    processor = image_processor.ImageProcessor()
    processor.process_image(img, palette_text, 1, False)
    self.assertTrue(processor.err().has())
    es = processor.err().get()
    for e in es:
      msg = '{0} {1}'.format(type(e).__name__, e)
      self.assertEqual(msg, ('PaletteBackgroundColorConflictError between '
                             'palette /30/ <> bg color /1/'))

  def test_output_valiant(self):
    img = Image.open('testdata/full-image.png')
    processor = image_processor.ImageProcessor()
    processor.process_image(img, None, None, False)
    self.args.output = self.args.tmpfile('full-image.o')
    a = app.Application()
    a.create_output(processor.ppu_memory(), self.args)
    self.assert_file_eq(self.args.output, self.golden('valiant', 'o'))

  def test_error(self):
    img = Image.open('testdata/full-image-with-error.png')
    processor = image_processor.ImageProcessor()
    processor.process_image(img, None, None, False)
    self.args.error_outfile = self.args.tmppng('error')
    a = app.Application()
    a.create_output(processor.ppu_memory(), self.args)
    self.assertTrue(processor.err().has())
    errs = processor.err().get()
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
    processor = image_processor.ImageProcessor()
    processor.process_image(img, palette_text, None, False)
    self.args.output = self.args.tmpfile('offset-image.o')
    a = app.Application()
    a.create_output(processor.ppu_memory(), self.args)
    self.golden_file_prefix = 'offset-image'
    self.assert_file_eq(self.args.output, self.golden('normal', 'o'))

  def test_output_valiant_for_offset_image_locked(self):
    img = Image.open('testdata/offset-image.png')
    palette_text = 'P/30-30-30-30/30-01-38-16/'
    processor = image_processor.ImageProcessor()
    self.args.is_locked_tiles = True
    processor.process_image(img, palette_text, None, self.args.is_locked_tiles)
    self.args.output = self.args.tmpfile('offset-image.o')
    a = app.Application()
    a.create_output(processor.ppu_memory(), self.args)
    self.golden_file_prefix = 'offset-image'
    self.assert_file_eq(self.args.output, self.golden('locked', 'o'))

  def test_output_valiant_order1(self):
    img = Image.open('testdata/full-image.png')
    processor = image_processor.ImageProcessor()
    processor.process_image(img, None, None, False)
    self.args.order = 1
    self.args.output = self.args.tmpfile('full-image.o')
    a = app.Application()
    a.create_output(processor.ppu_memory(), self.args)
    self.assert_file_eq(self.args.output, self.golden('valiant-order1', 'o'))

  def assert_output_result(self, name, golden_suffix=''):
    actual_file = self.args.output % name
    expect_file = self.golden(name + golden_suffix, 'dat')
    self.assert_file_eq(actual_file, expect_file)

  def assert_not_exist(self, name):
    missing_file = self.args.output % name
    self.assertFalse(os.path.exists(missing_file))

  def golden(self, name, ext):
    return 'testdata/%s-%s.%s' % (self.golden_file_prefix, name, ext)

  def assert_file_eq(self, actual_file, expect_file):
    self.assertTrue(filecmp.cmp(actual_file, expect_file, shallow=False),
                    "Files did not match actual:%s expect:%s" % (
        actual_file, expect_file))


if __name__ == '__main__':
  unittest.main()
