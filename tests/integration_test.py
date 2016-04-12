import unittest

import context
from makechr.gen import valiant_pb2 as valiant
from google.protobuf import text_format

import filecmp
import os
import subprocess
import tempfile


class IntegrationTests(unittest.TestCase):
  def setUp(self):
    self.tmpdir = tempfile.mkdtemp()
    self.output_name = os.path.join(self.tmpdir, 'full-image.o')
    self.golden_file_prefix = 'full-image'
    self.out = self.err = None

  def makechr(self, args, is_expect_fail=False):
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    makechr = os.path.join(curr_dir, '../makechr/makechr.py')
    cmd = 'python ' + makechr + ' ' + ' '.join(args)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    (self.out, self.err) = p.communicate()
    self.returncode = p.returncode
    if is_expect_fail:
      return
    if self.err:
      raise RuntimeError(self.err)

  def test_basic(self):
    args = ['testdata/full-image.png', '-o', self.output_name]
    self.makechr(args)
    self.assert_file_eq(self.output_name, self.golden(None, 'o'))
    self.assertEquals(self.returncode, 0)

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

  def test_error_too_many_tiles(self):
    args = ['testdata/257tiles.png', '-o', self.output_name]
    self.makechr(args, is_expect_fail=True)
    self.assertEquals(self.err, """Found 1 error:
NametableOverflow $100 @ tile (8y,0x)
To see errors visually, use -e command-line option.
""")
    self.assertEquals(self.returncode, 1)

  def test_error_view_renderer(self):
    error_view = os.path.join(self.tmpdir, 'error-no-choice.png')
    palette_text = 'P/30-38-16-01/'
    args = ['testdata/full-image.png', '-o', self.output_name, '-e', error_view,
            '-p', palette_text]
    self.makechr(args, is_expect_fail=True)
    self.assertEquals(self.err, """Found 1 error:
PaletteNoChoiceError at (2y,4x)
Errors displayed in "%s"
""" % error_view)
    self.assert_file_eq(error_view, self.golden('error-no-choice', 'png'))

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
