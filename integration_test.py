import unittest
import subprocess
import gen.valiant_pb2 as valiant
from google.protobuf import text_format
import os
import tempfile
import filecmp


class IntegrationTests(unittest.TestCase):
  def setUp(self):
    self.tmpdir = tempfile.mkdtemp()
    self.output_name = os.path.join(self.tmpdir, 'full-image.o')
    self.golden_file_prefix = 'full-image'
    self.out = self.err = None

  def makechr(self, args):
    cmd = 'python makechr.py ' + ' '.join(args)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    (self.out, self.err) = p.communicate()

  def test_basic(self):
    args = ['testdata/full-image.png', '-o', self.output_name]
    self.makechr(args)
    self.assert_file_eq(self.output_name, self.golden(None, 'o'))

  def test_order(self):
    # Order 0.
    args = ['testdata/full-image.png', '-o', self.output_name, '-r', '0']
    self.makechr(args)
    self.assert_file_eq(self.output_name, self.golden(None, 'o'))
    # Order 1.
    args = ['testdata/full-image.png', '-o', self.output_name, '-r', '1']
    self.makechr(args)
    self.assert_file_eq(self.output_name, self.golden('order1', 'o'))

  def test_bg_color(self):
    args = ['testdata/full-image.png', '-o', self.output_name, '-b', '16']
    self.makechr(args)
    self.assert_file_eq(self.output_name, self.golden('bg-color', 'o'))

  def test_show_stats(self):
    args = ['testdata/full-image.png', '-o', self.output_name, '-z']
    self.makechr(args)
    self.assert_file_eq(self.output_name, self.golden(None, 'o'))
    expect = """Number of dot-profiles: 6
Number of tiles: 6
Palette: P/30-38-16-01/30-19/
"""
    self.assertEqual(self.out, expect)

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
