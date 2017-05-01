import unittest

from PIL import Image

import context
from makechr import extract_indexed_image_palette, image_processor, \
  wrapped_image_palette


class MockWrappedImagePalette(wrapped_image_palette.WrappedImagePalette):
  def __init__(self, bytes, format):
    wrapped_image_palette.WrappedImagePalette.__init__(self)
    self.palette = [chr(b) for b in bytes]
    self.format = format
    self._build()


class ExtractIndexedImagePaletteTests(unittest.TestCase):
  def imgpal(self, img):
    return wrapped_image_palette.WrappedImagePalette.from_image(img)

  def test_extract_16color_png(self):
    """Extract a palette from a 16-color indexed png."""
    img = Image.open('testdata/full-image-16color.png')
    processor = image_processor.ImageProcessor()
    extractor = extract_indexed_image_palette.ExtractIndexedImagePalette(
        processor)
    pal = extractor.extract_palette(self.imgpal(img))
    self.assertEqual(str(pal),
                     'P/16-30-01-0f/16-30-01-38/16-30-19-28/16-23-23-28/')

  def test_extract_16color_bmp(self):
    """Extract a palette from a 16-color indexed bmp."""
    img = Image.open('testdata/full-image-16color.bmp')
    processor = image_processor.ImageProcessor()
    extractor = extract_indexed_image_palette.ExtractIndexedImagePalette(
        processor)
    pal = extractor.extract_palette(self.imgpal(img))
    self.assertEqual(str(pal),
                     'P/16-30-01-0f/16-30-01-38/16-30-19-28/16-23-23-28/')

  def test_extract_16overuse_png(self):
    """Extract a palette from a 16-color indexed png with 8bpp."""
    img = Image.open('testdata/full-image-16color-overuse.png')
    processor = image_processor.ImageProcessor()
    extractor = extract_indexed_image_palette.ExtractIndexedImagePalette(
        processor)
    pal = extractor.extract_palette(self.imgpal(img))
    self.assertEqual(str(pal),
                     'P/16-30-01-0f/16-30-01-38/16-30-19-28/16-23-23-28/')

  def test_extract_16overuse_bmp(self):
    """Extract a palette from a 16-color indexed bmp with 8bpp."""
    img = Image.open('testdata/full-image-16color-overuse.bmp')
    processor = image_processor.ImageProcessor()
    extractor = extract_indexed_image_palette.ExtractIndexedImagePalette(
        processor)
    pal = extractor.extract_palette(self.imgpal(img))
    self.assertEqual(str(pal),
                     'P/16-30-01-0f/16-30-01-38/16-30-19-28/16-23-23-28/')

  def test_wrapped_48_bytes_png(self):
    processor = image_processor.ImageProcessor()
    extractor = extract_indexed_image_palette.ExtractIndexedImagePalette(
        processor)
    bytes = [252,  56,   0, 255, 255, 255,   0,   0, 252,   0,   0,   0,
             252,  56,   0, 255, 255, 255,   0,   0, 252, 252, 216, 132,
             252,  56,   0, 255, 255, 255,   0, 184,   0, 248, 184,   0,
             252,  56,   0, 173, 145, 249, 173, 145, 249, 248, 184,   0]
    pal = extractor.extract_palette(MockWrappedImagePalette(bytes, 'PNG'))
    self.assertEqual(str(pal),
                     'P/16-30-01-0f/16-30-01-38/16-30-19-28/16-23-23-28/')

  def test_wrapped_48_bytes_bmp(self):
    processor = image_processor.ImageProcessor()
    extractor = extract_indexed_image_palette.ExtractIndexedImagePalette(
        processor)
    bytes = [  0,  56, 252, 255, 255, 255, 252,   0,   0,   0,   0,   0,
               0,  56, 252, 255, 255, 255, 252,   0,   0, 132, 216, 252,
               0,  56, 252, 255, 255, 255,   0, 184,   0,   0, 184, 248,
               0,  56, 252, 249, 145, 173, 249, 145, 173,   0, 184, 248]
    pal = extractor.extract_palette(MockWrappedImagePalette(bytes, 'BMP'))
    self.assertEqual(str(pal),
                     'P/16-30-01-0f/16-30-01-38/16-30-19-28/16-23-23-28/')

  def test_wrapped_64_bytes_png(self):
    processor = image_processor.ImageProcessor()
    extractor = extract_indexed_image_palette.ExtractIndexedImagePalette(
        processor)
    bytes = [252, 56,  0, 0,255,255,255, 1,  0,  0,252, 2,  0,  0,  0, 3,
             252, 56,  0, 4,255,255,255, 5,  0,  0,252, 6,252,216,132, 8,
             252, 56,  0, 8,255,255,255, 9,  0,184,  0,10,248,184,  0,11,
             252, 56,  0,12,173,145,249,13,173,145,249,14,248,184,  0,15]
    pal = extractor.extract_palette(MockWrappedImagePalette(bytes, 'PNG'))
    self.assertEqual(str(pal),
                     'P/16-30-01-0f/16-30-01-38/16-30-19-28/16-23-23-28/')

  def test_wrapped_64_bytes_bmp(self):
    processor = image_processor.ImageProcessor()
    extractor = extract_indexed_image_palette.ExtractIndexedImagePalette(
        processor)
    bytes = [  0, 56,252, 0,255,255,255, 1,252,  0,  0, 2,  0,  0,  0, 3,
               0, 56,252, 4,255,255,255, 5,252,  0,  0, 6,132,216,252, 8,
               0, 56,252, 8,255,255,255, 9,  0,184,  0,10,  0,184,248,11,
               0, 56,252,12,249,145,173,13,249,145,173,14,  0,184,248,15]
    pal = extractor.extract_palette(MockWrappedImagePalette(bytes, 'BMP'))
    self.assertEqual(str(pal),
                     'P/16-30-01-0f/16-30-01-38/16-30-19-28/16-23-23-28/')


if __name__ == '__main__':
  unittest.main()
