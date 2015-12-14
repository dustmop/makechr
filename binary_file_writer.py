ZERO_BYTE = 0


class BinaryFileWriter(object):
  def __init__(self, tmpl):
    self._name = None
    self._fout = None
    self._tmpl = tmpl
    self._order = None
    self._component_req = {}

  def _fill_template(self, replace):
    return self._tmpl.replace('%s', replace)

  def get_writable(self, name, unused_is_condensable):
    if self._fout:
      self.close()
    self._name = name
    self._fout = open(self._fill_template(name), 'wb')
    return self._fout

  def get_bytes(self, name):
    fin = open(self._fill_template(name), 'rb')
    content = fin.read()
    fin.close()
    byte_value = 0
    extract = self._component_req.get(name)
    if extract and len(content) < extract:
      content = content + (chr(byte_value) * (extract - len(content)))
    return content

  def pad(self, size, order, align, extract):
    _ = size
    _ = order
    _ = align
    self._component_req[self._name] = extract
    self._order = order
    if self._order == 1:
      num = extract - size
      self._fout.write(chr(ZERO_BYTE) * num)

  def close(self):
    extract = self._component_req.get(self._name)
    if extract:
      num = extract - self._fout.tell()
      self._fout.write(chr(ZERO_BYTE) * num)
    self._fout.close()
    self._fout = None


  def set_null_value(self, val):
    pass
