from PIL import Image, ImageDraw
from constants import *
import math
import os
import rgb


pkg_resources = None


GRAY_COLOR = (64, 64, 64)
ERROR_GRID_COLOR  = (0xf0, 0x20, 0x20)
ERROR_GRID_COLOR2 = (0xf0, 0x80, 0x80)
GRAY_PALETTE = [30, 105, 180, 255]
LEGACY_GRAY_PALETTE = [225, 150, 75, 0]
SCALE_FACTOR = 2


REUSE_COLORS = [(0x40, 0x40, 0x40), # dark grey (common)
                (0xff, 0xff, 0xff), # white (unique)
                (0xff, 0xff, 0x00), # yellow
                (0xff, 0xaa, 0x00), # light orange
                (0x80, 0xff, 0x00), # light green
                (0x00, 0xff, 0xff), # light blue
                (0xff, 0x00, 0xff), # light purple
                (0xff, 0x00, 0x00), # red
                (0x00, 0x80, 0x00), # dark green
                (0x00, 0x00, 0xff), # blue
                (0x80, 0x00, 0x80)] # dark purple


LEGACY_REUSE_COLORS = [(0xff, 0xff, 0xff), # white (common)
                       (0x00, 0x00, 0x00), # black (unique)
                       (0x00, 0x80, 0x00), # dark green
                       (0x00, 0xff, 0x00), # light green
                       (0x00, 0xff, 0xff), # light blue
                       (0x00, 0x00, 0xff), # blue
                       (0x80, 0x00, 0x80), # dark purple
                       (0xff, 0x00, 0xff), # light purple
                       (0xff, 0x40, 0x40), # red
                       (0xff, 0x80, 0x00), # orange
                       (0xff, 0xff, 0x00)] # yellow


class ViewRenderer(object):
  def __init__(self, is_legacy=False, scale=None):
    self.img = None
    self.draw = None
    self.font = None
    self.empty_tile = None
    self.is_legacy = is_legacy
    self.scale = scale or SCALE_FACTOR

  def create_file(self, outfile, width, height, color=None):
    if color is None:
      color = GRAY_COLOR
    self.img = Image.new('RGB', (width, height), color)
    self.draw = ImageDraw.Draw(self.img)
    self.outfile = outfile

  def save_file(self):
    if self.outfile:
      self.img.save(self.outfile)
    return self.img

  def determine_empty_tile(self, ppu_memory):
    self.empty_tile = None
    chr_set = ppu_memory.chr_set
    for i in xrange(chr_set.size()):
      if chr_set.get(i).is_empty():
        self.empty_tile = i
        return

  def to_tuple(self, value):
    r = value / (256 * 256)
    g = (value / 256) % 256
    b = value % 256
    return (r,g,b)

  def palette_option_to_colors(self, poption):
    return [self.to_tuple(rgb.RGB_COLORS[p]) for p in poption]

  def reuse_count_to_color(self, count, scheme):
    table = REUSE_COLORS if scheme != 'legacy' else LEGACY_REUSE_COLORS
    if count == 0:
      raise errors.UnknownLogicFailure('reuse number should not be 0')
    if count < len(table):
      return table[count]
    # Common is represented by index 0.
    return table[0]

  def load_nt_font(self):
    global pkg_resources
    if not pkg_resources:
      import pkg_resources
    self.font = [None] * 16
    if not self.is_legacy:
      w = self.font_width = 3
      h = self.font_height = 5
      rel = 'res/nt_tiny.png'
    else:
      w = self.font_width = 7
      h = self.font_height = 11
      rel = 'res/nt_font.png'
    font_img = Image.open(pkg_resources.resource_stream('makechr', rel))
    for n in range(16):
      self.font[n] = font_img.crop([n*w,0,n*w+w,h])
    font_img.close()

  def replace_color(self, img, old, new):
    img = img.copy()
    pixels = img.load()
    old_color = (old / 0x10000, (old / 0x100) % 0x100, old % 0x100)
    new_color = (new / 0x10000, (new / 0x100) % 0x100, new % 0x100)
    (cols, rows) = img.size
    for y in xrange(rows):
      for x in xrange(cols):
        tuple = pixels[x, y]
        curr_color = (tuple[0], tuple[1], tuple[2])
        if curr_color == old_color:
          pixels[x, y] = new_color
    return img

  def color_and_scale(self, img, old, new):
    img = self.replace_color(img, old, new)
    if self.scale != 1:
      img = img.resize((img.size[0] * self.scale, img.size[1] * self.scale),
                       Image.NEAREST)
    return img

  def draw_block(self, block_y, block_x, poption):
    s = self.scale * 8
    i = block_y * 2 * s
    j = block_x * 2 * s
    # Borders for the individual colors in the palette block.
    # 0) Background color, fills entire block.
    # 1) Color 1, upper-right with a 1-pixel border, squatter than a square.
    # 2) Color 2, lower-left with a 1-pixel border, thinner than a square.
    # 3) Color 3, lower-right, true square.
    offsets = [[ 0, 0, s*2-1, s*2-1],
               [ s, 1, s*2-1,   s-1],
               [ 1, s,   s-1, s*2-1],
               [ s, s, s*2-1, s*2-1]]
    color = self.palette_option_to_colors(poption)
    for k, c in enumerate(color):
      f = offsets[k]
      self.draw.rectangle([j+f[0],i+f[1],j+f[2],i+f[3]], c)

  def draw_poption(self, n, poption):
    if not poption:
      return
    j = n * 5 * 8 + 8
    offsets = [[ 0, 8, 7,15],
               [ 8, 8,15,15],
               [16, 8,23,15],
               [24, 8,31,15]]
    color = self.palette_option_to_colors(poption)
    for k, c in enumerate(color):
      f = offsets[k]
      self.draw.rectangle([j+f[0],f[1],j+f[2],f[3]], c)

  def draw_poption_square(self, n, poption):
    if not poption:
      return
    j = n * 3 * 8 + 8
    offsets = [[0,  8,  7, 15],
               [8,  8, 15, 15],
               [0, 16,  7, 23],
               [8, 16, 15, 23]]
    color = self.palette_option_to_colors(poption)
    for k, c in enumerate(color):
      f = offsets[k]
      self.draw.rectangle([j+f[0],f[1],j+f[2],f[3]], c)

  def draw_chr(self, tile, tile_y, tile_x, scheme):
    s = self.scale * 8
    t = self.scale
    if scheme != 'legacy':
      s *= 2
      t *= 2
    for y in xrange(8):
      for x in xrange(8):
        base_y = tile_y * (s + 1)
        base_x = tile_x * (s + 1)
        pixel = tile.get_pixel(y, x)
        if scheme != 'legacy':
          gray = GRAY_PALETTE[pixel]
        else:
          gray = LEGACY_GRAY_PALETTE[pixel]
        self.draw.rectangle([base_x + x * t, base_y + y * t,
                             base_x + x * t + t - 1, base_y + y * t + t - 1],
                             (gray, gray, gray))

  def draw_reuse_square(self, tile_y, tile_x, count, scheme):
    s = self.scale * 8
    i = tile_y * s
    j = tile_x * s
    color = self.reuse_count_to_color(count, scheme)
    self.draw.rectangle([j+0,i+0,j+s,i+s], color)

  def draw_empty_tile(self, tile_y, tile_x):
    s = self.scale * 8
    i = tile_y * s
    j = tile_x * s
    color = (0x00, 0x00, 0x00)
    self.draw.rectangle([j+0,i+0,j+s,i+s], color)

  def draw_empty_block(self, block_y, block_x, bg):
    s = self.scale * 8
    i = block_y * 2 * s
    j = block_x * 2 * s
    # TODO: Draw bg color instead.
    self.draw.rectangle([j+0,i+0,j+s*2,i+s*2], (0,0,0,255))

  def draw_nt_value(self, tile_y, tile_x, nt):
    try:
      if self.is_legacy:
        s = self.scale * 8
        x = tile_x * s + 1
        y = tile_y * s + 3
        w = 7
        h = 11
        offset = 7
        upper = self.font[nt / 16]
        lower = self.font[nt % 16]
      else:
        s = self.scale * 8
        x = tile_x * s + 1
        y = tile_y * s + 1
        w = self.font_width * self.scale
        h = self.font_height * self.scale
        offset = int(3.5 * self.scale)
        upper = self.color_and_scale(self.font[nt / 16], 0xffffff, 0xc0c0c0)
        lower = self.color_and_scale(self.font[nt % 16], 0xffffff, 0x909090)
      # Left digit (upper nibble).
      self.img.paste(upper, [x, y, x + w, y + h])
      # Right digit (lower nibble).
      self.img.paste(lower, [x + offset, y, x + offset + w, y + h])
    except IndexError:
      pass

  def draw_error(self, y, x, sz):
    # Inner line.
    self.draw.line([   x,    y, x+sz,    y], ERROR_GRID_COLOR)
    self.draw.line([   x,    y,    x, y+sz], ERROR_GRID_COLOR)
    self.draw.line([   x, y+sz, x+sz, y+sz], ERROR_GRID_COLOR)
    self.draw.line([x+sz,    y, x+sz, y+sz], ERROR_GRID_COLOR)
    # Outer line.
    self.draw.line([   x-1,    y-1, x+sz+1,    y-1], ERROR_GRID_COLOR2)
    self.draw.line([   x-1,    y-1,    x-1, y+sz+1], ERROR_GRID_COLOR2)
    self.draw.line([   x-1, y+sz+1, x+sz+1, y+sz+1], ERROR_GRID_COLOR2)
    self.draw.line([x+sz+1,    y-1, x+sz+1, y+sz+1], ERROR_GRID_COLOR2)

  def is_empty_block(self, y, x, nametable):
    nt0 = nametable[y*2  ][x*2  ]
    nt1 = nametable[y*2  ][x*2+1]
    nt2 = nametable[y*2+1][x*2  ]
    nt3 = nametable[y*2+1][x*2+1]
    return all(e == self.empty_tile for e in [nt0, nt1, nt2, nt3])

  def draw_grid(self, width, height):
    s = self.scale * 8
    tile_grid_color = (0x20,0x80,0x20)
    block_grid_color = (0x00,0xf0,0x00)
    # Draw tile grid.
    for col in xrange(16):
      self.draw.line([col*2*s+s, 0, col*2*s+s, height], tile_grid_color)
    for row in xrange(15):
      self.draw.line([0, row*2*s+s, width, row*2*s+s], tile_grid_color)
    # Draw block grid.
    for col in xrange(1, 16):
      self.draw.line([col*2*s, 0, col*2*s, height], block_grid_color)
    for row in xrange(1, 15):
      self.draw.line([0, row*2*s, width, row*2*s], block_grid_color)

  def create_colorization_view(self, outfile, ppu_memory, is_sprite):
    """Create an image that shows which palette is used for each block.

    outfile: Filename to output the view to.
    ppu_memory: Ppu memory containing colorization and palette.
    is_sprite: Whether sprite mode or not.
    """
    width, height = (256 * self.scale, 240 * self.scale)
    self.determine_empty_tile(ppu_memory)
    self.create_file(outfile, width, height)
    if not is_sprite:
      palette = ppu_memory.palette_nt
    else:
      palette = ppu_memory.palette_spr
    # TODO: Support both graphics pages.
    colorization = ppu_memory.gfx[0].colorization
    for y in xrange(NUM_BLOCKS_Y):
      for x in xrange(NUM_BLOCKS_X):
        pid = colorization[y*2][x*2]
        poption = palette.get(pid)
        if self.is_empty_block(y, x, ppu_memory.gfx[0].nametable):
          self.draw_empty_block(y, x, poption[0])
        else:
          self.draw_block(y, x, poption)
    return self.save_file()

  def create_reuse_view(self, outfile, ppu_memory, nt_inverter):
    """Create an image that shows tile reuse.

    Create an image that shows which tiles are reused, color coded by how many
    times they appear.

    outfile: Filename to output the view to.
    ppu_memory: Ppu memory containing nametable.
    nt_inverter: Dict mapping nametable tiles to list of positions.
    """
    width, height = (256 * self.scale, 240 * self.scale)
    self.create_file(outfile, width, height, (0, 0, 0))
    scheme = 'legacy' if self.is_legacy else 'normal'
    # TODO: Support both graphics pages.
    nametable = ppu_memory.gfx[0].nametable
    for block_y in xrange(NUM_BLOCKS_Y):
      for block_x in xrange(NUM_BLOCKS_X):
        for i in range(2):
          for j in range(2):
            y = block_y * 2 + i
            x = block_x * 2 + j
            nt = nametable[y][x]
            if not self.is_legacy and nt == ppu_memory.empty_tile:
              self.draw_empty_tile(y, x)
            else:
              self.draw_reuse_square(y, x, len(nt_inverter[nt]), scheme)
    return self.save_file()

  def create_palette_view(self, outfile, ppu_memory, is_sprite):
    """Create an image that shows the palette.

    outfile: Filename to output the palette to.
    ppu_memory: Ppu memory containing palette.
    is_sprite: Whether sprite mode or not.
    """
    if self.is_legacy:
      self.create_file(outfile, 168, 24)
    else:
      self.create_file(outfile, 104, 32, (0xa0, 0xa0, 0xa0))
    if not is_sprite:
      palette = ppu_memory.palette_nt
    else:
      palette = ppu_memory.palette_spr
    for i in xrange(4):
      poption = palette.get(i)
      if self.is_legacy:
        self.draw_poption(i, poption)
      else:
        self.draw_poption_square(i, poption)
    return self.save_file()

  def create_nametable_view(self, outfile, ppu_memory):
    """Create an image that shows nametable values for each tile.

    outfile: Filename to output the view to.
    ppu_memory: Ppu memory containing nametable.
    """
    width, height = (256 * self.scale, 240 * self.scale)
    self.load_nt_font()
    self.determine_empty_tile(ppu_memory)
    bg_color = (0, 0, 0) if not self.is_legacy else (255, 255, 255)
    self.create_file(outfile, width, height, bg_color)
    # TODO: Support both graphics pages.
    nametable = ppu_memory.gfx[0].nametable
    for block_y in xrange(NUM_BLOCKS_Y):
      for block_x in xrange(NUM_BLOCKS_X):
        for i in range(2):
          for j in range(2):
            y = block_y * 2 + i
            x = block_x * 2 + j
            nt = nametable[y][x]
            if nt != self.empty_tile:
              self.draw_nt_value(y, x, nt)
    if self.is_legacy:
      self.draw_grid(width, height)
    return self.save_file()

  def create_chr_view(self, outfile, ppu_memory):
    """Create an image that shows chr tiles.

    Create an image that shows chr tiles in a 16x16 grid layout. Has an
    abnormal size, which is the size of a chr tile, times 16, plus a 1-pixel
    border between each tile.

    outfile: Filename to output the view to.
    ppu_memory: Ppu memory containing chr.
    """
    s = self.scale * 8
    if not self.is_legacy:
      s *= 2
    chr_set = ppu_memory.chr_set
    if self.is_legacy:
      rows = int(math.ceil(chr_set.size() / 16.0))
      color = (255, 255, 255)
    else:
      rows = 16
      color = (0, 0, 0)
    width, height = (16 * (s + 1) - 1, rows * (s + 1) - 1)
    self.create_file(outfile, width, height, color)
    scheme = 'legacy' if self.is_legacy else 'normal'
    for k, tile in enumerate(chr_set.tiles):
      tile_y = k / 16
      tile_x = k % 16
      self.draw_chr(tile, tile_y, tile_x, scheme)
    return self.save_file()

  def create_free_zone_view(self, outfile, img, ppu_memory):
    """Create an image that shows zones for free sprite traversal.

    outfile: Filename to output the error display to.
    img: Input pixel art image.
    ppu_memory: Ppu memory containing zones.
    """
    create = img.copy()
    draw = ImageDraw.Draw(create)
    for z in ppu_memory.zones:
      draw.rectangle(z.rect(), outline=(0xff,0,0))
    create.save(outfile)

  def create_error_view(self, outfile, img, errs, has_grid=True):
    """Create an image that shows the errors.

    outfile: Filename to output the error display to.
    img: Input pixel art image.
    errs: List of errors created by processor.
    has_grid: Whether to draw a grid on the image.
    """
    orig_wide, orig_high = img.size
    make_wide, make_high = (orig_wide * self.scale, orig_high * self.scale)
    self.img = img.resize((make_wide, make_high), Image.NEAREST).convert('RGB')
    self.draw = ImageDraw.Draw(self.img)
    self.outfile = outfile
    if has_grid:
      self.draw_grid(make_wide, make_high)
    s = self.scale * 8
    # Draw errors.
    for e in errs:
      if hasattr(e, 'list_blocks'):
        for block_y,block_x in e.list_blocks:
          y = block_y * 16 * self.scale
          x = block_x * 16 * self.scale
          self.draw_error(y, x, s * 2)
      if (getattr(e, 'tile_y', None) is not None and
          getattr(e, 'tile_x', None) is not None):
        y = e.tile_y * 8 * self.scale
        x = e.tile_x * 8 * self.scale
        self.draw_error(y, x, s)
      elif (getattr(e, 'block_y', None) is not None and
            getattr(e, 'block_x', None) is not None):
        y = e.block_y * 16 * self.scale
        x = e.block_x * 16 * self.scale
        self.draw_error(y, x, s * 2)
    return self.save_file()

  def create_grid_view(self, outfile, img):
    """Create an image that shows the blocks and tiles.

    outfile: Filename to output the grid view to.
    img: Input pixel art image.
    """
    width, height = (256 * self.scale, 240 * self.scale)
    self.img = img.resize((width, height), Image.NEAREST).convert('RGB')
    self.draw = ImageDraw.Draw(self.img)
    self.outfile = outfile
    self.draw_grid(width, height)
    return self.save_file()
