from constants import *


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

  def save(self, tmpl):
    """Save binary files representing the ppu memory.

    tmpl: String representing a filename template to save files to.
    """
    self._tmpl = tmpl
    self.save_nametable(self.gfx_1.nametable)
    self.save_chr(self.chr_data)
    self.save_palette(self.palette_nt, self.palette_spr)
    self.save_attribute(self.gfx_1.block_palette)

  def pad(self, fout, num, byte_value=0):
    fout.write(chr(byte_value) * num)

  def fill_template(self, replace):
    return self._tmpl.replace('%s', replace)

  def save_nametable(self, nametable):
    fout = open(self.fill_template('nametable'), 'wb')
    for y in xrange(NUM_BLOCKS_Y * 2):
      for x in xrange(NUM_BLOCKS_X * 2):
        nt = nametable[y][x]
        fout.write(chr(nt))
    fout.close()

  def save_chr(self, chr_data):
    # TODO: Respect is_sprite and page_org.
    fout = open(self.fill_template('chr'), 'wb')
    for d in chr_data:
      d.write(fout)
    padding = 0x2000 - (len(chr_data) * 16)
    self.pad(fout, padding)
    fout.close()

  def save_palette(self, palette_1, palette_2):
    fout = open(self.fill_template('palette'), 'wb')
    bg_color = self._get_bg_color(palette_1, palette_2)
    self._write_single_palette(fout, palette_1, bg_color)
    self._write_single_palette(fout, palette_2, bg_color)
    fout.close()

  def save_attribute(self, block_palette):
    fout = open(self.fill_template('attribute'), 'wb')
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
    fout.close()

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
        palette_option = [bg_color] * 4
      for j in xrange(4):
        if j < len(palette_option):
          fout.write(chr(palette_option[j]))
        else:
          fout.write(chr(bg_color))
