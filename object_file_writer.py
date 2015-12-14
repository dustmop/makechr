import gen.valiant_pb2 as valiant
import StringIO


MAGIC_NUM = 7210303610482106886


class DataInfo(object):
  def __init__(self):
    self.clear()

  def clear(self):
    self.name = None
    self.align = None
    self.size = None
    self.order = None
    self.null_value = None
    self.is_condensable = False

  def empty(self):
    return self.name is None


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
    self.buffer = None
    self.info = DataInfo()
    self.component_req = {}

  def get_writable(self, name, is_condensable):
    if not self.info.empty():
      self.add_component(self.buffer.getvalue(), self.info)
    self.buffer = StringIO.StringIO()
    self.info.clear()
    self.info.name = name
    self.info.is_condensable = is_condensable
    return self.buffer

  def close(self):
    if not self.info.empty():
      self.add_component(self.buffer.getvalue(), self.info)
      self.info.clear()

  def pad(self, size, order, align, extract):
    self.info.size = size
    self.info.order = order
    self.info.align = align
    self.component_req[self.info.name] = extract

  def set_null_value(self, val):
    self.info.null_value = val

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
    content = binary.bin
    null_value = chr(binary.null_value or 0)
    if binary.padding:
      content = content + (null_value * binary.padding)
    if binary.pre_pad:
      content = (null_value * binary.padding) + content
    extract = self.component_req.get(name)
    if extract and len(content) < extract:
      content = content + (null_value * (extract - len(content)))
    return content

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
    chr_metadata = self._get_chr_metaata(settings)
    chr_metadata.size = len(chr_data)
    last = None
    for c,i in decorated:
      if c == last:
        continue
      chr_metadata.sorted_idx.append(i)
      last = c

  def write_extra_settings(self, order, traversal, is_locked_tiles):
    """Write extra settings to the valiant object."""
    if traversal == 'horizontal' and not order and not is_locked_tiles:
      return
    settings = self.obj_data.settings
    chr_metadata = self._get_chr_metaata(settings)
    if order:
      chr_metadata.order = order
    if is_locked_tiles:
      chr_metadata.is_locked_tiles = is_locked_tiles
    if traversal and traversal != 'horizontal':
      chr_metadata.traversal = traversal

  def add_component(self, bytes, info):
    pad_size = info.size - len(bytes) if (not info.size is None) else None
    if info.is_condensable:
      pre_pad, padding, bytes = self._condense(bytes, info.align, pad_size)
    else:
      pre_pad = padding = 0
    role = valiant.DataRole.Value(info.name.upper())
    idx = len(self.obj_data.binaries)
    binary = self.obj_data.binaries.add()
    binary.bin = bytes
    if not info.null_value is None:
      binary.null_value = info.null_value
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

  def _get_chr_metaata(self, settings):
    if len(settings.chr_metadata) > 0:
      return settings.chr_metadata[0]
    else:
      return settings.chr_metadata.add()

  def save(self, filename):
    serialized = self.file_obj.SerializeToString()
    fp = open(filename, 'wb')
    fp.write(serialized)
    fp.close()
