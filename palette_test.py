import unittest

import errors
from PIL import Image
import palette


class PaletteTests(unittest.TestCase):
  def test_parser(self):
    parser = palette.PaletteParser()
    pal = parser.parse('P/0f-01-02/')
    self.assertEqual(str(pal), 'P/0f-01-02/')
    pal = parser.parse('P/0f-01-02-03/0f-04-05-06/0f-10/')
    self.assertEqual(str(pal), 'P/0f-01-02-03/0f-04-05-06/0f-10/')

  def test_parser_bad_hex(self):
    parser = palette.PaletteParser()
    with self.assertRaises(errors.PaletteParseError) as cm:
      parser.parse('P/0f-01-4g/')
    self.assertEqual(cm.exception.i, 8)
    self.assertTrue('Invalid hex value' in cm.exception.msg)
    self.assertTrue((' ' * 8 + '^') in str(cm.exception))

  def test_parser_unknown_char(self):
    parser = palette.PaletteParser()
    with self.assertRaises(errors.PaletteParseError) as cm:
      parser.parse('P/0f-01-02-03?/')
    self.assertEqual(cm.exception.i, 13)
    self.assertTrue('Expected: "/"' in cm.exception.msg)
    self.assertTrue((' ' * 13 + '^') in str(cm.exception))

  def test_parser_no_ending_slash(self):
    parser = palette.PaletteParser()
    with self.assertRaises(errors.PaletteParseError) as cm:
      parser.parse('P/0f-01-02-03')
    self.assertEqual(cm.exception.i, 13)
    self.assertTrue('Expected: "/"' in cm.exception.msg)
    self.assertTrue((' ' * 13 + '^') in str(cm.exception))


if __name__ == '__main__':
  unittest.main()
