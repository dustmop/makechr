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
    self.assertEqual(self.out, '')

  def test_usage(self):
    args = ['-o', self.output_name]
    self.makechr(args)
    self.assertTrue(self.out.startswith('usage:'))

  def test_order(self):
    # Order 0.
    args = ['testdata/full-image.png', '-o', self.output_name, '-r', '0']
    self.makechr(args)
    self.assert_file_eq(self.output_name, self.golden(None, 'o'))
    # Order 1.
    args = ['testdata/full-image.png', '-o', self.output_name, '-r', '1']
    self.makechr(args)
    self.assert_file_eq(self.output_name, self.golden('order1', 'o'))
    self.assertEqual(self.out, '')

  def test_bg_color(self):
    args = ['testdata/full-image.png', '-o', self.output_name, '-b', '16']
    self.makechr(args)
    self.assert_file_eq(self.output_name, self.golden('bg-color', 'o'))
    self.assertEqual(self.out, '')

  def test_show_stats(self):
    args = ['testdata/full-image.png', '-o', self.output_name, '-z']
    self.makechr(args)
    self.assert_file_eq(self.output_name, self.golden(None, 'o'))
    expect = """Number of dot-profiles: 6
Number of tiles: 6
Palette: P/30-38-16-01/30-19/
"""
    self.assertEqual(self.out, expect)

  def test_import_memory_produce_png(self):
    self.output_name = os.path.join(self.tmpdir, 'full-image.png')
    args = ['-m', 'testdata/full-image.mem', '-o', self.output_name]
    self.makechr(args)
    self.assert_file_eq(self.output_name, self.golden(None, 'png'))
    self.assertEqual(self.out, '')

  def test_import_memory_produce_view(self):
    nt_view_name = os.path.join(self.tmpdir, 'nt.png')
    reuse_view_name = os.path.join(self.tmpdir, 'reuse.png')
    args = ['-m', 'testdata/full-image.mem', '-o', '/dev/null',
            '--nametable-view', nt_view_name, '--reuse-view', reuse_view_name,
            '--use-legacy-views']
    self.makechr(args)
    self.assert_file_eq(nt_view_name, self.golden('nt-legacy', 'png'))
    self.assert_file_eq(reuse_view_name, self.golden('reuse-legacy', 'png'))
    self.assertEqual(self.out, '')

  def test_import_valiant_produce_image(self):
    render_name = os.path.join(self.tmpdir, 'render.png')
    args = ['testdata/full-image.o', '-o', render_name]
    self.makechr(args)
    self.assert_file_eq(render_name, self.golden(None, 'png'))
    self.assertEqual(self.out, '')

  def test_sprite_8x16(self):
    self.output_name = os.path.join(self.tmpdir, 'reticule.o')
    self.golden_file_prefix = 'reticule'
    args = ['testdata/reticule.png', '-o', self.output_name, '-t', '8x16', '-s']
    self.makechr(args)
    self.assert_file_eq(self.output_name, self.golden('8x16', 'o'))
    self.assertEqual(self.out, '')

  def test_allow_too_many_tiles(self):
    output_tmpl = os.path.join(self.tmpdir, '%s.dat')
    args = ['testdata/257tiles.png', '-o', output_tmpl, '-s',
            '--allow-overflow', 's']
    self.makechr(args)
    self.assertEquals(self.returncode, 0)
    self.assert_file_eq(output_tmpl.replace('%s', 'chr'),
                        'testdata/allow_overflow_chr.dat')
    self.assert_file_eq(output_tmpl.replace('%s', 'spritelist'),
                        'testdata/allow_overflow_spritelist.dat')
    self.assert_file_eq(output_tmpl.replace('%s', 'palette'),
                        'testdata/allow_overflow_palette.dat')

  def test_extract_palette_ok(self):
    output_tmpl = os.path.join(self.tmpdir, '%s.dat')
    args = ['testdata/full-image-16color.png', '-o', output_tmpl]
    self.makechr(args)
    self.assertEquals(self.returncode, 0)
    self.assert_file_eq(output_tmpl.replace('%s', 'chr'),
                        'testdata/full-image-chr-16color.dat')
    self.assert_file_eq(output_tmpl.replace('%s', 'nametable'),
                        'testdata/full-image-nametable-16color.dat')
    self.assert_file_eq(output_tmpl.replace('%s', 'attribute'),
                        'testdata/full-image-attribute-16color.dat')
    self.assert_file_eq(output_tmpl.replace('%s', 'palette'),
                        'testdata/full-image-palette-16color.dat')

  def test_extract_palette_yes_flag(self):
    output_tmpl = os.path.join(self.tmpdir, '%s.dat')
    args = ['testdata/full-image-16color.png', '-o', output_tmpl, '-p', '+']
    self.makechr(args)
    self.assertEquals(self.returncode, 0)
    self.assert_file_eq(output_tmpl.replace('%s', 'chr'),
                        'testdata/full-image-chr-16color.dat')
    self.assert_file_eq(output_tmpl.replace('%s', 'nametable'),
                        'testdata/full-image-nametable-16color.dat')
    self.assert_file_eq(output_tmpl.replace('%s', 'attribute'),
                        'testdata/full-image-attribute-16color.dat')
    self.assert_file_eq(output_tmpl.replace('%s', 'palette'),
                        'testdata/full-image-palette-16color.dat')

  def test_extract_palette_no_flag(self):
    output_tmpl = os.path.join(self.tmpdir, '%s.dat')
    args = ['testdata/full-image-16color.png', '-o', output_tmpl, '-p', '-']
    self.makechr(args)
    self.assertEquals(self.returncode, 0)
    self.assert_file_eq(output_tmpl.replace('%s', 'chr'),
                        'testdata/full-image-chr.dat')
    self.assert_file_eq(output_tmpl.replace('%s', 'nametable'),
                        'testdata/full-image-nametable.dat')
    self.assert_file_eq(output_tmpl.replace('%s', 'attribute'),
                        'testdata/full-image-attribute.dat')
    self.assert_file_eq(output_tmpl.replace('%s', 'palette'),
                        'testdata/full-image-palette.dat')

  def test_error_no_output_dir(self):
    args = ['testdata/full-image.png', '-o', 'build/']
    self.makechr(args, is_expect_fail=True)
    self.assertEquals(self.err, """Directory does not exist: "build/"
""")
    self.assertEquals(self.returncode, 1)

  def test_error_too_many_tiles(self):
    args = ['testdata/257tiles.png', '-o', self.output_name]
    self.makechr(args, is_expect_fail=True)
    self.assertEquals(self.err, """Found 1 error:
NametableOverflow 256 at tile (8y,0x)
To see errors visually, use the "-e <error_image.png>" command-line option.
""")
    self.assertEquals(self.returncode, 1)

  def test_error_view_renderer(self):
    error_view = os.path.join(self.tmpdir, 'error-no-choice.png')
    palette_text = 'P/30-38-16-01/'
    args = ['testdata/full-image.png', '-o', self.output_name, '-e', error_view,
            '-p', palette_text]
    self.makechr(args, is_expect_fail=True)
    self.assertEquals(self.err, """Found 1 error:
PaletteNoChoiceError at (2y,4x) for 30-19
Errors displayed in "%s"
""" % error_view)
    self.assert_file_eq(error_view, self.golden('error-no-choice', 'png'))

  def test_error_input_and_import(self):
    args = ['testdata/full-image.png', '-m', 'testdata/full-image.mem',
            '-o', self.output_name]
    self.makechr(args, is_expect_fail=True)
    self.assertEquals(self.err, """Cannot both import memory and process input file""")
    self.assertEquals(self.returncode, 1)

  def test_error_8x16_without_sprite(self):
    self.output_name = os.path.join(self.tmpdir, 'reticule.o')
    self.golden_file_prefix = 'reticule'
    args = ['testdata/reticule.png', '-o', self.output_name, '-t', '8x16']
    self.makechr(args, is_expect_fail=True)
    self.assertEquals(self.err, """Command-line error: Traversal strategy \'8x16\' requires -s flag\n""")
    self.assertEquals(self.returncode, 1)

  def test_error_too_many_tiles_but_view(self):
    palette_view = os.path.join(self.tmpdir, 'palette_view.png')
    args = ['testdata/257tiles.png', '-o', self.output_name,
            '--palette-view', palette_view]
    self.makechr(args, is_expect_fail=True)
    self.assertEquals(self.err, """Found 1 error:
NametableOverflow 256 at tile (8y,0x)
To see errors visually, use the "-e <error_image.png>" command-line option.
""")
    self.assertEquals(self.returncode, 1)
    self.assert_file_eq(palette_view, 'testdata/too-many-tiles-pal.png')

  def test_error_makepal_border_not_found(self):
    args = ['testdata/error_border_not_found.png', '-o', self.output_name,
            '--makepal']
    self.makechr(args, is_expect_fail=True)
    self.assertEquals(self.err, """Found 1 error:
MakepalBorderNotFound 
To see errors visually, use the "-e <error_image.png>" command-line option.
""")
    self.assertEquals(self.returncode, 1)

  def test_error_extract_palette_failed(self):
    args = ['testdata/full-image-16color-badpal.png', '-o', self.output_name,
            '-p', '+']
    self.makechr(args, is_expect_fail=True)
    self.assertEquals(self.err, """Found 1 error:
PaletteExtractionError Background color did not match: 22 <> 35.
  Disable extraction using the flag "-p -"
To see errors visually, use the "-e <error_image.png>" command-line option.
""")
    self.assertEquals(self.returncode, 1)

  def test_error_extract_palette_failure_ignored(self):
    args = ['testdata/full-image-16color-badpal.png', '-o', self.output_name]
    self.makechr(args, is_expect_fail=True)
    self.assertEquals(self.err, '')
    self.assertEquals(self.returncode, 0)

  def test_error_image_not_found(self):
    args = ['testdata/not_found.png', '-o', self.output_name]
    self.makechr(args, is_expect_fail=True)
    self.assertEquals(self.err, """File not found: "testdata/not_found.png"
""")
    self.assertEquals(self.returncode, 1)

  def test_error_mem_not_found(self):
    args = ['-m', 'testdata/not_found.bin', '-o', self.output_name]
    self.makechr(args, is_expect_fail=True)
    self.assertEquals(self.err, """File not found: "testdata/not_found.bin"
""")
    self.assertEquals(self.returncode, 1)

  def golden(self, name, ext):
    if name:
      return 'testdata/%s-%s.%s' % (self.golden_file_prefix, name, ext)
    else:
      return 'testdata/%s.%s' % (self.golden_file_prefix, ext)

  def assert_file_eq(self, actual_file, expect_file):
    self.assertTrue(filecmp.cmp(actual_file, expect_file, shallow=False),
                    "Files did not match actual:%s expect:%s" % (
                      actual_file, os.path.abspath(expect_file)))


if __name__ == '__main__':
  unittest.main()
