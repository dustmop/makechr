from constants import *


class PpuMemory(object):
  """PpuMemory

  Data structure representing the components of graphics in PPU memory.
  """
  def __init__(self):
    self.block_palette = [row[:] for row in
                          [[None]*(NUM_BLOCKS_X)]*(NUM_BLOCKS_Y)]
    self.nametable = [row[:] for row in
                      [[None]*(NUM_BLOCKS_X*2)]*(NUM_BLOCKS_Y*2)]
    self.palette = None
    self.chr_data = []

  def save(self, tmpl):
    """Save binary files representing the ppu memory.

    tmpl: String representing a filename template to save files to.
    """
    self.save_nametable(self.nametable, tmpl)
    self.save_chr(self.chr_data, tmpl)
    self.save_palette(self.palette, tmpl)
    self.save_attribute(self.block_palette, tmpl)

  def pad(self, fout, num, byte_value=0):
    fout.write(chr(byte_value) * num)

  def fill_template(self, tmpl, replace):
    return tmpl.replace('%s', replace)

  def save_nametable(self, nametable, tmpl):
    fout = open(self.fill_template(tmpl, 'nametable'), 'wb')
    for y in xrange(NUM_BLOCKS_Y * 2):
      for x in xrange(NUM_BLOCKS_X * 2):
        nt = nametable[y][x]
        fout.write(chr(nt))
    fout.close()

  def save_chr(self, chr_data, tmpl):
    fout = open(self.fill_template(tmpl, 'chr'), 'wb')
    for d in chr_data:
      d.write(fout)
    padding = 8192 - (len(chr_data) * 16)
    self.pad(fout, padding)
    fout.close()

  def save_palette(self, palette, tmpl):
    fout = open(self.fill_template(tmpl, 'palette'), 'wb')
    bg_color = palette.bg_color
    for i in xrange(4):
      palette_option = palette.get(i)
      if palette_option is None:
        palette_option = [bg_color] * 4
      for j in xrange(4):
        if j < len(palette_option):
          fout.write(chr(palette_option[j]))
        else:
          fout.write(chr(bg_color))
    self.pad(fout, 16, bg_color)
    fout.close()

  def save_attribute(self, block_palette, tmpl):
    fout = open(self.fill_template(tmpl, 'attribute'), 'wb')
    for attr_y in xrange(NUM_BLOCKS_Y / 2):
      for attr_x in xrange(NUM_BLOCKS_X / 2):
        y = attr_y * 2
        x = attr_x * 2
        p0 = block_palette[y + 0][x + 0]
        p1 = block_palette[y + 0][x + 1]
        p2 = block_palette[y + 1][x + 0]
        p3 = block_palette[y + 1][x + 1]
        attr = p0 + (p1 << 2) + (p2 << 4) + (p3 << 6)
        fout.write(chr(attr))
    self.pad(fout, 8)
    fout.close()
