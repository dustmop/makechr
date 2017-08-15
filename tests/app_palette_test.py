import general_app_test_util
import unittest

from PIL import Image

import context
from makechr import bg_color_spec, view_renderer


class AppPaletteTests(general_app_test_util.GeneralAppTests):
  def test_output_background_color(self):
    """Background color option sets the background color."""
    img = Image.open('testdata/full-image.png')
    self.args.bg_color = bg_color_spec.build('16')
    self.process_image(img)
    self.create_output()
    self.assert_output_result('chr', golden_suffix='-bg-color')
    self.assert_output_result('nametable', golden_suffix='-bg-color')
    self.assert_output_result('palette', golden_suffix='-bg-color')
    self.assert_output_result('attribute')

  def test_output_combines_color_with_background(self):
    """Palette guesser will take background color into account."""
    img = Image.open('testdata/combine-colors.png')
    self.args.bg_color = bg_color_spec.build('0f')
    self.process_image(img)
    self.create_output()
    self.golden_file_prefix = 'combine-colors'
    self.assert_output_result('chr')
    self.assert_output_result('nametable')
    self.assert_output_result('palette')
    self.assert_output_result('attribute')

  def test_output_background_color_pair(self):
    """Background color spec can have look value and fill value."""
    img = Image.open('testdata/full-image.png')
    self.args.bg_color = bg_color_spec.build('16=0f')
    self.process_image(img)
    self.create_output()
    self.assert_output_result('chr', golden_suffix='-bg-color')
    self.assert_output_result('nametable', golden_suffix='-bg-color')
    self.assert_output_result('palette', golden_suffix='-black-color')
    self.assert_output_result('attribute')

  def test_output_background_color_mask(self):
    """Using a mask requires the mask in the bg_color_spec."""
    img = Image.open('testdata/full-image-mask.png')
    self.args.bg_color = bg_color_spec.build('34=30')
    self.process_image(img)
    self.create_output()
    self.golden_file_prefix = 'full-image'
    self.assert_output_result('chr')
    self.assert_output_result('nametable')
    self.assert_output_result('palette')
    self.assert_output_result('attribute')

  def test_output_explicit_palette(self):
    """Explicit palette can be set with palette option."""
    img = Image.open('testdata/full-image.png')
    palette_text = 'P/30-38-16-01/30-19-16-16/'
    self.process_image(img, palette_text=palette_text)
    self.create_output()
    self.assert_output_result('chr')
    self.assert_output_result('nametable')
    self.assert_output_result('palette', golden_suffix='-explicit-text')
    self.assert_output_result('attribute')

  def test_output_with_palette_file(self):
    """Explicit palette can be set with palette option."""
    img = Image.open('testdata/full-image.png')
    palette_text = 'testdata/bigger_palette.o'
    self.process_image(img, palette_text=palette_text)
    self.create_output()
    self.assert_output_result('chr')
    self.assert_output_result('nametable')
    self.assert_output_result('palette', golden_suffix='-object-file')
    self.assert_output_result('attribute')

  def test_output_extract_palette(self):
    """Indexed image with 16-color palette will use that exact palette."""
    img = Image.open('testdata/full-image-16color.png')
    self.process_image(img)
    self.create_output()
    self.assert_output_result('chr', golden_suffix='-16color')
    self.assert_output_result('nametable', golden_suffix='-16color')
    self.assert_output_result('palette', golden_suffix='-16color')
    self.assert_output_result('attribute', golden_suffix='-16color')

  def test_error_background_color_conflict(self):
    """If background color does not match explicit palette, throw error."""
    img = Image.open('testdata/full-image.png')
    palette_text = 'P/30-38-16-01/30-19-01-01/'
    self.args.bg_color = bg_color_spec.build('01')
    self.process_image(img, palette_text=palette_text)
    self.assertTrue(self.err.has())
    es = self.err.get()
    for e in es:
      msg = '{0} {1}'.format(type(e).__name__, e)
      self.assertEqual(msg, ('PaletteBackgroundColorConflictError between '
                             'palette /30/ <> bg color /1/'))

  def test_error_too_many_subsets(self):
    """If image colors cannot be merged into a valid palette, throw error."""
    img = Image.open('testdata/full-image-conflict.png')
    self.process_image(img)
    self.args.error_outfile = self.args.tmppng('error')
    self.assertTrue(self.err.has())
    es = self.err.get()
    expect_errors = ['PaletteTooManySubsets - valid: ' +
                     '30-28-19-14,38-30-16-01\n' +
                     'subsets that can\'t be merged: ' +
                     '[30-0c-0b,31-30-04,34-30-07]']
    actual_errors = ['%s %s' % (type(e).__name__, str(e)) for e in es]
    self.assertEqual(actual_errors, expect_errors)
    expect_list_blocks = [[1, 4], [2, 4], [3, 4]]
    self.assertEqual(es[0].list_blocks, expect_list_blocks)
    renderer = view_renderer.ViewRenderer()
    renderer.create_error_view(self.args.error_outfile, img, es)
    self.assert_file_eq(self.args.error_outfile,
                        'testdata/errors-conflict-palette.png')

  def test_error_background_but_already_filled(self):
    """If background color cannot fit into any guessed palette, throw error."""
    img = Image.open('testdata/full-image.png')
    self.args.bg_color = bg_color_spec.build('19')
    self.process_image(img)
    self.assertTrue(self.err.has())
    es = self.err.get()
    for e in es:
      msg = '{0} {1}'.format(type(e).__name__, e)
      self.assertEqual(msg, ('PaletteTooManySubsets - valid: 38-30-16-01\n' +
                             "subsets that can't be merged: [30-19]"))

  def test_error_palette_no_choice(self):
    """If explicit palette cannot be used for the image, throw error."""
    img = Image.open('testdata/full-image.png')
    palette_text = 'P/30-38-16-01/'
    self.process_image(img, palette_text=palette_text)
    self.assertTrue(self.err.has())
    es = self.err.get()
    for e in es:
      msg = '{0} {1}'.format(type(e).__name__, e)
      self.assertEqual(msg, 'PaletteNoChoiceError at (2y,4x) for 30-19')


if __name__ == '__main__':
  unittest.main()
