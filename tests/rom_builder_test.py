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
    self.palette_view = None
    self.colorization_view = None
    self.reuse_view = None
    self.nametable_view = None
    self.chr_view = None
    self.grid_view = None
    self.bg_color = None
    self.is_sprite = False
    self.is_locked_tiles = False
    self.order = None
    self.compile = self.tmpfile('rom.nes')
    self.output = self.tmpfile('full-image-%s.dat')

  def tmpfile(self, template):
    return os.path.join(self.dir, template)


class RomBuilderTests(unittest.TestCase):
  def setUp(self):
    self.args = MockArgs()

  def process_image(self, img, palette_text=None, traversal=None):
    if not traversal:
      traversal = 'horizontal'
    self.processor = image_processor.ImageProcessor()
    self.processor.process_image(img, palette_text, self.args.bg_color,
                                 traversal, self.args.is_sprite,
                                 self.args.is_locked_tiles)
    self.ppu_memory = self.processor.ppu_memory()

  def test_output(self):
    img = Image.open('testdata/full-image.png')
    self.process_image(img)
    a = app.Application()
    a.create_output(self.ppu_memory, self.args, 'horizontal')
    actual_file = self.args.compile
    expect_file = 'testdata/full-image-rom.nes'
    self.assert_file_eq(actual_file, expect_file)

  def test_output_using_valiant(self):
    img = Image.open('testdata/full-image.png')
    self.process_image(img)
    self.args.output = self.args.tmpfile('full-image.o')
    a = app.Application()
    a.create_output(self.ppu_memory, self.args, 'horizontal')
    actual_file = self.args.compile
    expect_file = 'testdata/full-image-rom.nes'
    self.assert_file_eq(actual_file, expect_file)

  def test_output_with_locked_tiles(self):
    img = Image.open('testdata/full-image.png')
    self.args.is_locked_tiles = True
    self.process_image(img)
    a = app.Application()
    a.create_output(self.ppu_memory, self.args, 'horizontal')
    actual_file = self.args.compile
    expect_file = 'testdata/full-image-rom-locked-tiles.nes'
    self.assert_file_eq(actual_file, expect_file)

  def test_output_square_small_with_locked_tiles(self):
    img = Image.open('testdata/full-image-small-square.png')
    self.args.is_locked_tiles = True
    self.process_image(img)
    a = app.Application()
    a.create_output(self.ppu_memory, self.args, 'horizontal')
    actual_file = self.args.compile
    expect_file = 'testdata/full-image-rom-small-square-locked-tiles.nes'
    self.assert_file_eq(actual_file, expect_file)

  def assert_file_eq(self, actual_file, expect_file):
    self.assertTrue(filecmp.cmp(actual_file, expect_file, shallow=False),
                    "Files did not match actual:%s expect:%s" % (
        actual_file, expect_file))


if __name__ == '__main__':
  unittest.main()
