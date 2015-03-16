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
