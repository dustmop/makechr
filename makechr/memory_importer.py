import chr_data
import errors
import os
import palette
import ppu_memory
from constants import *

class MemoryImporter(object):
  def read(self, filename):
    # Check file size
    fp = open(filename, 'rb')
    file_size = os.fstat(fp.fileno()).st_size
    if file_size != 0x4000:
      raise errors.FileFormatError(file_size, size=0x4000)
    mem = ppu_memory.PpuMemory()
    # Read CHR from $0000-$2000
    mem.chr_page = chr_data.ChrPage.from_binary(fp.read(0x1000))
    mem.chr_page2 = chr_data.ChrPage.from_binary(fp.read(0x1000))
    # TODO: Handle chr order (background / sprite at $0000 / $1000).
    # For each graphics page, read nametable & attribute.
    for loop_num in xrange(2):
      gfx = mem.gfx_0 if not loop_num else mem.gfx_1
      if loop_num == 1:
        # Skip $2400-$2c00
        fp.read(0x800)
      # Read nametable from $2000-$23c0 & $2c00-$2fc0.
      # TODO: Handle mirroring.
      for y in xrange(30):
        for x in xrange(32):
          gfx.nametable[y][x] = ord(fp.read(1))
      # Read attributes from $23c0-$2400 & $2fc0-$3000.
      for k in xrange(64):
        byte = ord(fp.read(1))
        y = (k / 8) * 4
        x = (k % 8) * 4
        gfx.colorization[y + 0][x + 0] = (byte & 0x03)
        gfx.colorization[y + 0][x + 2] = (byte & 0x0c) >> 2
        if y < (7 * 4):
          gfx.colorization[y + 2][x + 0] = (byte & 0x30) >> 4
          gfx.colorization[y + 2][x + 2] = (byte & 0xc0) >> 6
    # Unused $3000-$3f00.
    unused = fp.read(0x0f00)
    # Read palette $3f00.
    mem.palette_nt = palette.Palette()
    mem.palette_spr = palette.Palette()
    # Two palettes, first for nametable, then for palette.
    bg_color = None
    pal = mem.palette_nt
    for loop_num in xrange(2):
      pal = mem.palette_nt if not loop_num else mem.palette_spr
      for k in xrange(4):
        opt = [ord(p) for p in fp.read(4)]
        if bg_color is None:
          bg_color = opt[0]
        pal.set_bg_color(bg_color)
        pal.add(opt)
    return mem
