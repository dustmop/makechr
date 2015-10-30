import gen.valiant_pb2 as valiant
import StringIO


MAGIC_NUM = 7210303610482106886


class ObjectFileWriter(object):
  """Creates a valiant object file from ppu memory.

  A valiant object file is a structured binary file, built using protocol
  buffers. It can hold multiple types of graphical data, such as nametable,
  chr, palette, attributes, in a single file, along with some metadata. See
  valiant.proto for more information.
  """
  def __init__(self):
    self.file_obj = valiant.ObjectFile()
    self.file_obj.magic1 = MAGIC_NUM % 100
    self.file_obj.magic2 = MAGIC_NUM / 100
    self.obj_data = self.file_obj.data
    self.curr_buffer = None
    self.curr_name = None
    self.curr_align = None
    self.curr_pad_size = None
    self.curr_null_value = None

  def get_writable(self, name):
    if self.curr_name:
      self.add_component(self.curr_name, self.curr_buffer.getvalue(),
                         self.curr_align, self.curr_pad_size,
                         self.curr_null_value)
    self.curr_buffer = StringIO.StringIO()
    self.curr_name = name
    self.curr_align = None
    self.curr_pad_size = None
    self.curr_null_value = None
    return self.curr_buffer

  def close(self):
    if self.curr_name:
      self.add_component(self.curr_name, self.curr_buffer.getvalue(),
                         self.curr_align, self.curr_pad_size,
                         self.curr_null_value)
      self.curr_name = None

  def align(self, at):
    self.curr_align = at

  def pad(self, num):
    self.curr_pad_size = num

  def set_null_value(self, val):
    self.curr_null_value = val

  def get_bytes(self, name):
    """Get bytes written to the component with name."""
    binary_index = None
    role = valiant.DataRole.Value(name.upper())
    for component in self.obj_data.components:
      if component.role == role:
        binary_index = component.binary_index
        break
    if binary_index is None:
      raise ValueError('Did not find component "%s"' % (name,))
    binary = self.obj_data.binaries[binary_index]
    bin = binary.bin
    null_value = chr(binary.null_value or 0)
    if binary.padding:
      bin = bin + (null_value * binary.padding)
    if binary.pre_pad:
      bin = (null_value * binary.padding) + bin
    return bin

  def write_module(self, module_name):
    """Write the module name to the valiant object."""
    self.file_obj.header.module = module_name

  def write_bg_color(self, bg_color):
    """Write the bg_color metadata to the valiant object."""
    settings = self.obj_data.settings
    settings.bg_color = bg_color

  def write_chr_info(self, chr_data):
    """Write size of chr data. Also, sort the chr data and write the
       indexes to the valiant object."""
    decorated = [(c.low + c.hi,i) for i,c in enumerate(chr_data)]
    decorated.sort()
    settings = self.obj_data.settings
    settings.chr_size = len(chr_data)
    last = None
    for c,i in decorated:
      if c == last:
        continue
      settings.sorted_chr_idx.append(i)
      last = c

  def add_component(self, name, bytes, align, pad_size, null_value):
    if not pad_size is None:
      pad_size = pad_size - len(bytes)
    pre_pad, padding, bytes = self._condense(bytes, align, pad_size)
    role = valiant.DataRole.Value(name.upper())
    idx = len(self.obj_data.binaries)
    binary = self.obj_data.binaries.add()
    binary.bin = bytes
    if not null_value is None:
      binary.null_value = null_value
    if not pre_pad is None:
      binary.pre_pad = pre_pad
    if not padding is None:
      binary.padding = padding
    component = self.obj_data.components.add()
    component.role = role
    component.binary_index = idx

  # TODO: Test.
  def _condense(self, bytes, align, extra_padding):
    if not align:
      align = 1
    size = len(bytes)
    first = bytes[0]
    first_width = next((i for i,n in enumerate(bytes) if first != n), size)
    first_width = first_width / align * align
    if first_width <= align:
      first_width = 0
    last = bytes[size - 1]
    last_width = next((i for i,n in enumerate(reversed(bytes)) if last != n), 0)
    last_width = last_width / align * align
    if last_width <= align:
      last_width = 0
    bytes = bytes[first_width:size - last_width]
    if not first_width:
      first_width = None
    # TODO: Need to check null_value.
    if extra_padding:
      last_width += extra_padding
    if not last_width:
      last_width = None
    return (first_width, last_width, bytes)

  def save(self, filename):
    serialized = self.file_obj.SerializeToString()
    fp = open(filename, 'wb')
    fp.write(serialized)
    fp.close()
