class ChrTile(object):
  def __init__(self):
    self.low = [0] * 8
    self.hi = [0] * 8

  def put_pixel(self, y, x, val):
    """Set the pixel at y,x to have value val.

    y: Y position
    x: X position
    val: A pixel value, 0..3
    """
    low_bit = val & 1
    hi_bit = val >> 1 & 1
    self._assign_bit_low_plane(low_bit, y, x)
    self._assign_bit_hi_plane(hi_bit, y, x)

  def get_pixel(self, y, x):
    """Get the pixel value at y,x."""
    mask = 1 << (7 - x)
    low_bit = 1 if self.low[y] & mask else 0
    hi_bit = 1 if self.hi[y] & mask else 0
    return low_bit + hi_bit * 2

  def set(self, bytes):
    """Assign 16 bytes of data to this tile."""
    self.low = [ord(b) for b in bytes[0:8]]
    self.hi = [ord(b) for b in bytes[8:16]]

  def _assign_bit_low_plane(self, bit, index, offset):
    self.low[index] |= (bit << (7 - offset))

  def _assign_bit_hi_plane(self, bit, index, offset):
    self.hi[index] |= (bit << (7 - offset))

  def write(self, fp):
    """Write chr image to an output stream."""
    fp.write(bytearray(self.low))
    fp.write(bytearray(self.hi))


class ChrPage(object):
  def __init__(self):
    self.tiles = []

  def add(self, tile):
    if self.is_full():
      return None
    ret = self.size()
    self.tiles.append(tile)
    return ret

  def size(self):
    return len(self.tiles)

  def is_full(self):
    return len(self.tiles) >= 0x100

  def get(self, num):
    return self.tiles[num]

  @staticmethod
  def from_binary(bytes):
    make = ChrPage()
    for k in xrange(0x100):
      tile = ChrTile()
      tile.set(bytes[k*0x10:k*0x10+0x10])
      make.add(tile)
    return make

  def save(self, fp):
    for t in self.tiles:
      t.write(fp)
