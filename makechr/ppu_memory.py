import binary_file_writer
import collections
import chr_data
from constants import *
import json
import os
import sys

object_file_writer = None


if sys.version_info < (3,0):
  range = xrange
  to_byte = chr
else:
  to_byte = lambda v: bytes([v])


class GraphicsPage(object):
  def __init__(self):
    self.nt_start = None
    self.nt_width = None
    self.nametable = [row[:] for row in [[0]*(NUM_TILES_X)]*(NUM_TILES_Y)]
    self.colorization = [row[:] for row in [[0]*(NUM_TILES_X)]*(NUM_TILES_Y)]


class PpuMemoryConfig(object):
  def __init__(self, traversal=None, is_sprite=None, is_locked_tiles=None,
               lock_sprite_flips=None, allow_overflow=None, chr_order=None,
               select_chr_plane=False):
    self.traversal = traversal
    self.is_sprite = is_sprite
    self.is_locked_tiles = is_locked_tiles
    self.lock_sprite_flips = lock_sprite_flips
    self.allow_overflow = allow_overflow or []
    self.chr_order = self.pick_order(chr_order, is_sprite)
    self.palette_order = int(bool(is_sprite))
    self.select_chr_plane = select_chr_plane

  def pick_order(self, order, is_sprite):
    if order is not None:
      return order
    return int(bool(is_sprite))


class PpuMemory(object):
  """PpuMemory

  Data structure representing the components of graphics in PPU memory.
  """
  def __init__(self):
    self.gfx = None
    self.palette_nt = None
    self.palette_spr = None
    self.chr_set = chr_data.ChrPage()
    self._writer = None
    self._bg_color = None
    self.empty_tile = None
    self.spritelist = []
    self.sprite_picdata = None
    # HACK: Not actually a part of ppu_memory. Only set here so that it can
    # be passed to the view renderer after free sprite traversal.
    self.zones = None

  def allocate_num_pages(self, num):
    self.gfx = [GraphicsPage() for i in range(num)]

  def override_bg_color(self, bg_color):
    self._bg_color = bg_color
    if self.palette_nt:
      self.palette_nt.set_bg_color(self._bg_color)
    if self.palette_spr:
      self.palette_spr.set_bg_color(self._bg_color)

  def upgrade_chr_set_to_bank(self):
    self.chr_set = chr_data.ChrBank()

  def save_template(self, tmpl, config):
    """Save binary files representing the ppu memory.

    tmpl: String representing a filename template to save files to.
    config: Configuration for how memory is represented.
    """
    self._writer = binary_file_writer.BinaryFileWriter(tmpl)
    return self._save_components(config)

  def save_valiant(self, output_filename, config):
    """Save the ppu memory as a protocal buffer based object file.

    The format of an object file is specific by valiant.proto.

    output_filename: String representing a filename for the object file.
    config: Configuration for how memory is represented.
    """
    global object_file_writer
    if object_file_writer is None:
      import object_file_writer
    self._writer = object_file_writer.ObjectFileWriter()
    ret = self._save_components(config)
    module_name = os.path.splitext(os.path.basename(output_filename))[0]
    self._writer.write_module(module_name)
    self._writer.write_bg_color(self._bg_color)
    self._writer.write_chr_info(self.chr_set)
    self._writer.write_extra_settings(config)
    self._writer.save(output_filename)
    return ret

  def _save_components(self, config):
    self._bg_color = self._get_bg_color(self.palette_nt, self.palette_spr)
    components = self._get_enabled_components(config)
    if 'nametable' in components:
      for i, gfx in enumerate(self.gfx):
        name = 'nametable' if i == 0 else ('nametable%d' % i)
        fout = self._writer.get_writable(name, False)
        self._save_nametable(fout, gfx.nametable)
        self._writer.close()
    if 'chr' in components:
      fout = self._writer.get_writable('chr', True)
      self._writer.configure(null_value=0, size=0x1000, order=config.chr_order,
                             align=0x10, extract=0x2000)
      self._save_chr(fout, self.chr_set, config.select_chr_plane)
    if 'palette' in components:
      fout = self._writer.get_writable('palette', True)
      self._writer.configure(null_value=self._bg_color, size=0x10,
                             order=config.palette_order, extract=0x20)
      self._save_palette(fout, self.palette_nt, self.palette_spr)
    if 'attribute' in components:
      for i, gfx in enumerate(self.gfx):
        name = 'attribute' if i == 0 else ('attribute%d' % i)
        fout = self._writer.get_writable(name, False)
        self._save_attribute(fout, gfx.colorization)
        self._writer.close()
    # TODO: Rename this component to `sprites`
    # Represents either `spritelist` or `sprite_picdata`
    if 'spritelist' in components:
      if self.sprite_picdata:
        fout = self._writer.get_writable('sprite_picdata', False)
        self._save_sprite_picdata(fout, self.sprite_picdata)
      else:
        fout = self._writer.get_writable('spritelist', False)
        self._save_spritelist(fout, self.spritelist, self.gfx[0].colorization)
    self._writer.close()
    return components

  def _save_nametable(self, fout, nametable):
    for y in range(NUM_BLOCKS_Y * 2):
      for x in range(NUM_BLOCKS_X * 2):
        nt = nametable[y][x]
        fout.write(bytearray([nt]))

  def _save_chr(self, fout, chr_set, select_chr_plane):
    if select_chr_plane in ['0','1']:
      fout.write(chr_set.to_bytes_select_plane(int(select_chr_plane)))
    elif select_chr_plane is None:
      fout.write(chr_set.to_bytes())
    else:
      raise RuntimeError('Unknown option for select-chr-plane: %s' %
                         (select_chr_plane,))

  def _save_palette(self, fout, palette_1, palette_2):
    self._write_single_palette(fout, palette_1, self._bg_color)
    self._write_single_palette(fout, palette_2, self._bg_color)

  def _save_attribute(self, fout, colorization):
    for attr_y in range(NUM_BLOCKS_Y // 2 + 1):
      for attr_x in range(NUM_BLOCKS_X // 2):
        block_y = attr_y * 2
        block_x = attr_x * 2
        y = block_y * 2
        x = block_x * 2
        p0 = colorization[y + 0][x + 0]
        p1 = colorization[y + 0][x + 2]
        p2 = colorization[y + 2][x + 0] if block_y + 1 < NUM_BLOCKS_Y else 0
        p3 = colorization[y + 2][x + 2] if block_y + 1 < NUM_BLOCKS_Y else 0
        attr = p0 + (p1 << 2) + (p2 << 4) + (p3 << 6)
        fout.write(to_byte(attr))

  def _save_spritelist(self, fout, spritelist, sprite_palettes):
    n = 0
    for y_pos, tile, attr, x_pos in spritelist:
      fout.write(to_byte(y_pos))
      fout.write(to_byte(tile))
      fout.write(to_byte(attr))
      fout.write(to_byte(x_pos))
      n += 1
    fout.write(to_byte(0xff))

  def _save_sprite_picdata(self, fout, sprite_picdata):
    text = json.dumps(sprite_picdata, indent=2)
    fout.write(text)

  def _get_bg_color(self, palette_1, palette_2):
    bg_color = None
    if palette_1:
      bg_color = palette_1.bg_color
    if palette_2:
      if bg_color and bg_color != palette_2.bg_color:
        # TODO: Add test.
        raise errors.PaletteInconsistentError(bg_color, palette_2.bg_color)
      bg_color = palette_2.bg_color
    return bg_color

  def _get_enabled_components(self, config):
    components = set()
    if not config.is_sprite and not config.is_locked_tiles:
      components.add('nametable')
    components.add('chr')
    components.add('palette')
    if not config.is_sprite:
      components.add('attribute')
    else:
      components.add('spritelist')
    return components

  def _write_single_palette(self, fout, palette, bg_color):
    if not palette:
      return
    for i in range(4):
      palette_option = palette.get(i)
      if palette_option is None:
        palette_option = []
      for j in range(4):
        if j < len(palette_option):
          fout.write(to_byte(palette_option[j]))
        else:
          fout.write(to_byte(bg_color))

  def build_nt_inverter(self):
    """Build a table that maps tile numbers to lists of positions."""
    nametable = self.gfx[0].nametable
    lookup = collections.defaultdict(list)
    for y in range(NUM_BLOCKS_Y * 2):
      for x in range(NUM_BLOCKS_X * 2):
        lookup[nametable[y][x]].append([y,x])
    return lookup

  def get_bytes(self, role):
    if role == 'nametable':
      nametable = self.gfx[0].nametable
      bytes = bytearray()
      for y in range(30):
        bytes += bytearray(nametable[y])
      return bytes
    elif role == 'attribute':
      colorization = self.gfx[0].colorization
      bytes = bytearray()
      for attr_y in range(NUM_BLOCKS_Y // 2 + 1):
        for attr_x in range(NUM_BLOCKS_X // 2):
          block_y = attr_y * 2
          block_x = attr_x * 2
          y = block_y * 2
          x = block_x * 2
          p0 = colorization[y  ][x  ]
          p1 = colorization[y  ][x+2]
          p2 = colorization[y+2][x  ] if block_y + 1 < NUM_BLOCKS_Y else 0
          p3 = colorization[y+2][x+2] if block_y + 1 < NUM_BLOCKS_Y else 0
          attr = p0 + (p1 << 2) + (p2 << 4) + (p3 << 6)
          bytes.append(attr)
      return bytes
    elif role == 'palette':
      if self._bg_color is None:
        self._bg_color = self._get_bg_color(self.palette_nt, self.palette_spr)
      bytes = bytearray()
      if self.palette_nt:
        bytes += self.palette_nt.to_bytes()
        bytes += bytearray([self._bg_color] * (0x10 - len(bytes)))
      else:
        bytes += bytearray([self._bg_color] * 0x10)
      if self.palette_spr:
        bytes += self.palette_spr.to_bytes()
        bytes += bytearray([self._bg_color] * (0x20 - len(bytes)))
      else:
        bytes += bytearray([self._bg_color] * 0x10)
      return bytes
    elif role == 'chr':
      bytes = self.chr_set.to_bytes()
      bytes += bytearray([0] * (0x2000 - len(bytes)))
      return bytes
    else:
      raise RuntimeError('Unknown role %s' % role)
