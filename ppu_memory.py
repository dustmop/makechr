from constants import *
import object_file_writer
import os


class GraphicsPage(object):
  def __init__(self):
    self.nametable = [row[:] for row in
                      [[None]*(NUM_BLOCKS_X*2)]*(NUM_BLOCKS_Y*2)]
    self.block_palette = [row[:] for row in
                          [[None]*(NUM_BLOCKS_X)]*(NUM_BLOCKS_Y)]


class PpuMemory(object):
  """PpuMemory

  Data structure representing the components of graphics in PPU memory.
  """
  def __init__(self):
    self.gfx_1 = GraphicsPage()
    self.gfx_2 = GraphicsPage() # unused
    self.palette_nt = None
    self.palette_spr = None
    self.chr_data = []
    self._tmpl = None

  def save_template(self, tmpl):
    """Save binary files representing the ppu memory.

    tmpl: String representing a filename template to save files to.
    """
    self._tmpl = tmpl
    fout = open(self.fill_template('nametable'), 'wb')
    self.save_nametable(fout, self.gfx_1.nametable)
    fout.close()
    fout = open(self.fill_template('chr'), 'wb')
    self.save_chr(fout, self.chr_data)
    fout.close()
    fout = open(self.fill_template('palette'), 'wb')
    self.save_palette(fout, self.palette_nt, self.palette_spr)
    fout.close()
    fout = open(self.fill_template('attribute'), 'wb')
    self.save_attribute(fout, self.gfx_1.block_palette)
    fout.close()

  def save_valiant(self, output_filename):
    """Save the ppu memory as a protocal buffer based object file.

    The format of an object file is specific by valiant.proto.

    output_filename: String representing a filename for the object file.
    """
    self._writer = object_file_writer.ObjectFileWriter()
    # nametable
    fout = self._writer.get_writable()
    self.save_nametable(fout, self.gfx_1.nametable)
    self._writer.write_nametable(fout)
    # chr
    fout = self._writer.get_writable()
    padding = self.save_chr(fout, self.chr_data)
    self._writer.write_chr(fout, padding)
    # palette
    fout = self._writer.get_writable()
    (pre_pad, padding, bg_color) = self.save_palette(
      fout, self.palette_nt, self.palette_spr)
    self._writer.write_palette(fout, pre_pad, padding, bg_color)
    # attribute
    fout = self._writer.get_writable()
    self.save_attribute(fout, self.gfx_1.block_palette)
    self._writer.write_attribute(fout)
    # others
    module_name = os.path.splitext(os.path.basename(output_filename))[0]
    self._writer.write_module(module_name)
    self._writer.write_bg_color(bg_color)
    self._writer.save(output_filename)

  def pad(self, fout, num, byte_value=0):
    fout.write(chr(byte_value) * num)

  def get_bytes(self, name):
    if self._tmpl:
      fin = open(self.fill_template(name), 'rb')
      content = fin.read()
      fin.close()
      return content
    elif self._writer:
      return self._writer.get_component_bytes(name)

  def fill_template(self, replace):
    return self._tmpl.replace('%s', replace)

  def save_nametable(self, fout, nametable):
    for y in xrange(NUM_BLOCKS_Y * 2):
      for x in xrange(NUM_BLOCKS_X * 2):
        nt = nametable[y][x]
        fout.write(chr(nt))

  def save_chr(self, fout, chr_data):
    # TODO: Respect is_sprite and page_org.
    for d in chr_data:
      d.write(fout)
    padding = 0x2000 - (len(chr_data) * 16)
    self.pad(fout, padding)
    return padding

  def save_palette(self, fout, palette_1, palette_2):
    bg_color = self._get_bg_color(palette_1, palette_2)
    pre_pad = 0
    inner   = self._write_single_palette(fout, palette_1, bg_color)
    padding = self._write_single_palette(fout, palette_2, bg_color)
    # If the entire second palette is empty, increase the amount of padding.
    if padding == 16:
      padding += inner
    elif inner == 16:
      pre_pad = inner
    return (pre_pad, padding, bg_color)

  def save_attribute(self, fout, block_palette):
    for attr_y in xrange(NUM_BLOCKS_Y / 2 + 1):
      for attr_x in xrange(NUM_BLOCKS_X / 2):
        y = attr_y * 2
        x = attr_x * 2
        p0 = block_palette[y + 0][x + 0]
        p1 = block_palette[y + 0][x + 1]
        p2 = block_palette[y + 1][x + 0] if y + 1 < NUM_BLOCKS_Y else 0
        p3 = block_palette[y + 1][x + 1] if y + 1 < NUM_BLOCKS_Y else 0
        attr = p0 + (p1 << 2) + (p2 << 4) + (p3 << 6)
        fout.write(chr(attr))

  def _get_bg_color(self, palette_1, palette_2):
    bg_color = None
    if palette_1:
      bg_color = palette_1.bg_color
    if palette_2:
      if bg_color and bg_color != palette_2.bg_color:
        raise errors.PaletteInconsistentError(bg_color, palette_2.bg_color)
      bg_color = palette_2.bg_color
    return bg_color

  def _write_single_palette(self, fout, palette, bg_color):
    if not palette:
      fout.write(chr(bg_color) * 16)
      return 16
    padding = 0
    for i in xrange(4):
      palette_option = palette.get(i)
      if palette_option is None:
        palette_option = []
      for j in xrange(4):
        if j < len(palette_option):
          fout.write(chr(palette_option[j]))
          padding = 0
        else:
          fout.write(chr(bg_color))
          padding += 1
    return padding
