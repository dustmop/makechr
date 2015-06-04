class ChrTile(object):
  def __init__(self):
    self.low = [0] * 8
    self.hi = [0] * 8

  def set(self, y, x, val):
    """Set the pixel at y,x to have value val.

    y: Y position
    x: X position
    val: A pixel value, 0..3
    """
    low_bit = val & 1
    hi_bit = val >> 1 & 1
    self.set_low(low_bit, y, x)
    self.set_hi(hi_bit, y, x)

  def get(self, y, x):
    """Get the pixel value at y,x."""
    mask = 1 << (7 - x)
    low_bit = 1 if self.low[y] & mask else 0
    hi_bit = 1 if self.hi[y] & mask else 0
    return low_bit + hi_bit * 2

  def set_low(self, bit, index, offset):
    self.low[index] |= (bit << (7 - offset))

  def set_hi(self, bit, index, offset):
    self.hi[index] |= (bit << (7 - offset))

  def write(self, fp):
    """Write chr image to an output stream."""
    for b in self.low:
      fp.write(chr(b))
    for b in self.hi:
      fp.write(chr(b))
