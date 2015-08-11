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

  def get_writable(self):
    return StringIO.StringIO()

  def get_component_bytes(self, name):
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
    """Write the module name."""
    self.file_obj.header.module = module_name

  def write_bg_color(self, bg_color):
    """Write the bg_color metadata."""
    settings = self.obj_data.settings
    settings.bg_color = bg_color

  def write_nametable(self, buffer):
    self._write_single_component(valiant.NAMETABLE, buffer.getvalue(), 0, 0)

  def write_chr(self, buffer, padding):
    self._write_single_component(valiant.CHR, buffer.getvalue(), 0, padding)

  def write_palette(self, buffer, pre_pad, padding, bg_color):
    self._write_single_component(valiant.PALETTE, buffer.getvalue(), pre_pad,
                                 padding, bg_color)

  def write_attribute(self, buffer):
    self._write_single_component(valiant.ATTRIBUTE, buffer.getvalue(), 0, 0)

  def _write_single_component(self, role, bytes, pre_pad, padding,
                              null_value=None):
    idx = len(self.obj_data.binaries)
    binary = self.obj_data.binaries.add()
    binary.bin = bytes
    if not null_value is None:
      binary.null_value = null_value
    if pre_pad:
      binary.pre_pad = pre_pad
      binary.bin = binary.bin[pre_pad:]
    if padding:
      binary.padding = padding
      binary.bin = binary.bin[0:len(binary.bin) - padding]
    component = self.obj_data.components.add()
    component.role = role
    component.binary_index = idx

  def save(self, filename):
    serialized = self.file_obj.SerializeToString()
    fp = open(filename, 'wb')
    fp.write(serialized)
    fp.close()
