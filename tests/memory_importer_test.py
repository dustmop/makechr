import unittest

import context
from makechr import app, errors, memory_importer

import filecmp
import os
import tempfile
from PIL import Image, ImageChops


class MockArgs(object):
  def __init__(self):
    self.dir = tempfile.mkdtemp()
    self.output = self.tmpfile('full-image-%s.dat')
    self.order = None
    self.is_sprite = None
    self.is_locked_tiles = None
    self.compile = None

  def tmpfile(self, template):
    return os.path.join(self.dir, template)


class MemoryImporterTests(unittest.TestCase):
  def setUp(self):
    self.args = MockArgs()
    self.golden_file_prefix = 'full-image'

  def test_import(self):
    importer = memory_importer.MemoryImporter()
    mem = importer.read_ram('testdata/full-image.mem')
    a = app.Application()
    a.create_output(mem, self.args, 'horizontal')
    self.assert_output_result('chr')
    self.assert_output_result('nametable')
    self.assert_output_result('palette')
    self.assert_output_result('attribute')

  def test_import_and_render(self):
    importer = memory_importer.MemoryImporter()
    mem = importer.read_ram('testdata/full-image.mem')
    self.args.output = self.args.tmpfile('full-image.png')
    a = app.Application()
    a.create_output(mem, self.args, 'horizontal')
    self.assert_equal_image(self.args.output, 'testdata/full-image.png')

  def test_import_error_bad_size(self):
    importer = memory_importer.MemoryImporter()
    with self.assertRaises(errors.FileFormatError) as e:
      importer.read_ram('testdata/full-image-chr.dat')
      self.assertEqual(e.file_size, 0x2000)

  def assert_output_result(self, name, golden_suffix=''):
    actual_file = self.args.output % name
    expect_file = self.golden(name + golden_suffix, 'dat')
    self.assert_file_eq(actual_file, expect_file)

  def assert_equal_image(self, actual_file, expect_file):
    actual_img = Image.open(actual_file)
    expect_img = Image.open(expect_file)
    bbox = ImageChops.difference(actual_img, expect_img).getbbox()
    self.assertTrue(bbox is None)

  def golden(self, name, ext):
    return 'testdata/%s-%s.%s' % (self.golden_file_prefix, name, ext)

  def assert_file_eq(self, actual_file, expect_file):
    self.assertTrue(filecmp.cmp(actual_file, expect_file, shallow=False),
                    "Files did not match actual:%s expect:%s" % (
        actual_file, expect_file))


if __name__ == '__main__':
  unittest.main()
