import unittest

import app
import filecmp
import image_processor
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
    self.compile = None
    self.output = self.tmpfile('full-image-%s.dat')

  def tmppng(self, name):
    return os.path.join(self.dir, 'full-image-%s.png' % name)

  def tmpfile(self, template):
    return os.path.join(self.dir, template)


class AppTests(unittest.TestCase):
  def test_views(self):
    img = Image.open('testdata/full-image.png')
    processor = image_processor.ImageProcessor()
    processor.process_image(img, None, None)
    self.args = MockArgs()
    a = app.Application()
    a.create_views(processor, self.args, img)
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
    processor.process_image(img, None, None)
    self.args = MockArgs()
    a = app.Application()
    a.create_output(processor, self.args)
    self.assert_output_result('chr')
    self.assert_output_result('nametable')
    self.assert_output_result('palette')
    self.assert_output_result('attribute')

  def assert_output_result(self, name):
    actual_file = self.args.output % name
    expect_file = self.golden(name, 'dat')
    self.assert_file_eq(actual_file, expect_file)

  def golden(self, name, ext):
    return 'testdata/full-image-%s.%s' % (name, ext)

  def assert_file_eq(self, actual_file, expect_file):
    self.assertTrue(filecmp.cmp(actual_file, expect_file, shallow=False))


if __name__ == '__main__':
  unittest.main()
