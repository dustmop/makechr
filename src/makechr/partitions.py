def partitions(s):
  def partitions_rec(s):
    if not s:
      yield []
      return
    for i in range(2**len(s)//2):
      parts = [set(), set()]
      for item in s:
        parts[i&1].add(item)
        i >>= 1
      for b in partitions_rec(parts[1]):
        yield [parts[0]]+b
  if isinstance(s, int):
    return partitions_rec(range(s))
  else:
    return partitions_rec(s)
