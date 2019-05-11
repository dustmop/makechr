from constants import *


ZERO_BYTE = bytearray([0])[0]


class BinaryFileWriter(object):
  def __init__(self, tmpl):
    self._name = None
    self._fout = None
    self._tmpl = tmpl
    self._order = None
    self._null_value = ZERO_BYTE
    self._component_req = {}

  def _fill_template(self, replace):
    return self._tmpl.replace('%s', replace)

  def get_writable(self, name, unused_is_condensable):
    if self._fout:
      self.close()
    self._name = name
    filename = self._fill_template(name)
    if name == 'sprite_picdata':
      filename = filename.replace('.dat', '.json')
    self._fout = open(filename, 'wb')
    return self._fout

  def configure(self, null_value=None, size=None, order=None, align=None,
                extract=None):
    self._null_value = null_value or bytearray([0])[0]
    _ = size
    _ = order
    _ = align
    self._component_req[self._name] = extract
    self._order = order
    if self._order == 1:
      num = extract - size
      self._fout.write(bytearray([self._null_value]) * num)

  def close(self):
    if self._fout is None:
      return
    extract = self._component_req.get(self._name)
    if extract:
      num = extract - self._fout.tell()
      self._fout.write(bytearray([self._null_value]) * num)
    self._fout.close()
    self._fout = None
