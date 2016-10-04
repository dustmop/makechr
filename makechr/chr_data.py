import errors


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

  def is_empty(self):
    return all(e == 0 for e in self.low) and all(e == 0 for e in self.hi)

  def flip(self, direction):
    make = ChrTile()
    make.low = self.low
    make.hi = self.hi
    if direction == 'v' or direction == 'vh':
      make.low = make.low[::-1]
      make.hi = make.hi[::-1]
    if direction == 'h' or direction == 'vh':
      make.low = [self._reverse_bits(b) for b in make.low]
      make.hi = [self._reverse_bits(b) for b in make.hi]
    return make

  def _assign_bit_low_plane(self, bit, index, offset):
    self.low[index] |= (bit << (7 - offset))

  def _assign_bit_hi_plane(self, bit, index, offset):
    self.hi[index] |= (bit << (7 - offset))

  def _reverse_bits(self, b):
    return int('{:08b}'.format(b)[::-1], 2)

  def __cmp__(self, other):
    if self.low < other.low:
      return -1
    elif self.low > other.low:
      return 1
    elif self.hi < other.hi:
      return -1
    elif self.hi > other.hi:
      return 1
    return 0

  def __repr__(self):
    return '%s' % (self.low + self.hi)


class ChrPage(object):
  def __init__(self):
    self.tiles = []

  def add(self, tile):
    if self.is_full():
      raise errors.ChrPageFull()
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
    for k in xrange(len(bytes) / 0x10):
      tile = ChrTile()
      tile.set(bytes[k*0x10:k*0x10+0x10])
      make.add(tile)
    return make

  def to_bytes(self):
    bytes = bytearray(len(self.tiles) * 0x10)
    for k,tile in enumerate(self.tiles):
      bytes[k*0x10+0x00:k*0x10+0x08] = tile.low
      bytes[k*0x10+0x08:k*0x10+0x10] = tile.hi
    return bytes


class SortableChrPage(ChrPage):
  def __init__(self):
    ChrPage.__init__(self)
    self.idx = []

  def add(self, tile):
    r = ChrPage.add(self, tile)
    self._assign_idx()
    return r

  def clone(self):
    make = SortableChrPage()
    make.tiles = self.tiles
    make.idx = self.idx
    return make

  def index(self, k):
    return self.idx[k]

  def k_smallest(self, k):
    return self.tiles[self.idx[k]]

  def num_idx(self):
    return len(self.idx)

  @staticmethod
  def from_binary(bytes):
    inner = ChrPage.from_binary(bytes)
    make = SortableChrPage()
    make.tiles = inner.tiles
    make._assign_idx()
    return make

  def _assign_idx(self):
    es = [(e.low + e.hi,i) for (i,e) in enumerate(self.tiles)]
    es.sort(key=lambda x:x[0])
    self.idx = []
    last = None
    for e,i in es:
      if e == last:
        continue
      last = e
      self.idx.append(i)

