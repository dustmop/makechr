import collections


class IdManifest(object):
  """Stores bytearrays, returning monotonically increasing ids for each.

  Stores bytearrays creating hashable keys for each element stored. Faster
  than an OrderedDict because it avoids needing to unserialize strings back
  to bytearrays.
  """

  def __init__(self):
    self._dict = {}
    self._elems = []

  def __len__(self):
    return len(self._dict)

  def id(self, obj):
    key = str(obj)
    if key in self._dict:
      result = self._dict[key]
    else:
      result = len(self._dict)
      self._dict[key] = result
      self._elems.append([e for e in obj if e != 0xff])
    return result

  def at(self, id):
    return self._elems[id]

  def elems(self):
    return self._elems

  def get(self, obj):
    return self._dict.get(obj)


class CountingIdManifest(IdManifest):
  """Count how many objects exist that only consist of a single byte."""

  def __init__(self):
    self._count = collections.defaultdict(int)
    IdManifest.__init__(self)

  def id(self, obj):
    if obj[1:4] == bytearray('\xff\xff\xff'):
      self._count[obj[0]] += 1
    return IdManifest.id(self, obj)

  def counts(self):
    return self._count.items()
