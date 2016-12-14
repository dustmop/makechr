import general_app_test_util
import unittest

import context
from makechr import makepal_processor

from PIL import Image


class MakepalProcessorTests(general_app_test_util.GeneralAppTests):
  def process_image(self, img, only_binary=False):
    if not only_binary:
      self.args.output = self.args.tmpfile('pal.o')
    else:
      self.args.output = self.args.tmpfile('pal.dat')
    self.processor = makepal_processor.MakepalProcessor()
    self.processor.process_image(img, self.args)
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

if __name__ == '__main__':
  unittest.main()
