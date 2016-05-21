import binary_file_writer
from constants import *
import os

object_file_writer = None


class GraphicsPage(object):
  def __init__(self):
    self.nametable = [row[:] for row in
                      [[0]*(NUM_BLOCKS_X*2)]*(NUM_BLOCKS_Y*2)]
    self.position_palette = [row[:] for row in
                             [[0]*(NUM_BLOCKS_X*2)]*(NUM_BLOCKS_Y*2)]


class PpuMemory(object):
  """PpuMemory

  Data structure representing the components of graphics in PPU memory.
  """
  def __init__(self):
    self.gfx_0 = GraphicsPage()
    self.gfx_1 = GraphicsPage() # unused
    self.palette_nt = None
    self.palette_spr = None
    self.chr_data = []
    self._writer = None
    self._bg_color = None
    self.empty_tile = None
    self.is_locked_tiles = False
    self.nt_width = None

  def get_writer(self):
    return self._writer

  def save_template(self, tmpl, chr_order, is_sprite):
    """Save binary files representing the ppu memory.

    tmpl: String representing a filename template to save files to.
    chr_order: Order of the chr data in memory.
    is_sprite: Whether the image is of sprites.
    """
    components = self._get_enabled_components(is_sprite)
    self._writer = binary_file_writer.BinaryFileWriter(tmpl,
        self.is_locked_tiles, self.nt_width)
    self._save_components(components, chr_order)

  def save_valiant(self, output_filename, chr_order, traversal, is_sprite):
    """Save the ppu memory as a protocal buffer based object file.

    The format of an object file is specific by valiant.proto.

    output_filename: String representing a filename for the object file.
    chr_order: Order of the chr data in memory.
    traversal: Traversal order, either "horizontal" or "block".
    is_sprite: Whether the image is of sprites.
    """
    global object_file_writer
    if object_file_writer is None:
      import object_file_writer
    components = self._get_enabled_components(is_sprite)
    self._writer = object_file_writer.ObjectFileWriter()
    self._save_components(components, chr_order)
    module_name = os.path.splitext(os.path.basename(output_filename))[0]
    self._writer.write_module(module_name)
    self._writer.write_bg_color(self._bg_color)
    self._writer.write_chr_info(self.chr_data)
    self._writer.write_extra_settings(chr_order, traversal,
                                      self.is_locked_tiles)
    self._writer.save(output_filename)

  def _save_components(self, components, chr_order):
    if 'nametable' in components:
      fout = self._writer.get_writable('nametable', False)
      self._save_nametable(fout, self.gfx_0.nametable)
    if 'chr' in components:
      fout = self._writer.get_writable('chr', True)
      self._writer.pad(size=0x1000, order=chr_order, align=0x10, extract=0x2000)
      self._save_chr(fout, self.chr_data)
    if 'palette' in components:
      fout = self._writer.get_writable('palette', True)
      self._save_palette(fout, self.palette_nt, self.palette_spr)
      self._writer.set_null_value(self._bg_color)
    if 'attribute' in components:
      fout = self._writer.get_writable('attribute', False)
      self._save_attribute(fout, self.gfx_0.position_palette)
    if 'spritelist' in components:
      fout = self._writer.get_writable('spritelist', False)
      self._save_spritelist(fout, self.gfx_0.nametable,
                            self.gfx_0.position_palette)
    self._writer.close()

  def _save_nametable(self, fout, nametable):
    for y in xrange(NUM_BLOCKS_Y * 2):
      for x in xrange(NUM_BLOCKS_X * 2):
        nt = nametable[y][x]
        fout.write(chr(nt))

  def _save_chr(self, fout, chr_data):
    for d in chr_data:
      d.write(fout)

  def _save_palette(self, fout, palette_1, palette_2):
    self._bg_color = self._get_bg_color(palette_1, palette_2)
    self._write_single_palette(fout, palette_1, self._bg_color)
    self._write_single_palette(fout, palette_2, self._bg_color)

  def _save_attribute(self, fout, position_palette):
    for attr_y in xrange(NUM_BLOCKS_Y / 2 + 1):
      for attr_x in xrange(NUM_BLOCKS_X / 2):
        block_y = attr_y * 2
        block_x = attr_x * 2
        y = block_y * 2
        x = block_x * 2
        p0 = position_palette[y + 0][x + 0]
        p1 = position_palette[y + 0][x + 2]
        p2 = position_palette[y + 2][x + 0] if block_y + 1 < NUM_BLOCKS_Y else 0
        p3 = position_palette[y + 2][x + 2] if block_y + 1 < NUM_BLOCKS_Y else 0
        attr = p0 + (p1 << 2) + (p2 << 4) + (p3 << 6)
        fout.write(chr(attr))

  def _save_spritelist(self, fout, sprite_positions, sprite_palettes):
    n = 0
    for y in xrange(NUM_BLOCKS_Y * 2):
      for x in xrange(NUM_BLOCKS_X * 2):
        tile = sprite_positions[y][x]
        if tile != self.empty_tile:
          y_pos = y * 8 - 1 if y > 0 else 0
          x_pos = x * 8
          attr = sprite_palettes[y][x]
          fout.write(chr(y_pos))
          fout.write(chr(tile))
          fout.write(chr(attr))
          fout.write(chr(x_pos))
          n += 1
    if n < 64:
      fout.write(chr(0xff))

  def _get_bg_color(self, palette_1, palette_2):
    bg_color = None
    if palette_1:
      bg_color = palette_1.bg_color
    if palette_2:
      if bg_color and bg_color != palette_2.bg_color:
        raise errors.PaletteInconsistentError(bg_color, palette_2.bg_color)
      bg_color = palette_2.bg_color
    return bg_color

  def _get_enabled_components(self, is_sprite):
    components = set()
    if not is_sprite and not self.is_locked_tiles:
      components.add('nametable')
    components.add('chr')
    components.add('palette')
    if not is_sprite:
      components.add('attribute')
    else:
      components.add('spritelist')
    return components

  def _write_single_palette(self, fout, palette, bg_color):
    if not palette:
      if not bg_color:
        bg_color = 0x0f
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
