import unittest

import context
from makechr import span_list_delta
from makechr.data import Span


class SpanListDeltaTests(unittest.TestCase):
  def make_spans(self, elems):
    return [Span(left, right) for (left, right) in elems]

  def assertNull(self, delta, keys):
    for k in keys:
      if k in delta:
        self.fail('key=%s: %r not null' % (k, delta[k]))

  def test_include_one(self):
    older = []
    newer = self.make_spans([(1,4)])
    delta = span_list_delta.get_delta(newer, older)
    self.assertEqual(delta['include'], [Span(1,4)])
    self.assertNull(delta, ['exclude', 'same', 'merge', 'split', 'diff'])

  def test_exclude_one(self):
    older = self.make_spans([(7,9)])
    newer = []
    delta = span_list_delta.get_delta(newer, older)
    self.assertEqual(delta['exclude'], [Span(7,9)])
    self.assertNull(delta, ['include', 'same', 'merge', 'split', 'diff'])

  def test_same_one(self):
    older = self.make_spans([(1,4)])
    newer = self.make_spans([(1,4)])
    delta = span_list_delta.get_delta(newer, older)
    self.assertEqual(delta['same'],    [Span(1,4)])
    self.assertNull(delta, ['include', 'exclude', 'merge', 'split', 'diff'])

  def test_include_to_left(self):
    older = self.make_spans([       (7,9)])
    newer = self.make_spans([(1,4), (7,9)])
    delta = span_list_delta.get_delta(newer, older)
    self.assertEqual(delta['include'], [Span(1,4)])
    self.assertEqual(delta['same'],    [Span(7,9)])
    self.assertNull(delta, ['exclude', 'merge', 'split', 'diff'])

  def test_include_to_right(self):
    older = self.make_spans([(1,4)])
    newer = self.make_spans([(1,4), (7,9)])
    delta = span_list_delta.get_delta(newer, older)
    self.assertEqual(delta['include'], [Span(7,9)])
    self.assertEqual(delta['same'],    [Span(1,4)])
    self.assertNull(delta, ['exclude', 'merge', 'split', 'diff'])

  def test_exclude_to_right(self):
    older = self.make_spans([(1,4), (7,9)])
    newer = self.make_spans([(1,4)])
    delta = span_list_delta.get_delta(newer, older)
    self.assertEqual(delta['exclude'], [Span(7,9)])
    self.assertEqual(delta['same'],    [Span(1,4)])
    self.assertNull(delta, ['include', 'merge', 'split', 'diff'])

  def test_exclude_to_left(self):
    older = self.make_spans([(1,4), (7,9)])
    newer = self.make_spans([       (7,9)])
    delta = span_list_delta.get_delta(newer, older)
    self.assertEqual(delta['exclude'], [Span(1,4)])
    self.assertEqual(delta['same'],    [Span(7,9)])
    self.assertNull(delta, ['include', 'merge', 'split', 'diff'])

  def test_include_between(self):
    older = self.make_spans([(1,4),(7,9)])
    newer = self.make_spans([(5,6)])
    delta = span_list_delta.get_delta(newer, older)
    self.assertEqual(delta['include'], [Span(5,6)])
    self.assertEqual(delta['exclude'], [Span(1,4), Span(7,9)])
    self.assertNull(delta, ['same', 'merge', 'split', 'diff'])

  def test_exclude_between(self):
    older = self.make_spans([(5,6)])
    newer = self.make_spans([(1,4),(7,9)])
    delta = span_list_delta.get_delta(newer, older)
    self.assertEqual(delta['include'], [Span(1,4), Span(7,9)])
    self.assertEqual(delta['exclude'], [Span(5,6)])
    self.assertNull(delta, ['same', 'merge', 'split', 'diff'])

  def test_overlap_on_left(self):
    older = self.make_spans([(7,9)])
    newer = self.make_spans([(5,8)])
    delta = span_list_delta.get_delta(newer, older)
    self.assertEqual(delta['merge'], [{'new': [Span(5,8)],
                                       'old': [Span(7,9)]}])
    self.assertNull(delta, ['include', 'exclude', 'same', 'split', 'diff'])

  def test_overlap_on_right(self):
    older = self.make_spans([(7,9)])
    newer = self.make_spans([(8,11)])
    delta = span_list_delta.get_delta(newer, older)
    self.assertEqual(delta['merge'], [{'new': [Span(8,11)],
                                       'old': [Span(7,9)]}])
    self.assertNull(delta, ['include', 'exclude', 'same', 'split', 'diff'])

  def test_overlap_multiple_new(self):
    older = self.make_spans([(7,16)])
    newer = self.make_spans([(1,4),(5,8),(10,12),(14,19),(24,26)])
    delta = span_list_delta.get_delta(newer, older)
    self.assertEqual(delta['split'], [{'new':
                                      [Span(5,8), Span(10,12), Span(14,19)],
                                      'old': [Span(7,16)]}])
    self.assertEqual(delta['include'], [Span(1,4), Span(24,26)])
    self.assertNull(delta, ['exclude', 'same', 'merge', 'diff'])

  def test_overlap_multiple_old(self):
    older = self.make_spans([(1,4),(5,8),(10,12),(14,19),(24,26)])
    newer = self.make_spans([(7,16)])
    delta = span_list_delta.get_delta(newer, older)
    self.assertEqual(delta['merge'], [{'new': [Span(7,16)],
                                       'old':
                                      [Span(5,8), Span(10,12), Span(14,19)]}])
    self.assertEqual(delta['exclude'], [Span(1,4), Span(24,26)])
    self.assertNull(delta, ['include', 'same', 'split', 'diff'])

  def test_change_first_then_same(self):
    older = self.make_spans([(54,70),(103,111),(144,160)])
    newer = self.make_spans([(54,62),(103,111),(144,160)])
    delta = span_list_delta.get_delta(newer, older)
    self.assertEqual(delta['merge'], [{'new': [Span(54,62)],
                                       'old': [Span(54,70)]}])
    self.assertEqual(delta['same'], [Span(103,111), Span(144,160)])
    self.assertNull(delta, ['include', 'exclude', 'split', 'diff'])

  def test_change_middle_others_same(self):
    older = self.make_spans([(54,62),(103,111),(144,160)])
    newer = self.make_spans([(54,62),(103,117),(144,160)])
    delta = span_list_delta.get_delta(newer, older)
    self.assertEqual(delta['merge'], [{'new': [Span(103,117)],
                                       'old': [Span(103,111)]}])
    self.assertEqual(delta['same'], [Span(54,62), Span(144,160)])
    self.assertNull(delta, ['include', 'exclude', 'split', 'diff'])

  def test_two_merges(self):
    older = self.make_spans([(61,69),(76,84),(92,100),(107,115)])
    newer = self.make_spans([(64,84),(92,112)])
    delta = span_list_delta.get_delta(newer, older)
    self.assertEqual(delta['merge'], [{'new': [Span(64,84)],
                                       'old': [Span(61,69),Span(76,84)]},
                                      {'new': [Span(92,112)],
                                       'old': [Span(92,100),Span(107,115)]}])
    self.assertNull(delta, ['include', 'exclude', 'same', 'split', 'diff'])


if __name__ == '__main__':
  unittest.main()
