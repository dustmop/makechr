import chr_data
import errors
import image_processor
import outline_tracer
import rectilinear_coverage
import rgb
from PIL import Image, ImageDraw
import sys


if sys.version_info < (3,0):
  range = xrange


class DecomposeSpritesProcessor(image_processor.ImageProcessor):
  """Decompose sprites in an image, to build PPU memory and json."""

  def process_image(self, img, palette_text, bg_mask, bg_fill, debug_flags):
    self.img = img
    self.palette_text = palette_text
    self.bg_mask = bg_mask
    self.bg_fill = bg_fill
    self.pixels = self.img.load()
    self.width, self.height = self.img.size
    if not self.check_corners_for_fill():
      return
    self.traverse(debug_flags)

  def traverse(self, debug_flags):
    # General algorithm:
    # 1) Image -> []Region
    #      find the list of regions in the image, by tracing outlines
    # 2) Region -> []Coverage
    #      find the orthogonally convex rectilinear coverage of regions
    # 3) Coverage -> []Tile
    #      split coverage into tiles, resolving palette ambiguities

    # Find image outlines to build list of regions
    # Image -> []Region
    regions = self.find_regions_from_outlines()

    # Covert regions into coverages
    # Region -> []Coverage
    self.calc_coverages_from_regions(regions)

    # Sort the coverage collections from top to bottom, left to right
    self.sort_coverages_per_region(regions)

    # For debugging
    if debug_flags and debug_flags.get('anon_view'):
      self.display_coverage(regions, debug_flags['anon_view'], True)
    if debug_flags and debug_flags.get('steps_view'):
      self.display_coverage(regions, debug_flags['steps_view'], False)

    # Create the tiles, for each region
    # Coverage -> []Tile
    all_tiles, picdata = self.regions_to_tiles(regions)

    self.write_data(regions, all_tiles, picdata)

  def find_regions_from_outlines(self):
    ot = outline_tracer.OutlineTracer(self.height, self.width,
                                      self.pixel_is_clear)
    return ot.find_regions()

  def pixel_is_clear(self, y, x):
    nc = self.get_nes_color(y, x)
    return nc == self.bg_fill

  def calc_coverages_from_regions(self, regions):
    rc = rectilinear_coverage.RectilinearCoverage()
    rc.calc(regions)

  def sort_coverages_per_region(self, regions):
    for i in range(len(regions)):
      g = regions[i]
      accum = {}
      for r in g.rects:
        accum[str(r)] = r
      elems = accum.values()
      g.rects = sorted(elems, key=lambda r: (r.top, r.left))

  def display_coverage(self, regions, filename, anonymize):
    fill_color = 'black' if anonymize else 'white'
    target = Image.new('RGB', (512, 480), fill_color)
    orig = self.img.resize((self.width*2, self.height*2))
    if anonymize:
      pixels = orig.load()
      bg_color = pixels[0,0]
      for y in range(self.height*2):
        for x in range(self.width*2):
          if pixels[x,y] == bg_color:
            pixels[x,y] = (0,0,0)
          else:
            pixels[x,y] = (0xff,0xff,0xff)
    target.paste(orig)
    draw = ImageDraw.Draw(target)
    for step in range(4):
      for g in regions:
        for r in g.rects:
          if r.count == step:
            if anonymize:
              color = self.get_debug_color(-1)
            else:
              color = self.get_debug_color(r.count)
            if r.bot - r.top < 8 or r.right - r.left < 8:
              color = self.get_debug_color(-2)
            draw.rectangle([(r.left*2, r.top*2),
                            (r.right*2-1, r.bot*2-1)], outline=color)
    del draw
    target.save(filename)

  def get_debug_color(self, count):
    if count == -2:
      return (0xa0, 0xa0, 0xff)
    elif count == -1:
      return (0xff, 0x00, 0x00)
    elif count == 0:
      return (0x80, 0x00, 0x00)
    elif count == 1:
      return (0xf0, 0x20, 0x00)
    elif count == 2:
      return (0xf0, 0x80, 0x00)
    elif count == 3:
      return (0xf0, 0xf0, 0x00)
    raise RuntimeError('Not found: %r' % count)

  def regions_to_tiles(self, regions):
    # Collect tiles used by all regions.
    all_tiles = []
    picdata = []
    for g in regions:
      b_y = g.min_y
      b_x = g.min_x
      result = []
      for r in g.rects:
        # Handle this rectangles here, those that can't fit any tiles.
        if r.bot - r.top < 8 or r.right - r.left < 8:
          print(('Warning: ignoring rectangle at %sy,%sx, too '
                 'small to fit a tile') % (r.top, r.left))
          continue
        y = r.top
        while y < r.bot:
          x = r.left
          while x < r.right:
            tile = self.img.crop((x, y, x + 8, y + 8))
            all_tiles.append(tile)
            result.append(PicElem(len(all_tiles) - 1, y - b_y, x - b_x))
            # Increment X
            x += 8
            if r.right - x > 0 and r.right - x < 8:
              x -= 8 - (r.right - x)
          # Increment Y
          y += 8
          if r.bot - y > 0 and r.bot - y < 8:
            y -= 8 - (r.bot - y)
      picdata.append(result)
    return all_tiles, picdata

  def write_data(self, regions, all_tiles, picdata):
    self.image_y = self.image_x = 8
    self.mask_rgb_color = rgb.nc_to_rgb(self.bg_mask)
    # Create color_needs for each tile's non-overlapping pixels
    for i, g in enumerate(regions):
      b_y = g.min_y
      b_x = g.min_x
      picture = picdata[i]
      for j, elem in enumerate(picture):
        dots = self.calculate_overlap(elem, j, picture)
        tile = all_tiles[elem.tile_idx]
        self.pixels = tile.copy().load()
        self.apply_dots_overlap(dots, self.pixels)
        try:
          color_needs, dot_profile = self.process_tile(0, 0)
        except errors.CouldntConvertRGB as e:
          self._err.add(e)
          continue
        cid = self._color_manifest.id(color_needs)
        elem.cid = cid
    self._needs_provider = self._color_manifest
    # Calculate the palette
    pal = None
    if self.palette_text:
      pal = self.parse_palette(self.palette_text, self.bg_mask)
    if not pal:
      pal = self.make_palette(self.bg_mask, True)
    if self._err.has():
      return
    # Set palette
    self._ppu_memory.palette_spr = pal
    # Create chr and picdata
    result = []
    chrdata_cache = {}
    for i, _ in enumerate(regions):
      accum = []
      for _, elem in enumerate(picdata[i]):
        tile_pixels = all_tiles[elem.tile_idx]
        color_needs = self._color_manifest.at(elem.cid)
        try:
          (pid, popt) = pal.select(color_needs)
        except IndexError:
          self._err.add(errors.PaletteNoChoiceError(elem.y, elem.x,
                                                    color_needs))
          continue
        tile = self.build_tile_from_pixels_ignoring_unknown(tile_pixels, popt)
        key = str(tile)
        if key in chrdata_cache:
          chr_num, flips = chrdata_cache[key]
        else:
          chr_num = self._ppu_memory.chr_set.add(tile)
          flips = 0
          self.assign_tile_flips(tile, [chr_num], chrdata_cache)
        accum.append({'y': elem.y, 'x': elem.x, 'attr': flips | pid,
                      'tile': chr_num})
      g = regions[i]
      result.append({'top': g.min_y, 'left': g.min_x,
                     'bottom': g.max_y, 'right': g.max_x,
                     'elems': accum})
    self._ppu_memory.sprite_picdata = result

  def calculate_overlap(self, elem, j, all_pic):
    dots = [0] * 64
    for k, other in enumerate(all_pic):
      if j == k:
        continue
      y_offset = other.y - elem.y
      x_offset = other.x - elem.x
      if y_offset < -7 or y_offset > 7 or x_offset < -7 or x_offset > 7:
        continue
      for a in range(8):
        for b in range(8):
          y = a + y_offset
          x = b + x_offset
          if y in range(0, 8) and x in range(0, 8):
            dots[y*8 + x] += 1
    return dots

  def apply_dots_overlap(self, dots, pixels):
    for y in range(8):
      for x in range(8):
        if dots[y*8 + x] > 0:
          pixels[x,y] = self.mask_rgb_color

  def tile_palette_fault(self, tile_y, tile_x):
    # TODO: Record failed colors, use to reconstruct overlapping colors.
    return 0

  def add_error(self, e):
    self._err.add(e)

  def build_tile_from_pixels_ignoring_unknown(self, tile_pixels, popt):
    pixels = tile_pixels.load()
    tile = chr_data.ChrTile()
    for row in range(8):
      for col in range(8):
        i = row * 8 + col
        p = pixels[col, row]
        color_val = (p[0] << 16) + (p[1] << 8) + p[2]
        if color_val in rgb.RGB_XLAT:
          nc = rgb.RGB_XLAT[color_val]
        else:
          nc = self.components_to_nescolor(p[0], p[1], p[2])
          if nc == -1:
            raise errors.CouldntConvertRGB(p, tile_y, tile_x, i, j)
        try:
          val = popt.index(nc)
        except ValueError:
          val = 0
        tile.put_pixel(row, col, val)
    return tile

  def check_corners_for_fill(self):
    top_left  = self.pixels[0,0]
    top_right = self.pixels[self.width - 1, 0]
    bot_left  = self.pixels[0, self.height - 1]
    bot_right = self.pixels[self.width - 1, self.height - 1]
    if top_left == top_right == bot_left == bot_right:
      try:
        nc = self.get_nes_color(0, 0)
        if nc != self.bg_fill:
          raise errors.PaletteBackgroundFillColorSeemsWrong(nc, self.bg_fill)
      except errors.PaletteBackgroundFillColorSeemsWrong as e:
        self._err.add(e)
        return False
    else:
      print('Warning: inconsistent colors in corners')
    return True


class PicElem(object):
  def __init__(self, tile_idx, y, x):
    self.tile_idx = tile_idx
    self.y = y
    self.x = x
    self.cid = None
