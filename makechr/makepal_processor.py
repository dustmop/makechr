import errors
import image_processor
import gen.valiant_pb2 as valiant
import palette


MAGIC_NUM = 7210303610482106886


class MakepalProcessor(object):
  def process_image(self, img, args):
    self._err = errors.ErrorCollector()
    self.width, self.height = img.size
    self.pixels = img.load()
    self.base = image_processor.ImageProcessor()
    self.base.pixels = self.pixels
    try:
      self.unit_size = self._find_unit_size()
      self.pal = self._build_palette()
    except Exception as e:
      self._err.add(e)
      return

  def err(self):
    return self._err

  def _find_unit_size(self):
    self.border_color = self.pixels[0,0]
    unit_size = None
    for k in xrange(min(self.width, self.height)):
      if self.pixels[k,k] != self.border_color:
        unit_size = k
        break
    else:
      raise errors.MakepalBorderNotFound()
    # Validate border.
    for x in xrange(self.width):
      # Top border
      self._validate_border(unit_size, 0, x)
      self._validate_border(unit_size, unit_size - 1, x)
      # Bottom border
      self._validate_border(unit_size, self.height - unit_size, x)
      self._validate_border(unit_size, self.height - 1, x)
    for y in xrange(self.height):
      # Left border
      self._validate_border(unit_size, y, 0)
      self._validate_border(unit_size, y, unit_size - 1)
      # Right border
      self._validate_border(unit_size, y, self.width - unit_size)
      self._validate_border(unit_size, y, self.width - 1)
    return unit_size

  def _validate_border(self, unused, y, x):
    color = self.pixels[x,y]
    if color != self.border_color:
      sys.stderr.write('Failed')

  def _build_palette(self):
    cols = self.width / self.unit_size
    rows = self.height / self.unit_size
    pal = palette.Palette()
    for y in xrange(1, rows - 1):
      p = []
      for x in xrange(1, cols - 1):
        nc = self._unit_nes_color(y, x)
        if nc != -1:
          p.append(nc)
      if p:
        pal.set_bg_color(p[0])
        pal.add(p)
    pal.ensure_alignment()
    return pal

  def _unit_nes_color(self, row, col):
    color = self.pixels[col * self.unit_size, row * self.unit_size]
    if color == self.border_color:
      return -1
    y = row * self.unit_size
    x = col * self.unit_size
    nc = self.base.get_nes_color(y, x)
    for i in xrange(self.unit_size):
      # Top
      if nc != self.base.get_nes_color(y, x + i):
        raise errors.MakepalInvalidFormat()
      # Bottom
      if nc != self.base.get_nes_color(y + self.unit_size - 1, x + i):
        raise errors.MakepalInvalidFormat()
      # Left
      if nc != self.base.get_nes_color(y + i, x):
        raise errors.MakepalInvalidFormat()
      # Right
      if nc != self.base.get_nes_color(y + i, x + self.unit_size - 1):
        raise errors.MakepalInvalidFormat()
    return nc

  def _build_vobject(self, palette):
    obj = valiant.ObjectFile()
    obj.magic1 = MAGIC_NUM % 100
    obj.magic2 = MAGIC_NUM / 100
    obj.header.short_palette = True
    packet = obj.body.packets.add()
    packet.role = valiant.PALETTE
    binary = packet.binary
    binary.bin = bytes(self.pal.to_bytes())
    return obj

  def create_output(self, out_file):
    if out_file.endswith('.bin') or out_file.endswith('.dat'):
      serialized = self.pal.to_bytes()
    else:
      obj = self._build_vobject(self.pal)
      serialized = obj.SerializeToString()
    fp = open(out_file, 'wb')
    fp.write(serialized)
    fp.close()
