import errors


class ChrTile(object):
  """Single chr tile, 16 bytes, stored in a planar format."""

  def __init__(self):
    self.low = [0] * 8
    self.hi = [0] * 8

  def get_bytes(self):
    """Get the bytes representing the chr."""
    return bytearray(self.low + self.hi)

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

  def vertical_pixel_display(self):
    def vertical_plane(plane):
      make = [0] * 8
      for i,b in enumerate(plane):
        for j in xrange(8):
          make[j] |= (((b >> (7 - j)) & 1) << (i))
      return make
    self.low = vertical_plane(self.low)
    self.hi = vertical_plane(self.hi)

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

  def __str__(self):
    return '<ChrTile %r>' % bytes(self.get_bytes())

  def __repr__(self):
    return self.__str__()


class ChrPage(object):
  """One page of chr tiles, 0x1000 bytes, enough for 256 tiles."""

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

  def _enum_tiles(self):
    return enumerate(self.tiles)

  def to_bytes(self):
    bytes = bytearray(len(self.tiles) * 0x10)
    for k,tile in self._enum_tiles():
      bytes[k*0x10+0x00:k*0x10+0x08] = tile.low
      bytes[k*0x10+0x08:k*0x10+0x10] = tile.hi
    return bytes

  def to_bytes_select_plane(self, selection):
    bytes = bytearray(len(self.tiles) * 0x08)
    if selection == 0:
      for k,tile in self._enum_tiles():
        bytes[k*0x08+0x00:k*0x08+0x08] = tile.low
    elif selection == 1:
      for k,tile in self._enum_tiles():
        bytes[k*0x08+0x00:k*0x08+0x08] = tile.hi
    return bytes

  def vertical_pixel_display(self):
    for tile in self.tiles:
      tile.vertical_pixel_display()


class ChrBank(ChrPage):
  """Two pages of chr tiles, 0x2000 bytes, enough for 2*256 tiles."""

  def add(self, tile):
    return ChrPage.add(self, tile) % 0x100

  def is_full(self):
    return len(self.tiles) >= 0x200

  @staticmethod
  def from_binary(bytes):
    make = ChrBank()
    for k in xrange(len(bytes) / 0x10):
      tile = ChrTile()
      tile.set(bytes[k*0x10:k*0x10+0x10])
      make.add(tile)
    return make


class SortableChrPage(ChrPage):
  """ChrPage with a sorted view, easier to merge or compare."""

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


class SparseChrPage(ChrPage):
  """ChrPage stored as a sparse array, can insert into arbitrary indexes."""

  def __init__(self):
    ChrPage.__init__(self)
    self.lower = 0
    self.tiles = {}

  def add(self, tile):
    if self.is_full():
      raise errors.ChrPageFull()
    ret = self.lower
    self.tiles[self.lower] = tile
    self._adjust_lower()
    return ret

  def insert(self, pos, tile):
    self.tiles[pos] = tile
    self._adjust_lower()
    return pos

  def _adjust_lower(self):
    while self.lower in self.tiles:
      self.lower += 1

  def _enum_tiles(self):
    return self.tiles.items()


class VertTilePair(object):
  """A pair of 8x8 tiles, vertically oriented."""

  def __init__(self, upper, lower):
    self.upper = upper
    self.lower = lower

  def get_bytes(self):
    bytes = self.upper.low + self.upper.hi + self.lower.low + self.lower.hi
    return bytearray(bytes)

  def flip(self, direction):
    if direction == 'h':
      return VertTilePair(self.upper.flip('h'), self.lower.flip('h'))
    elif direction == 'v':
      return VertTilePair(self.lower.flip('v'), self.upper.flip('v'))
    elif direction == 'vh':
      return VertTilePair(self.lower.flip('vh'), self.upper.flip('vh'))
    raise RuntimeError('Unknown flip direction "%s"' % direction)

  def __str__(self):
    return '<VertTilePair ' + bytes(self.get_bytes()) + '>'
