from PIL import Image
import rgb


class PixelArtRenderer(object):
  def render(self, mem):
    img = Image.new('RGB', (256, 240), 'white')
    for y in xrange(30):
      for x in xrange(32):
        nt_num = mem.gfx[0].nametable[y][x]
        tile = mem.chr_set.get(nt_num)
        attr = mem.gfx[0].colorization[y & 0xfe][x & 0xfe]
        pal = mem.palette_nt.get(attr)
        pixels = self.create_pixels(tile, pal)
        img.paste(pixels, (x*8, y*8, x*8+8, y*8+8))
    return img

  def create_pixels(self, tile, pal):
    make = Image.new('RGB', (8, 8), 'white')
    pixels = make.load()
    for i in xrange(8):
      for j in xrange(8):
        nc = pal[tile.get_pixel(i, j)]
        col = rgb.RGB_COLORS[nc]
        pixels[j,i] = (col / 0x10000, (col / 0x100) % 0x100, col % 0x100)
    return make
