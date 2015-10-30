import binary_file_writer
from constants import *
import os

object_file_writer = None


class GraphicsPage(object):
  def __init__(self):
    self.nametable = [row[:] for row in
                      [[0]*(NUM_BLOCKS_X*2)]*(NUM_BLOCKS_Y*2)]
    self.block_palette = [row[:] for row in
                          [[0]*(NUM_BLOCKS_X)]*(NUM_BLOCKS_Y)]


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
    self._writer = None
    self._bg_color = None

  def get_writer(self):
    return self._writer

  def save_template(self, tmpl, is_locked_tiles):
    """Save binary files representing the ppu memory.

    tmpl: String representing a filename template to save files to.
    """
    self._writer = binary_file_writer.BinaryFileWriter(tmpl)
    self._save_components(is_locked_tiles)

  def save_valiant(self, output_filename, is_locked_tiles):
    """Save the ppu memory as a protocal buffer based object file.

    The format of an object file is specific by valiant.proto.

    output_filename: String representing a filename for the object file.
    """
    global object_file_writer
    if object_file_writer is None:
      import object_file_writer
    self._writer = object_file_writer.ObjectFileWriter()
    self._save_components(is_locked_tiles)
    module_name = os.path.splitext(os.path.basename(output_filename))[0]
    self._writer.write_module(module_name)
    self._writer.write_bg_color(self._bg_color)
    self._writer.write_chr_info(self.chr_data)
    self._writer.write_extra_settings(is_locked_tiles)
    self._writer.save(output_filename)

  def _save_components(self, skip_nametable):
    if not skip_nametable:
      fout = self._writer.get_writable('nametable')
      self._save_nametable(fout, self.gfx_1.nametable)
    fout = self._writer.get_writable('chr')
    self._save_chr(fout, self.chr_data)
    self._writer.pad(0x2000)
    self._writer.align(0x10)
    fout = self._writer.get_writable('palette')
    self._save_palette(fout, self.palette_nt, self.palette_spr)
    self._writer.set_null_value(self._bg_color)
    fout = self._writer.get_writable('attribute')
    self._save_attribute(fout, self.gfx_1.block_palette)
    self._writer.close()

  def _save_nametable(self, fout, nametable):
    for y in xrange(NUM_BLOCKS_Y * 2):
      for x in xrange(NUM_BLOCKS_X * 2):
        nt = nametable[y][x]
        fout.write(chr(nt))

  def _save_chr(self, fout, chr_data):
    # TODO: Respect is_sprite and page_org.
    for d in chr_data:
      d.write(fout)

  def _save_palette(self, fout, palette_1, palette_2):
    self._bg_color = self._get_bg_color(palette_1, palette_2)
    self._write_single_palette(fout, palette_1, self._bg_color)
    self._write_single_palette(fout, palette_2, self._bg_color)

  def _save_attribute(self, fout, block_palette):
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
      return
    for i in xrange(4):
      palette_option = palette.get(i)
      if palette_option is None:
        palette_option = []
      for j in xrange(4):
        if j < len(palette_option):
          fout.write(chr(palette_option[j]))
        else:
          fout.write(chr(bg_color))
