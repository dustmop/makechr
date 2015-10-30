class BinaryFileWriter(object):
  def __init__(self, tmpl):
    self._fout = None
    self._tmpl = tmpl

  def _fill_template(self, replace):
    return self._tmpl.replace('%s', replace)

  def get_writable(self, name):
    if self._fout:
      self._fout.close()
    self._fout = open(self._fill_template(name), 'wb')
    return self._fout

  def get_bytes(self, name):
    fin = open(self._fill_template(name), 'rb')
    content = fin.read()
    fin.close()
    return content

  def close(self):
    self._fout.close()
    self._fout = None

  def align(self, at):
    pass

  def pad(self, size, byte_value=0):
    num = size - self._fout.tell()
    self._fout.write(chr(byte_value) * num)

  def set_null_value(self, val):
    pass
