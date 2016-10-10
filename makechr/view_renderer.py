from PIL import Image, ImageDraw
from constants import *
import math
import os
import rgb


GRAY_COLOR = (64, 64, 64)
ERROR_GRID_COLOR  = (0xf0, 0x20, 0x20)
ERROR_GRID_COLOR2 = (0xf0, 0x80, 0x80)
GRAY_PALETTE = [225, 150, 75, 0]
SCALE_FACTOR = 2


class ViewRenderer(object):
  def __init__(self):
    self.img = None
    self.draw = None
    self.font = None
    self.empty_tile = None

  def create_file(self, outfile, width, height, color=None):
    if color is None:
      color = GRAY_COLOR
    self.img = Image.new('RGB', (width, height), color)
    self.draw = ImageDraw.Draw(self.img)
    self.outfile = outfile

  def save_file(self):
    self.img.save(self.outfile)

  def determine_empty_tile(self, ppu_memory):
    self.empty_tile = None
    chr_page = ppu_memory.chr_page
    for i in xrange(chr_page.size()):
      if chr_page.get(i).is_empty():
        self.empty_tile = i
        return

  def to_tuple(self, value):
    r = value / (256 * 256)
    g = (value / 256) % 256
    b = value % 256
    return (r,g,b)

  def palette_option_to_colors(self, poption):
    return [self.to_tuple(rgb.RGB_COLORS[p]) for p in poption]

  def count_to_color(self, count):
    COLORS = [None,               # unused
              None,               # clear
              (0x00, 0x80, 0x00), # dark green
              (0x00, 0xff, 0x00), # light green
              (0x00, 0xff, 0xff), # light blue
              (0x00, 0x00, 0xff), # blue
              (0x80, 0x00, 0x80), # dark purple
              (0xff, 0x00, 0xff), # light purple
              (0xff, 0x40, 0x40), # red
              (0xff, 0x80, 0x00), # orange
              (0xff, 0xff, 0x00)] # yellow
    if count < len(COLORS):
      return COLORS[count]
    return (0xff, 0xff, 0xff)

  def resource(self, rel):
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), rel)

  def load_nt_font(self):
    self.font = [None] * 16
    font_img = Image.open(self.resource('res/nt_font.png'))
    for n in range(16):
      self.font[n] = font_img.crop([n*7,0,n*7+7,11])
    font_img.close()

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

  def draw_chr(self, tile, tile_y, tile_x):
    s = self.scale * 8
    t = self.scale
    for y in xrange(8):
      for x in xrange(8):
        base_y = tile_y * (s + 1)
        base_x = tile_x * (s + 1)
        pixel = tile.get_pixel(y, x)
        gray = GRAY_PALETTE[pixel]
        self.draw.rectangle([base_x + x * t, base_y + y * t,
                             base_x + x * t + t - 1, base_y + y * t + t - 1],
                             (gray, gray, gray))

  def draw_square(self, tile_y, tile_x, count):
    s = self.scale * 8
    i = tile_y * s
    j = tile_x * s
    color = self.count_to_color(count)
    if not color:
      color = (0x00, 0x00, 0x00)
    self.draw.rectangle([j+0,i+0,j+s,i+s], color)

  def draw_empty_block(self, block_y, block_x, bg):
    s = self.scale * 8
    i = block_y * 2 * s
    j = block_x * 2 * s
    # TODO: Draw bg color instead.
    self.draw.rectangle([j+0,i+0,j+s*2,i+s*2], (0,0,0,255))

  def draw_nt_value(self, tile_y, tile_x, nt):
    s = self.scale * 8
    upper = self.font[nt / 16]
    lower = self.font[nt % 16]
    # Left digit (upper nibble).
    self.img.paste(upper, [tile_x*s+1,tile_y*s+3,tile_x*s+8,tile_y*s+14])
    # Right digit (lower nibble).
    self.img.paste(lower, [tile_x*s+8,tile_y*s+3,tile_x*s+15,tile_y*s+14])

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

  def create_colorization_view(self, outfile, ppu_memory):
    """Create an image that shows which palette is used for each block.

    outfile: Filename to output the view to.
    ppu_memory: Ppu memory containing colorization and palette.
    """
    self.scale = SCALE_FACTOR
    width, height = (256 * self.scale, 240 * self.scale)
    self.determine_empty_tile(ppu_memory)
    self.create_file(outfile, width, height)
    palette = ppu_memory.palette_nt
    # TODO: Support both graphics pages.
    colorization = ppu_memory.gfx_0.colorization
    for y in xrange(NUM_BLOCKS_Y):
      for x in xrange(NUM_BLOCKS_X):
        pid = colorization[y*2][x*2]
        poption = palette.get(pid)
        if self.is_empty_block(y, x, ppu_memory.gfx_0.nametable):
          self.draw_empty_block(y, x, poption[0])
        else:
          self.draw_block(y, x, poption)
    self.save_file()

  def create_reuse_view(self, outfile, ppu_memory, nt_count):
    """Create an image that shows tile reuse.

    Create an image that shows which tiles are reused, color coded by how many
    times they appear.

    outfile: Filename to output the view to.
    ppu_memory: Ppu memory containing nametable.
    nt_count: Dict mapping nametable values to number of times.
    """
    self.scale = SCALE_FACTOR
    width, height = (256 * self.scale, 240 * self.scale)
    self.create_file(outfile, width, height)
    # TODO: Support both graphics pages.
    nametable = ppu_memory.gfx_0.nametable
    for block_y in xrange(NUM_BLOCKS_Y):
      for block_x in xrange(NUM_BLOCKS_X):
        for i in range(2):
          for j in range(2):
            y = block_y * 2 + i
            x = block_x * 2 + j
            nt = nametable[y][x]
            self.draw_square(y, x, nt_count[nt])
    self.save_file()

  def create_palette_view(self, outfile, ppu_memory):
    """Create an image that shows the palette.

    outfile: Filename to output the palette to.
    ppu_memory: Ppu memory containing palette.
    """
    self.create_file(outfile, 168, 24)
    # TODO: Support sprite palettes.
    palette = ppu_memory.palette_nt
    for i in xrange(4):
      poption = palette.get(i)
      self.draw_poption(i, poption)
    self.save_file()

  def create_nametable_view(self, outfile, ppu_memory):
    """Create an image that shows nametable values for each tile.

    outfile: Filename to output the view to.
    ppu_memory: Ppu memory containing nametable.
    """
    self.scale = SCALE_FACTOR
    width, height = (256 * self.scale, 240 * self.scale)
    self.load_nt_font()
    self.determine_empty_tile(ppu_memory)
    self.create_file(outfile, width, height, (255, 255, 255))
    # TODO: Support both graphics pages.
    nametable = ppu_memory.gfx_0.nametable
    for block_y in xrange(NUM_BLOCKS_Y):
      for block_x in xrange(NUM_BLOCKS_X):
        for i in range(2):
          for j in range(2):
            y = block_y * 2 + i
            x = block_x * 2 + j
            nt = nametable[y][x]
            if nt != self.empty_tile:
              self.draw_nt_value(y, x, nt)
    self.draw_grid(width, height)
    self.save_file()

  def create_chr_view(self, outfile, ppu_memory):
    """Create an image that shows chr tiles.

    Create an image that shows chr tiles in a 16x16 grid layout. Has an
    abnormal size, which is the size of a chr tile, times 16, plus a 1-pixel
    border between each tile.

    outfile: Filename to output the view to.
    ppu_memory: Ppu memory containing chr.
    """
    self.scale = SCALE_FACTOR
    s = self.scale * 8
    chr_page = ppu_memory.chr_page
    rows = int(math.ceil(chr_page.size() / 16.0))
    width, height = (16 * (s + 1) - 1, rows * (s + 1) - 1)
    self.create_file(outfile, width, height, (255, 255, 255))
    for k, tile in enumerate(chr_page.tiles):
      tile_y = k / 16
      tile_x = k % 16
      self.draw_chr(tile, tile_y, tile_x)
    self.save_file()

  def create_error_view(self, outfile, img, errs):
    """Create an image that shows the errors.

    outfile: Filename to output the error display to.
    img: Input pixel art image.
    errs: List of errors created by processor.
    """
    self.scale = SCALE_FACTOR
    width, height = (256 * self.scale, 240 * self.scale)
    self.img = img.resize((width, height), Image.NEAREST).convert('RGB')
    self.draw = ImageDraw.Draw(self.img)
    self.outfile = outfile
    self.draw_grid(width, height)
    s = self.scale * 8
    # Draw errors.
    for e in errs:
      if (not getattr(e, 'tile_y', None) is None and
          not getattr(e, 'tile_x', None) is None):
        y = e.tile_y * 8 * self.scale
        x = e.tile_x * 8 * self.scale
        self.draw_error(y, x, s)
      elif (not getattr(e, 'block_y', None) is None and
            not getattr(e, 'block_x', None) is None):
        y = e.block_y * 16 * self.scale
        x = e.block_x * 16 * self.scale
        self.draw_error(y, x, s * 2)
    self.save_file()

  def create_grid_view(self, outfile, img):
    """Create an image that shows the blocks and tiles.

    outfile: Filename to output the grid view to.
    img: Input pixel art image.
    """
    self.scale = SCALE_FACTOR
    width, height = (256 * self.scale, 240 * self.scale)
    self.img = img.resize((width, height), Image.NEAREST).convert('RGB')
    self.draw = ImageDraw.Draw(self.img)
    self.outfile = outfile
    self.draw_grid(width, height)
    self.save_file()

