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
    self.palette_view = None
    self.colorization_view = None
    self.reuse_view = None
    self.nametable_view = None
    self.chr_view = None
    self.grid_view = None
    self.compile = self.tmpfile('rom.nes')
    self.output = self.tmpfile('full-image-%s.dat')

  def tmpfile(self, template):
    return os.path.join(self.dir, template)


class RomBuilderTests(unittest.TestCase):
  def test_output(self):
    img = Image.open('testdata/full-image.png')
    processor = image_processor.ImageProcessor()
    processor.process_image(img, None)
    args = MockArgs()
    a = app.Application()
    a.create_output(processor.ppu_memory(), args)
    actual_file = args.compile
    expect_file = 'testdata/full-image-rom.nes'
    self.assert_file_eq(actual_file, expect_file)

  def assert_file_eq(self, actual_file, expect_file):
    self.assertTrue(filecmp.cmp(actual_file, expect_file, shallow=False),
                    "Files did not match actual:%s expect:%s" % (
        actual_file, expect_file))


if __name__ == '__main__':
  unittest.main()
