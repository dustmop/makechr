class ChrTile(object):
  def __init__(self):
    self.low = [0] * 8
    self.hi = [0] * 8

  def set(self, val, offset, index):
    low_bit = val & 1
    hi_bit = val >> 1 & 1
    self.set_low(low_bit, offset, index)

  def set_low(self, bit, offset, index):
    self.low[index] |= (bit << offset)

  def set_hi(self, bit, offset, index):
    self.hi[index] |= (bit << offset)
