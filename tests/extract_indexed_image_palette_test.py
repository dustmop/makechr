import unittest

from PIL import Image

import context
from makechr import extract_indexed_image_palette, image_processor


class ExtractIndexedImagePaletteTests(unittest.TestCase):
  def test_extract(self):
    """Extract a palette from a 16-color indexed image."""
    img = Image.open('testdata/full-image-16color.png')
    processor = image_processor.ImageProcessor()
    extractor = extract_indexed_image_palette.ExtractIndexedImagePalette(
        processor)
    pal = extractor.extract_palette(img.palette, img.format)
    self.assertEqual(str(pal),
                     'P/16-30-01-0f/16-30-01-38/16-30-19-28/16-23-23-28/')


if __name__ == '__main__':
  unittest.main()
