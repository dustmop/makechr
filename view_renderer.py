from PIL import Image, ImageDraw
from constants import *
import os
import rgb


GRAY_COLOR = (64, 64, 64)


class ViewRenderer(object):
  def __init__(self):
    self.img = None
    self.draw = None
    self.font = None

  def create_file(self, outfile, width, height, color=None):
    if color is None:
      color = GRAY_COLOR
    self.img = Image.new('RGB', (width, height), color)
    self.draw = ImageDraw.Draw(self.img)
    self.outfile = outfile

  def save_file(self):
    self.img.save(self.outfile)

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
    i = block_y * 16
    j = block_x * 16
    offsets = [[ 0, 0,15,15],
               [ 8, 1,15, 7],
               [ 1, 8, 7,15],
               [ 8, 8,15,15]]
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

  def draw_square(self, tile_y, tile_x, count):
    i = tile_y * 8
    j = tile_x * 8
    color = self.count_to_color(count)
    if not color:
      color = (0x00, 0x00, 0x00)
    self.draw.rectangle([j+0,i+0,j+8,i+8], color)

  def draw_empty_block(self, block_y, block_x):
    i = block_y * 16
    j = block_x * 16
    self.draw.rectangle([j+0,i+0,j+16,i+16], (0,0,0,255))

  def draw_nt_value(self, tile_y, tile_x, nt):
    upper = self.font[nt / 16]
    lower = self.font[nt % 16]
    # Left digit (upper nibble).
    self.img.paste(upper, [tile_x*16+1,tile_y*16+2,tile_x*16+8,tile_y*16+13])
    # Right digit (lower nibble).
    self.img.paste(lower, [tile_x*16+8,tile_y*16+2,tile_x*16+15,tile_y*16+13])

  def is_empty_block(self, y, x, artifacts, cmanifest, bg):
    # TODO: This could be much more efficient. Perhaps add a value to artifacts
    # that determines whether the tile / block is empty.
    cid_0 = artifacts[y * 2  ][x * 2  ][ARTIFACT_CID]
    cid_1 = artifacts[y * 2  ][x * 2+1][ARTIFACT_CID]
    cid_2 = artifacts[y * 2+1][x * 2  ][ARTIFACT_CID]
    cid_3 = artifacts[y * 2+1][x * 2+1][ARTIFACT_CID]
    if cid_0 == cid_1 and cid_1 == cid_2 and cid_2 == cid_3:
      color_needs = cmanifest.get(cid_0)
      if color_needs == [bg, None, None, None]:
        return True
    return False

  # create_colorization_view
  #
  # Create an image that shows which palette is used for each block.
  #
  # outfile: Filename to output the view to.
  # artifacts: Artifacts created by the image processor.
  # palette: The palette for the image.
  def create_colorization_view(self, outfile, artifacts, palette, cmanifest):
    self.create_file(outfile, 256, 240)
    for y in xrange(NUM_BLOCKS_Y):
      for x in xrange(NUM_BLOCKS_X):
        pid = artifacts[y * 2][x * 2][ARTIFACT_PID]
        poption = palette.get(pid)
        if self.is_empty_block(y, x, artifacts, cmanifest, poption[0]):
          self.draw_empty_block(y, x)
          continue
        self.draw_block(y, x, poption)
    self.save_file()

  # create_resuse_view
  #
  # Create an image that shows which tiles are reused, color coded by how many
  # times they appear.
  #
  # outfile: Filename to output the view to.
  # artifacts: Artifacts created by the image processor.
  # nt_count: Dict mapping nametable values to number of times.
  def create_reuse_view(self, outfile, artifacts, nt_count):
    self.create_file(outfile, 256, 240)
    for block_y in xrange(NUM_BLOCKS_Y):
      for block_x in xrange(NUM_BLOCKS_X):
        for i in range(2):
          for j in range(2):
            y = block_y * 2 + i
            x = block_x * 2 + j
            nt = artifacts[y][x][ARTIFACT_NT]
            self.draw_square(y, x, nt_count[nt])
    self.save_file()

  # create_palette_view
  #
  # Create an image that shows the palette.
  #
  # outfile: Filename to output the palette to.
  # palette: The palette to show.
  def create_palette_view(self, outfile, palette):
    self.create_file(outfile, 168, 24)
    for i in xrange(4):
      poption = palette.get(i)
      self.draw_poption(i, poption)
    self.save_file()

  # create_nametable_view
  #
  # Create an image that shows nametable values for each tile.
  #
  # outfile: Filename to output the view to.
  # artifacts: Artifacts created by the image processor.
  def create_nametable_view(self, outfile, artifacts):
    self.load_nt_font()
    self.create_file(outfile, 512, 480, (255, 255, 255))
    for block_y in xrange(NUM_BLOCKS_Y):
      for block_x in xrange(NUM_BLOCKS_X):
        for i in range(2):
          for j in range(2):
            y = block_y * 2 + i
            x = block_x * 2 + j
            nt = artifacts[y][x][ARTIFACT_NT]
            if nt != 0:
              self.draw_nt_value(y, x, nt)
    self.save_file()

  # create_error_view
  #
  # Create an image that shows the errors.
  #
  # outfile: Filename to output the error display to.
  # img: Input pixel art image.
  # errs: List of errors created by processor.
  def create_error_view(self, outfile, img, errs):
    width = 256 * 2
    height = 240 * 2
    tile_grid_color = (0x20,0x80,0x20)
    block_grid_color = (0x00,0xf0,0x00)
    error_grid_color = (0xf0, 0x20, 0x20)
    error_grid_color2 = (0xc0, 0x00, 0x00)
    self.img = img.resize((width, height), Image.NEAREST).convert('RGB')
    self.draw = ImageDraw.Draw(self.img)
    self.outfile = outfile
    # Draw tile grid.
    for col in xrange(16):
      self.draw.line([col*32+16, 0, col*32+16, height], tile_grid_color)
    for row in xrange(15):
      self.draw.line([0, row*32+16, width, row*32+16], tile_grid_color)
    # Draw block grid.
    for col in xrange(1, 16):
      self.draw.line([col*32, 0, col*32, height], block_grid_color)
    for row in xrange(1, 15):
      self.draw.line([0, row*32, width, row*32], block_grid_color)
    # Draw errors.
    for e in errs:
      if not (getattr(e, 'tile_y', None) and getattr(e, 'tile_x', None)):
        continue
      y = e.tile_y * 8 * 2
      x = e.tile_x * 8 * 2
      # Inner line.
      self.draw.line([   x,    y, x+16,    y], error_grid_color)
      self.draw.line([   x,    y,    x, y+16], error_grid_color)
      self.draw.line([   x, y+16, x+16, y+16], error_grid_color)
      self.draw.line([x+16,    y, x+16, y+16], error_grid_color)
      # Outer line.
      self.draw.line([ x-1,  y-1, x+17,  y-1], error_grid_color2)
      self.draw.line([ x-1,  y-1,  x-1, y+17], error_grid_color2)
      self.draw.line([ x-1, y+17, x+17, y+17], error_grid_color2)
      self.draw.line([x+17,  y-1, x+17, y+17], error_grid_color2)
    self.save_file()

  # create_grid_view
  #
  # Create an image that shows the blocks and tiles.
  #
  # outfile: Filename to output the grid view to.
  # img: Input pixel art image.
  def create_grid_view(self, outfile, img):
    width, height = (512, 480)
    tile_grid_color = (0x20,0x80,0x20)
    block_grid_color = (0x00,0xf0,0x00)
    self.img = img.resize((width, height), Image.NEAREST).convert('RGB')
    self.draw = ImageDraw.Draw(self.img)
    self.outfile = outfile
    # Draw tile grid.
    for col in xrange(16):
      self.draw.line([col*32+16, 0, col*32+16, height], tile_grid_color)
    for row in xrange(15):
      self.draw.line([0, row*32+16, width, row*32+16], tile_grid_color)
    # Draw block grid.
    for col in xrange(1, 16):
      self.draw.line([col*32, 0, col*32, height], block_grid_color)
    for row in xrange(1, 15):
      self.draw.line([0, row*32, width, row*32], block_grid_color)
    self.save_file()

