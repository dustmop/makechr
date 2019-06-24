import unittest

import context
import errors, palette


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

  def test_parser_zero_is_valid(self):
    parser = palette.PaletteParser()
    pal = parser.parse('P/0f-00/')
    self.assertEqual(str(pal), 'P/0f-00/')

  def test_bg_color_simple(self):
    pal = palette.Palette()
    pal.set_bg_color(0x0f)
    self.assertEqual(str(pal), 'P//')
    pal.add([0x0f])
    self.assertEqual(str(pal), 'P/0f/')

  def test_bg_color_add_error_missing(self):
    pal = palette.Palette()
    with self.assertRaises(errors.PaletteBackgroundColorMissingError):
      pal.add([0x30, 0x01])

  def test_bg_color_add_error_conflict(self):
    pal = palette.Palette()
    pal.set_bg_color(0x0f)
    with self.assertRaises(errors.PaletteBackgroundColorConflictError):
      pal.add([0x30, 0x01])

  def test_bg_color_add_zero_bg_color_is_ignored(self):
    pal = palette.Palette()
    pal.set_bg_color(0x0f)
    pal.add([0x0f, 0x01, 0x02, 0x03])
    pal.add([0x00, 0x04, 0x05, 0x06])
    self.assertEqual(str(pal), 'P/0f-01-02-03/0f-04-05-06/')

  def test_bg_color_override_old(self):
    pal = palette.Palette()
    pal.set_bg_color(0x0f)
    pal.add([0x0f, 0x01])
    pal.set_bg_color(0x30)
    self.assertEqual(str(pal), 'P/30-01/')


if __name__ == '__main__':
  unittest.main()
