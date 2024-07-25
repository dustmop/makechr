class NumRange(object):
  def __init__(self, p0, p1):
    if p0 >= p1:
      raise RuntimeError('Invalid values for range: %d, %d' % (p0, p1))
    self.p0 = p0
    self.p1 = p1

  def __eq__(self, other):
    if not isinstance(other, NumRange):
      return False
    return self.p0 == other.p0 and self.p1 == other.p1

  def __str__(self):
    return '#<Range p0=%s p1=%s>' % (self.p0, self.p1)

  def __repr__(self):
    return self.__str__()

  def intersect(self, other):
    # Exactly the same.
    if self == other:
      return self
    # This matches the other exactly at its left-most point
    if self.p0 == other.p1:
      return self.p0
    # This matches the other exactly at its right-most point
    if self.p1 == other.p0:
      return self.p1
    if self.p0 > other.p0:
      # case 0 : this is fully right of other
      if self.p0 > other.p1:
        return None
      # case 1 :
      if self.p0 < other.p1 and self.p1 > other.p1:
        return NumRange(self.p0, other.p1)
      # case 2 : this is within other
      else:
        return NumRange(self.p0, self.p1)
    else:
      # case 3 : other is within this
      if self.p1 > other.p1:
        return NumRange(other.p0, other.p1)
      # case 4 :
      if self.p1 > other.p0 and self.p1 <= other.p1:
        return NumRange(other.p0, self.p1)
      # case 5 : this is fully left of other
      else:
        return None

  def union_if_match(self, other):
    # Exactly the same.
    if self == other:
      return self
    # This matches the other exactly at its left-most point
    if self.p0 == other.p1:
      return NumRange(other.p0, self.p1)
    # This matches the other exactly at its right-most point
    if self.p1 == other.p0:
      return NumRange(self.p0, other.p1)
    if self.p0 > other.p0:
      # case 0 : this is fully right of other
      #           <      >
      # <      >
      if self.p0 > other.p1:
        return None
      # case 1 :
      #    <      >
      # <      >
      if self.p0 < other.p1 and self.p1 > other.p1:
        return NumRange(other.p0, self.p1)
      # case 2 : this is within other
      #    <      >
      # <            >
      else:
        return NumRange(other.p0, other.p1)
    else:
      # case 3 : other is within this
      #    <      >
      #      <  >
      if self.p1 > other.p1:
        return NumRange(self.p0, self.p1)
      # case 4 :
      #    <      >
      #      <      >
      if self.p1 > other.p0 and self.p1 <= other.p1:
        return NumRange(self.p0, other.p1)
      # case 5 : this is fully left of other
      #    <      >
      #             <      >
      else:
        return None

  def less_than(self, other):
    return self.p1 < other.p0

  def greater_than(self, other):
    return self.p0 > other.p1

  def contains(self, other):
    return self.p0 <= other.p0 and self.p1 >= other.p1


class MultiRange(object):
  def __init__(self, arrays=[]):
    self.rs = []
    for a in arrays:
      self.rs.append(NumRange(a[0], a[1]))

  def __eq__(self, other):
    if isinstance(other, NumRange) and len(self.rs) == 1:
      return self.rs[0] == other
    if not isinstance(other, MultiRange):
      return False
    return self.rs == other.rs

  def __str__(self):
    accum = ''
    for r in self.rs:
      if accum:
        accum += ' '
      accum += str(r)
    return '#<MultiRange %s>' % accum

  def __repr__(self):
    return self.__str__()

  def add(self, new):
    i = 0
    while i < len(self.rs):
      r = self.rs[i]
      if new.less_than(r):
        self.rs = self.rs[:i] + [new] + self.rs[i:]
        return self
      c = r.union_if_match(new)
      if c:
        new = c
        self.rs = self.rs[:i] + self.rs[i + 1:]
        continue
      i += 1
    self.rs.append(new)
    return self

  def subtract_from(self, entire):
    result = []
    start = entire.p0
    for r in self.rs:
      end = r.p0
      if end > start:
        result.append([start, end])
      start = r.p1
    end = entire.p1
    if end > start:
      result.append([start, end])
    return MultiRange(result)

  def to_single_range(self):
    if len(self.rs) == 0:
      return None
    if len(self.rs) != 1:
      raise RuntimeError('Error: %s is not a single range' % self)
    return self.rs[0]

  def fully_overlap(self, other):
    for r in self.rs:
      if r.contains(other):
        return True
    return False
