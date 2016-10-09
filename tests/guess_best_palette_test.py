import unittest

import context
from makechr import guess_best_palette


class GuessBestPaletteTests(unittest.TestCase):
  def setUp(self):
    self.guesser = guess_best_palette.GuessBestPalette()

  def test_uniq_color_sets(self):
    # Color manifest uses bytearray.
    color_element_list = []
    color_element_list.append(bytearray('\x03\x04\x05'))
    color_element_list.append(bytearray('\x05\x06'))
    color_element_list.append(bytearray('\x01\x02\x03'))
    color_element_list.append(bytearray('\x03\x02\x01'))
    color_element_list.append(bytearray('\x05\x06\x07'))
    uniq_sets = self.guesser.get_uniq_color_sets(color_element_list)
    self.assertEquals(uniq_sets, [[3, 2, 1], [5, 4, 3], [6, 5], [7, 6, 5]])
    # Block color manifest uses sets.
    color_element_list = []
    color_element_list.append(set([3, 4, 5]))
    color_element_list.append(set([5, 6]))
    color_element_list.append(set([1, 2, 3]))
    color_element_list.append(set([3, 2, 1]))
    color_element_list.append(set([5, 6, 7]))
    uniq_sets = self.guesser.get_uniq_color_sets(color_element_list)
    self.assertEquals(uniq_sets, [[3, 2, 1], [5, 4, 3], [6, 5], [7, 6, 5]])

  def test_minimal_colors(self):
    uniq_sets = [[3, 2, 1], [5, 4, 3], [6, 5], [7, 6, 5]]
    expected = [[3, 2, 1], [5, 4, 3], [7, 6, 5]]
    self.assertEquals(self.guesser.get_minimal_colors(uniq_sets), expected)

  def test_merged_color_possibilities(self):
    # TODO: These test cases show that guesser's behavior is hard to describe,
    # and doesn't act correctly in certain cases. In particular, it should
    # enumerate all possibilities that exist, and be better at determining the
    # background color.
    minimal_colors = [[3, 2, 1], [5, 4, 3], [7, 6, 5]]
    actual = self.guesser.get_merged_color_possibilities(minimal_colors)
    expected = [[5, [set([5, 6, 7]), set([3, 4, 5]), set([1, 2, 3])]]]
    self.assertEquals(actual, expected)

    minimal_colors = [[3, 2, 1, 0], [5, 4, 3], [7, 6, 5]]
    actual = self.guesser.get_merged_color_possibilities(minimal_colors)
    expected = [[0, [[3, 2, 1, 0], set([5, 6, 7]), set([3, 4, 5])]]]
    self.assertEquals(actual, expected)

    minimal_colors = [[3, 2, 1, 0], [5, 4, 3, 0], [7, 6, 5]]
    actual = self.guesser.get_merged_color_possibilities(minimal_colors)
    expected = [[0, [[3, 2, 1, 0], [5, 4, 3, 0], set([5, 6, 7])]]]
    self.assertEquals(actual, expected)

    minimal_colors = [[5, 2, 1, 0], [5, 4, 3, 0], [7, 6, 5]]
    actual = self.guesser.get_merged_color_possibilities(minimal_colors)
    expected = [[5, [[5, 2, 1, 0], [5, 4, 3, 0], set([5, 6, 7])]]]
    self.assertEquals(actual, expected)

    minimal_colors = [[5, 2, 1, 0], [5, 4, 3, 0], [6, 5, 0]]
    actual = self.guesser.get_merged_color_possibilities(minimal_colors)
    expected = [[0, [[5, 2, 1, 0], [5, 4, 3, 0], set([0, 5, 6])]]]
    self.assertEquals(actual, expected)

    minimal_colors = [[5, 2, 1, 0], [5, 4, 3, 0], [7, 6, 5, 0]]
    actual = self.guesser.get_merged_color_possibilities(minimal_colors)
    expected = [[0, [[5, 2, 1, 0], [5, 4, 3, 0], [7, 6, 5, 0]]]]
    self.assertEquals(actual, expected)


if __name__ == '__main__':
  unittest.main()
