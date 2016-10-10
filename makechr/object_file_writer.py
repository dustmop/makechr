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

  def configure(self, null_value=None, size=None, order=None, align=None,
                extract=None):
    self.info.null_value = null_value
    self.info.size = size
    self.info.order = order
    self.info.align = align
    self.component_req[self.info.name] = extract

  def write_module(self, module_name):
    """Write the module name to the valiant object."""
    self.file_obj.header.module = module_name

  def write_bg_color(self, bg_color):
    """Write the bg_color metadata to the valiant object."""
    settings = self.obj_data.settings
    settings.bg_color = bg_color

  def write_chr_info(self, chr_data):
    """Write size of chr data."""
    settings = self.obj_data.settings
    chr_metadata = self._get_chr_metadata(settings)
    chr_metadata.size = chr_data.size()

  def write_extra_settings(self, config):
    """Write extra settings to the valiant object."""
    if (config.traversal == 'horizontal' and not config.chr_order and
        not config.palette_order and not config.is_locked_tiles):
      return
    settings = self.obj_data.settings
    chr_metadata = self._get_chr_metadata(settings)
    if config.chr_order:
      chr_metadata.order = config.chr_order
    if config.is_locked_tiles:
      chr_metadata.is_locked_tiles = config.is_locked_tiles
    if config.traversal and config.traversal != 'horizontal':
      chr_metadata.traversal = config.traversal
    if config.is_sprite:
      palette_metadata = self._get_palette_metadata(settings)
      palette_metadata.order = 1

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
    if info.null_value:
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

  def _get_chr_metadata(self, settings):
    if len(settings.chr_metadata) > 0:
      return settings.chr_metadata[0]
    else:
      return settings.chr_metadata.add()

  def _get_palette_metadata(self, settings):
    if len(settings.palette_metadata) > 0:
      return settings.palette_metadata[0]
    else:
      return settings.palette_metadata.add()

  def save(self, filename):
    serialized = self.file_obj.SerializeToString()
    fp = open(filename, 'wb')
    fp.write(serialized)
    fp.close()
