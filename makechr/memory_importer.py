import chr_data
import errors
import os
import palette
import ppu_memory
from constants import *

class MemoryImporter(object):
  def read(self, filename, kind):
    if kind == 'ram':
      return self.read_ram(filename)
    elif kind == 'valiant':
      return self.read_valiant(filename)
    raise errors.UnknownMemoryKind(kind)

  def read_ram(self, filename):
    # Check file size
    fp = open(filename, 'rb')
    file_size = os.fstat(fp.fileno()).st_size
    if file_size != 0x4000:
      raise errors.FileFormatError(file_size, size=0x4000)
    mem = ppu_memory.PpuMemory()
    mem.allocate_num_pages(2)
    # Read CHR from $0000-$2000
    mem.chr_set = chr_data.ChrBank.from_binary(fp.read(0x2000))
    # TODO: Handle chr order (background / sprite at $0000 / $1000).
    # For each graphics page, read nametable & attribute.
    for loop_num in xrange(2):
      gfx = mem.gfx[0] if not loop_num else mem.gfx[1]
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

  def read_valiant(self, filename):
    import gen.valiant_pb2 as valiant
    fp = open(filename)
    content = fp.read()
    fp.close()
    mem = ppu_memory.PpuMemory()
    mem.allocate_num_pages(2)
    obj_file = valiant.ObjectFile()
    obj_file.ParseFromString(content)
    binary_map = {}
    for packet in obj_file.body.packets:
      if packet.role == valiant.CHR:
        binary_map['chr'] = packet.binary
      if packet.role == valiant.NAMETABLE:
        binary_map['nametable'] = packet.binary
      if packet.role == valiant.ATTRIBUTE:
        binary_map['attribute'] = packet.binary
      if packet.role == valiant.PALETTE:
        binary_map['palette'] = packet.binary
    chr_bin = self._expand_binary(binary_map['chr'])
    nt_bin = self._expand_binary(binary_map['nametable'])
    at_bin = self._expand_binary(binary_map['attribute'])
    pal_bin = self._expand_binary(binary_map['palette'])
    # Parse chr data.
    mem.chr_set = chr_data.ChrBank.from_binary(bytes(bytearray(chr_bin)))
    # Parse nametable data.
    for y in xrange(30):
      for x in xrange(32):
        mem.gfx[0].nametable[y][x] = nt_bin[y*32 + x]
    # Parse attributes data.
    for a in xrange(64):
      p0 = (at_bin[a] >> 0) & 0x03
      p1 = (at_bin[a] >> 2) & 0x03
      p2 = (at_bin[a] >> 4) & 0x03
      p3 = (at_bin[a] >> 6) & 0x03
      y = (a / 8) * 4
      x = (a % 8) * 4
      mem.gfx[0].colorization[y + 0][x + 0] = p0
      mem.gfx[0].colorization[y + 0][x + 2] = p1
      if y < (7 * 4):
        mem.gfx[0].colorization[y + 2][x + 0] = p2
        mem.gfx[0].colorization[y + 2][x + 2] = p3
    # Parse palette data.
    pal = palette.Palette()
    pal.set_bg_color(pal_bin[0])
    for i in xrange(4):
      p = []
      for j in xrange(4):
        p.append(pal_bin[i*4 + j])
      pal.add(p)
    mem.palette_nt = pal
    return mem

  def _expand_binary(self, binary, req_align=0):
    prepad = binary.pre_pad if binary.pre_pad else None
    padding = binary.padding if binary.padding else None
    nullval = binary.null_value if binary.null_value else 0
    if req_align:
      size = (prepad or 0) + len(binary.bin) + (padding or 0)
      padding = (padding or 0) + req_align - size
    bytes = bytearray()
    if prepad is not None:
      bytes += (chr(nullval) * prepad)
    bytes += binary.bin
    if padding is not None:
      bytes += (chr(nullval) * padding)
    return bytes
