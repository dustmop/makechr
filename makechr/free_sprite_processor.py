import collections
import image_processor
import ppu_memory
import rgb


NULL = 0xff


class Edge(object):
  def __init__(self, left, right):
    self.left = left
    self.right = right

  def __repr__(self):
    return '<Edge L=%s R=%s>' % (self.left, self.right)


class Region(object):
  def __init__(self, top, left, right, bottom):
    self.top = top
    self.left = left
    self.right = right
    self.bottom = bottom

  def __repr__(self):
    return '<Region T=%s L=%s R=%s B=%s>' % (
      self.top, self.left, self.right, self.bottom)


class FreeSpriteProcessor(image_processor.ImageProcessor):
  """Converts free sprites image into data structures of the PPU's memory."""

  def __init__(self):
    image_processor.ImageProcessor.__init__(self)
    self._interest = {}

  def process_image(self, img, palette_text, bg_color_look, bg_color_fill):
    """Process free sprites image, creating the ppu_memory it represents.

    The image represents the entire screen, and is mostly filled with
    bg_color_fill. Anywhere that contains other pixel data is considered to be
    made of sprites. Those sprites are located, treated as tiles, and processed
    to be converted into PPU memory.

    img: Pixel art image.
    palette_text: Optional string representing a palette to be parsed.
    bg_color_look: Background color usable in existing free sprite tiles.
    bg_color_fill: Background color which fills up the outside space.
    """
    self.load_image(img)
    config = ppu_memory.PpuMemoryConfig(is_sprite=True, is_locked_tiles=False)
    # Scan the image, find corners of each tile based upon region merging.
    self._find_region_corners(bg_color_fill)
    # Collect artifacts, each of which is a corner with color and dot ids.
    artifacts = []
    for corner_y, corner_x in self._corners:
      (color_needs, dot_profile) = self.process_tile(
        corner_y / 8, corner_x / 8, corner_y % 8, corner_x % 8)
      cid = self._color_manifest.id(color_needs)
      did = self._dot_manifest.id(dot_profile)
      artifacts.append([corner_y, corner_x, cid, did])
    self._needs_provider = self._color_manifest
    # Build the palette.
    pal = self.make_palette(palette_text, bg_color_look, True)
    # Build the PPU memory.
    for corner_y, corner_x, cid, did in artifacts:
      color_needs = self._color_manifest.at(cid)
      (pid, palette_option) = pal.select(color_needs)
      dot_xlat = self.get_dot_xlat(color_needs, palette_option)
      (chr_num, flip_bits) = self.store_chrdata(dot_xlat, did, config)
      self._ppu_memory.spritelist.append([corner_y - 1, chr_num,
                                          pid | flip_bits, corner_x])
    self._ppu_memory.palette_spr = pal

  def _find_region_corners(self, fill):
    """Scan the entire image. Calculate the positions of tile corners."""
    self._regions = []
    self._corners = []
    for y in xrange(self.image_y):
      isImage = False
      x = 0
      edges = []
      while x < self.image_x:
        nc = self._get_nes_color(y, x)
        if nc != fill and not isImage:
          isImage = True
          edges.append(Edge(x, None))
        elif nc == fill and isImage:
          isImage = False
          edges[-1].right = x
        x += 1
      self._combine_edges_into_region(y, edges)

  def _combine_edges_into_region(self, y, edges):
    """Merge new edges into the current set of regions."""
    removal = self._regions_to_remove(y)
    if removal:
      self._apply_removal_to_regions(removal)
    for e in edges:
      self._insert_or_merge_into(y, e)

  def _regions_to_remove(self, y):
    """Calculate indexes of which regions to remove."""
    removal = []
    for k, r in enumerate(self._regions):
      if y != r.bottom + 1:
        removal.append(k)
    return removal

  def _apply_removal_to_regions(self, removal):
    """Remove regions."""
    accum = []
    for k, r in enumerate(self._regions):
      if not k in removal:
        accum.append(r)
    self._regions = accum

  def _insert_or_merge_into(self, y, edge):
    k = 0
    for r in self._regions:
      if edge.left == r.left and edge.right == r.right and y == r.bottom + 1:
        r.bottom = y
        return
      if edge.left >= r.right:
        k += 1
        continue
      if edge.right <= r.left:
        break
      if edge.left < r.left and edge.right == r.right:
        # Corner created by a partially overlapping edge.
        self._corners.append((y, edge.left))
        r.left = edge.left
        r.bottom = y
        return
      if edge.left == r.left and edge.right < r.right:
        r.right = edge.right
        r.bottom = y
        return
      if edge.left == r.left and edge.right > r.right:
        # Region expands to the right, implying a corner inside the region.
        self._corners.append((y, edge.right - 8))
        r.right = edge.right
        r.bottom = y
        return
      if edge.left > r.left and edge.right == r.right:
        r.left = edge.left
        r.bottom = y
        return
      if edge.left < r.left and edge.right < r.right:
        # Entire region shifts to the left, creating a new corner.
        self._corners.append((y, edge.left))
        r.left = edge.left
        r.bottom = y
        return
      raise NotImplementedError()
    # Corner caused by a brand new edge of a region.
    self._corners.append((y, edge.left))
    insert = Region(top=y, left=edge.left, right=edge.right, bottom=y)
    self._regions = self._regions[:k] + [insert] + self._regions[k:]

  def _get_nes_color(self, y, x):
    p = self.pixels[x, y]
    color_val = (p[0] << 16) + (p[1] << 8) + p[2]
    if color_val in rgb.RGB_XLAT:
      return rgb.RGB_XLAT[color_val]
    else:
      nc = self.components_to_nescolor(p[0], p[1], p[2])
      if nc == -1:
        raise errors.ColorNotAllowedError(p, tile_y, tile_x, i, j)
      return nc
