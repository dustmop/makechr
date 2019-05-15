import general_app_test_util
import unittest

from PIL import Image


class PlatformTests(general_app_test_util.GeneralAppTests):
  def test_gameboy(self):
    """Output an image for the gameboy platform."""
    img = Image.open('testdata/gb-sample.png')
    self.args.platform = 'gameboy'
    self.process_image(img, palette_text='P/30-10-00-0f/')
    self.create_output()
    self.golden_file_prefix = 'gb-sample'
    self.assert_output_result('chr')
    self.assert_not_exist('palette')
    self.assert_output_result('nametable')
    self.assert_not_exist('attribute')


if __name__ == '__main__':
  unittest.main()
