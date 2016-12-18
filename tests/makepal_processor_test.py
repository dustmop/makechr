import general_app_test_util
import unittest

import context
from makechr import makepal_processor

from PIL import Image


class MakepalProcessorTests(general_app_test_util.GeneralAppTests):
  def process_image(self, img, only_binary=False, expect_fail=False):
    if not only_binary:
      self.args.output = self.args.tmpfile('pal.o')
    else:
      self.args.output = self.args.tmpfile('pal.dat')
    self.processor = makepal_processor.MakepalProcessor()
    self.processor.process_image(img, self.args)
    if self.processor.err().has():
      if expect_fail:
        self.err = self.processor.err()
        return
    self.processor.create_output(self.args.output)

  def test_simple_palette(self):
    img = Image.open('testdata/simple_palette.png')
    self.args.makepal = True
    self.process_image(img)
    self.golden_file_prefix = 'simple_palette'
    self.assert_file_eq(self.args.output, 'testdata/simple_palette.o')

  def test_simple_palette_only_binary(self):
    img = Image.open('testdata/simple_palette.png')
    self.args.makepal = True
    self.process_image(img, only_binary=True)
    self.golden_file_prefix = 'simple_palette'
    self.assert_file_eq(self.args.output, 'testdata/simple_palette.dat')

  def test_partial_palette(self):
    img = Image.open('testdata/partial_palette.png')
    self.args.makepal = True
    self.process_image(img)
    self.golden_file_prefix = 'partial_palette'
    self.assert_file_eq(self.args.output, 'testdata/partial_palette.o')

  def test_bigger_palette(self):
    img = Image.open('testdata/bigger_palette.png')
    self.args.makepal = True
    self.process_image(img)
    self.golden_file_prefix = 'bigger_palette'
    self.assert_file_eq(self.args.output, 'testdata/bigger_palette.o')

  def test_error_border_not_found(self):
    img = Image.open('testdata/error_border_not_found.png')
    self.args.makepal = True
    self.process_image(img, expect_fail=True)
    self.assertTrue(self.err.has())
    es = self.err.get()
    self.assertEqual(len(es), 1)
    msg = '{0} {1}'.format(type(es[0]).__name__, es[0])
    self.assertEqual(msg, 'MakepalBorderNotFound ')

  def test_error_invalid_format(self):
    img = Image.open('testdata/error_invalid_format.png')
    self.args.makepal = True
    self.process_image(img, expect_fail=True)
    self.assertTrue(self.err.has())
    es = self.err.get()
    self.assertEqual(len(es), 1)
    msg = '{0} {1}'.format(type(es[0]).__name__, es[0])
    self.assertEqual(msg, 'MakepalInvalidFormat ')


if __name__ == '__main__':
  unittest.main()
