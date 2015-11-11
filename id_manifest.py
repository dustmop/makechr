class IdManifest(object):
  """Stores objects, returning monotonically increasing ids for each.

  Stores objects, typically bytearrays, creating hashable keys for each
  element stored. Faster than an OrderedDict because it avoids needing to
  unserialize strings back to bytearrays.
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
      self._elems.append(obj)
    return result

  def at(self, id):
    return self._elems[id]

  def elems(self):
    return self._elems

  def get(self, obj):
    return self._dict.get(obj)
