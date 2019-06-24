import general_app_test_util
import os
import tempfile
import unittest

from PIL import Image

import context
import decompose_sprites_processor


class DecomposeSpritesProcessorTests(general_app_test_util.GeneralAppTests):
  def setUp(self):
    self.processor = decompose_sprites_processor.DecomposeSpritesProcessor()
    self.ppu_memory = self.processor._ppu_memory
    self.ppu_memory.allocate_num_pages(1)
    general_app_test_util.GeneralAppTests.setUp(self)
    self.args.is_sprite = True

  def test_decompose_geometric_outlines(self):
    tmpdir = tempfile.mkdtemp()
    img = Image.open('testdata/geometric-outlines.png')
    anon_view_actual = os.path.join(tmpdir, 'geometric-anon-view.png')
    steps_view_actual = os.path.join(tmpdir, 'geometric-steps-view.png')
    flags = {'anon_view': anon_view_actual,
             'steps_view': steps_view_actual}
    self.processor.process_image(img, None, 0x31, 0x30, flags)
    self.assert_file_eq(anon_view_actual, 'testdata/geometric-anon-view.png')
    self.assert_file_eq(steps_view_actual, 'testdata/geometric-steps-view.png')

  def test_decompose_sprites_and_palettes(self):
    tmpdir = tempfile.mkdtemp()
    img = Image.open('testdata/decompose-colors.png')
    steps_view_actual = os.path.join(tmpdir, 'decompose-steps-view.png')
    flags = {'steps_view': steps_view_actual}
    self.processor.process_image(img, None, 0x31, 0x30, flags)
    self.assert_file_eq(steps_view_actual,
                        'testdata/decompose-colors-steps-view.png')
    self.create_output()
    self.golden_file_prefix = 'decompose-colors'
    self.assert_output_result('chr')
    self.assert_output_result('palette')
    self.assert_output_result_json('sprite_picdata')


if __name__ == '__main__':
  unittest.main()
