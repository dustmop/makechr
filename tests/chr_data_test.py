import unittest

import context
from makechr import chr_data


class ChrDataTests(unittest.TestCase):
  def test_put_pixel_get_pixel(self):
    tile = chr_data.ChrTile()
    self.assertEqual(tile.get_pixel(3, 4), 0)
    tile.put_pixel(3, 4, 1)
    self.assertEqual(tile.get_pixel(3, 4), 1)

  def test_put_pixel_to_low_hi(self):
    tile = chr_data.ChrTile()
    #  0 1 2 3 4 5 6 7
    #0
    #1     1     1
    #2     1     1
    #3     2     2
    #4
    #5   3         3
    #6     3 3 3 3
    #7
    tile.put_pixel(1, 2, 1)
    tile.put_pixel(1, 5, 1)
    tile.put_pixel(2, 2, 1)
    tile.put_pixel(2, 5, 1)
    tile.put_pixel(3, 2, 2)
    tile.put_pixel(3, 5, 2)
    tile.put_pixel(5, 1, 3)
    tile.put_pixel(5, 6, 3)
    tile.put_pixel(6, 2, 3)
    tile.put_pixel(6, 3, 3)
    tile.put_pixel(6, 4, 3)
    tile.put_pixel(6, 5, 3)
    self.assertEqual(tile.low, [0x00,0x24,0x24,0x00,0x00,0x42,0x3c,0x00])
    self.assertEqual(tile.hi,  [0x00,0x00,0x00,0x24,0x00,0x42,0x3c,0x00])

  def test_set_bytes_to_low_hi(self):
    tile = chr_data.ChrTile()
    tile.set(bytes(bytearray([0,1,2,3,4,5,6,7] + ([0] * 8))))
    self.assertEqual(tile.low, [0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07])
    self.assertEqual(tile.hi,  [0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00])

  def test_set_get_pixel(self):
    tile = chr_data.ChrTile()
    tile.set(bytes(bytearray([0,1,2,3,4,5,6,7] + ([0] * 8))))
    self.assertEqual(tile.get_pixel(4, 5), 1)

  def test_compare(self):
    left = chr_data.ChrTile()
    rite = chr_data.ChrTile()
    left.set(bytes(bytearray([0,1,2,3,4,5,6,7] + ([0] * 8))))
    rite.set(bytes(bytearray(([0] * 8) + [0,1,2,3,4,5,6,7])))
    self.assertTrue(left > rite)
    self.assertTrue(rite < left)
    self.assertTrue(left == left)
    self.assertTrue(rite == rite)

  def test_chr_page(self):
    raw_data = bytes(bytearray(xrange(64)))
    page = chr_data.ChrPage.from_binary(raw_data)
    self.assertEqual(page.size(), 4)
    self.assertFalse(page.is_full())
    tile = page.get(1)
    self.assertEqual(tile.low, list(xrange(16,24)))
    self.assertEqual(tile.hi,  list(xrange(24,32)))
    page.add(tile)
    self.assertEqual(page.size(), 5)
    b = page.to_bytes()
    self.assertEqual(b, raw_data + raw_data[16:32])

  def test_sorted_chr_page(self):
    data = bytes(bytearray(xrange(64)))
    input = data[16:32] + data[48:64] + data[32:48] + data[48:64] + data[0:16]
    spage = chr_data.SortableChrPage.from_binary(input)
    self.assertEqual(spage.size(), 5)
    self.assertEqual(spage.num_idx(), 4)
    self.assertFalse(spage.is_full())
    self.assertEqual(spage.idx, [4,0,2,1])
    self.assertEqual(spage.index(0), 4)
    expect_tile = chr_data.ChrTile()
    expect_tile.set(bytes(bytearray(xrange(0,16))))
    self.assertEqual(spage.get(4), expect_tile)
    self.assertEqual(spage.k_smallest(0), expect_tile)

  def test_sparse_chr_page(self):
    spage = chr_data.SparseChrPage()
    first_tile = chr_data.ChrTile()
    first_tile.set(bytes(bytearray(xrange(0,16))))
    spage.insert(2, first_tile)
    second_tile = chr_data.ChrTile()
    second_tile.set(bytes(bytearray(range(1,17))))
    spage.insert(4, second_tile)
    self.assertEqual(spage.size(), 2)
    self.assertFalse(spage.is_full())
    third_tile = chr_data.ChrTile()
    third_tile.set(bytes(bytearray(range(2,18))))
    spage.add(third_tile)
    fourth_tile = chr_data.ChrTile()
    fourth_tile.set(bytes(bytearray(range(3,19))))
    spage.add(fourth_tile)
    fifth_tile = chr_data.ChrTile()
    fifth_tile.set(bytes(bytearray(range(4,20))))
    spage.add(fifth_tile)
    self.assertEqual(spage.size(), 5)
    self.assertEqual(spage.get(0), third_tile)
    self.assertEqual(spage.get(1), fourth_tile)
    self.assertEqual(spage.get(2), first_tile)
    self.assertEqual(spage.get(3), fifth_tile)
    self.assertEqual(spage.get(4), second_tile)
    expect_bytes = bytearray()
    for t in [third_tile, fourth_tile, first_tile, fifth_tile, second_tile]:
      expect_bytes += t.get_bytes()
    self.assertEqual(spage.to_bytes(), expect_bytes)

  def test_flip(self):
    empty = [0] * 8
    origin = [0,1,2,3,4,5,6,7]
    golden = [0x00,0x80,0x40,0xc0,0x20,0xa0,0x60,0xe0]
    tile = chr_data.ChrTile()
    tile.set(bytes(bytearray(origin + empty)))
    horz = tile.flip('h')
    self.assertEqual(horz.low, golden)
    self.assertEqual(horz.hi, empty)
    vert = tile.flip('v')
    self.assertEqual(vert.low, origin[::-1])
    self.assertEqual(vert.hi, empty)
    spin = tile.flip('vh')
    self.assertEqual(spin.low, golden[::-1])
    self.assertEqual(spin.hi, empty)


if __name__ == '__main__':
  unittest.main()
