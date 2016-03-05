import unittest

import context
from makechr import app, memory_importer

import filecmp
import os
import tempfile


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
    mem = importer.read('testdata/full-image.mem')
    a = app.Application()
    a.create_output(mem, self.args, 'horizontal')
    self.assert_output_result('chr')
    self.assert_output_result('nametable')
    self.assert_output_result('palette')
    self.assert_output_result('attribute')

  def assert_output_result(self, name, golden_suffix=''):
    actual_file = self.args.output % name
    expect_file = self.golden(name + golden_suffix, 'dat')
    self.assert_file_eq(actual_file, expect_file)

  def golden(self, name, ext):
    return 'testdata/%s-%s.%s' % (self.golden_file_prefix, name, ext)

  def assert_file_eq(self, actual_file, expect_file):
    self.assertTrue(filecmp.cmp(actual_file, expect_file, shallow=False),
                    "Files did not match actual:%s expect:%s" % (
        actual_file, expect_file))


if __name__ == '__main__':
  unittest.main()
