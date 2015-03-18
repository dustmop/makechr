from PIL import Image, ImageDraw
from constants import *
import rgb


GRAY_COLOR = (64, 64, 64)


class ViewRenderer(object):
  def __init__(self):
    self.img = None
    self.draw = None

  def create_file(self, outfile, width, height):
    self.img = Image.new('RGB', (width, height), GRAY_COLOR)
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
    return [self.to_tuple(rgb.RGB_COLORS[poption[n]]) for n in xrange(4)]

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

  def draw_block(self, block_y, block_x, poption):
    i = block_y * 16
    j = block_x * 16
    color = self.palette_option_to_colors(poption)
    self.draw.rectangle([j+0,i+0,j+15,i+15], color[0])
    self.draw.rectangle([j+8,i+1,j+15,i+ 8], color[1])
    self.draw.rectangle([j+1,i+8,j+ 8,i+15], color[2])
    self.draw.rectangle([j+8,i+8,j+15,i+15], color[3])

  def draw_poption(self, n, poption):
    if not poption:
      return
    j = n * 5 * 8 + 8
    color = self.palette_option_to_colors(poption)
    self.draw.rectangle([j+ 0,8,j+ 7,15], color[0])
    self.draw.rectangle([j+ 8,8,j+15,15], color[1])
    self.draw.rectangle([j+16,8,j+23,15], color[2])
    self.draw.rectangle([j+24,8,j+31,15], color[3])

  def draw_square(self, tile_y, tile_x, count):
    i = tile_y * 8
    j = tile_x * 8
    color = self.count_to_color(count)
    if not color:
      color = (0x00, 0x00, 0x00)
    self.draw.rectangle([j+0,i+0,j+8,i+8], color)

  # create_colorization_view
  #
  # Create an image that shows which palette is used for each block.
  #
  # outfile: Filename to output the view to.
  # artifacts: Artifacts created by the image processor.
  # palette: The palette for the image.
  def create_colorization_view(self, outfile, artifacts, palette):
    self.create_file(outfile, 256, 240)
    for y in xrange(NUM_BLOCKS_Y):
      for x in xrange(NUM_BLOCKS_X):
        pid = artifacts[y * 2][x * 2][ARTIFACT_PID]
        poption = palette.get(pid)
        self.draw_block(y, x, poption)
    self.save_file()

  # create_resuse_view
  #
  # Create an image that shows which tiles are reused, color coded by how many
  # times they appear.
  #
  # outfile: Filename to output the view to.
  # artifacts: Artifacts created by the image processor.
  # nt_count: TODO
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
    tile_grid_color = (0x50,0xa0,0x50)
    block_grid_color = (0x00,0xf0,0x00)
    error_grid_color = (0xf0, 0x20, 0x20)
    error_grid_color2 = (0xc0, 0x00, 0x00)
    self.img = img.resize((width, height), Image.NEAREST)
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
