class IdManifest(object):
  def __init__(self):
    self._dict = {}
    self._elems = []

  def id(self, obj):
    key = str(obj)
    if key in self._dict:
      result = self._dict[key]
    else:
      result = len(self._dict)
      self._dict[key] = result
      self._elems.append(obj)
    return result

  def get(self, id):
    return self._elems[id]

  def elems(self):
    return self._elems

  def size(self):
    return len(self._dict)
