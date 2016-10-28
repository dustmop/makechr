import collections
import image_processor
import ppu_memory
import rgb


NULL = 0xff


class Span(object):
  """Span represents a start side on the left, and finish side on the right."""

  def __init__(self, left, right):
    self.left = left
    self.right = right

  def same_as(self, other):
    return self.left == other.left and self.right == other.right

  def fully_left(self, other):
    return self.right <= other.left

  def fully_right(self, other):
    return self.left >= other.right

  def contains(self, num):
    return self.left <= num <= self.right

  def __repr__(self):
    return '<Span L=%s R=%s>' % (self.left, self.right)

  def __cmp__(self, other):
    if self.left < other.left:
      return -1
    if self.right < other.right:
      return -1
    if self.left > other.left:
      return 1
    if self.right > other.right:
      return 1
    return 0


class Zone(object):
  """A rectangle which contains 4 sides. May have ambiguous sides."""

  def __init__(self, top=None, left=None, right=None, bottom=None,
               left_range=None, right_range=None):
    self.top = top
    self.left = left
    self.right = right
    self.bottom = bottom
    self.left_range = left_range
    self.right_range = right_range

  def each_sprite(self):
    y = self.top
    while y < self.bottom:
      x = self.left
      while x < self.right:
        yield y,x
        x += 8
        if 0 < self.right - x < 8:
          x = self.right - 8
      y += 8
      if 0 < self.bottom - y < 8:
        y = self.bottom - 8

  def rect(self):
    return [self.left, self.top, self.right-1, self.bottom-1]

  def __repr__(self):
    maybe_bottom = ''
    if not self.bottom is None:
      maybe_bottom = ' B=%s' % self.bottom
    return ('<Zone T=%s L=%s R=%s%s>' % (
      self.top, self.left_range or self.left, self.right_range or self.right,
      maybe_bottom))


class FreeSpriteProcessor(image_processor.ImageProcessor):
  """Converts free sprites image into data structures of the PPU's memory."""

  def __init__(self):
    image_processor.ImageProcessor.__init__(self)
    self._built = []

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
    zones = self._find_zones(bg_color_fill)
    # Convert zones into artifacts.
    artifacts = []
    for z in zones:
      for sprite_y, sprite_x in z.each_sprite():
        (color_needs, dot_profile) = self.process_tile(
          sprite_y / 8, sprite_x / 8, sprite_y % 8, sprite_x % 8)
        cid = self._color_manifest.id(color_needs)
        did = self._dot_manifest.id(dot_profile)
        artifacts.append([sprite_y, sprite_x, cid, did])
    self._needs_provider = self._color_manifest
    # Build the palette.
    pal = self.make_palette(palette_text, bg_color_look, True)
    # Build the PPU memory.
    for y, x, cid, did in artifacts:
      color_needs = self._color_manifest.at(cid)
      (pid, palette_option) = pal.select(color_needs)
      dot_xlat = self.get_dot_xlat(color_needs, palette_option)
      (chr_num, flip_bits) = self.store_chrdata(dot_xlat, did, config)
      self._ppu_memory.spritelist.append([y - 1, chr_num, pid | flip_bits, x])
    self._ppu_memory.palette_spr = pal
    # HACK: Assign zones to ppu_memory so that they can be used by the
    # view renderer.
    self._ppu_memory.zones = zones

  def _find_zones(self, fill):
    """Scan the entire image. Calculate the positions of tile corners."""
    self._making = []
    self._built = []
    self._previous = []
    # For each line of the image, starting from the top.
    for y in xrange(self.image_y):
      is_color = False
      x = 0
      spans = []
      # Construct next span.
      while x < self.image_x:
        nc = self.get_nes_color(y, x)
        if nc != fill and not is_color:
          is_color = True
          spans.append(Span(x, None))
        elif nc == fill and is_color:
          is_color = False
          spans[-1].right = x
        x += 1
      # Combine previous and next spans.
      self._combine_spans(y, spans)
    if len(self._making):
      raise errors.UnknownLogicFailure('incomplete zones after span processing')
    zones = self._built
    self._making = self._built = None
    return zones

  def _combine_spans(self, y, spans):
    # If previous and next spans are the same, nothing to do.
    if spans == self._previous:
      return
    # Zip the previous and next spans, combining them as we go along.
    i = j = 0
    while i < len(self._previous) and j < len(spans):
      above = self._previous[i]
      below = spans[j]
      # Check if either completely the same, or completely separate.
      if below.same_as(above):
        i += 1
        j += 1
        continue
      elif below.fully_left(above):
        j += 1
        self._insert_zone(top=y, left=below.left, right=below.right)
        continue
      elif below.fully_right(above):
        i += 1
        self._finish_span(y, above)
        continue
      # Some partial overlap between above and below.
      did_insert = False
      want_side = None
      # Check how the left sides of the spans compare to each other.
      if below.left < above.left:
        want_side = self._insert_zone(top=y, left=below.left, right=above.left)
      elif below.left == above.left:
        pass
      elif below.left > above.left:
        for zone in self._making:
          if not above.contains(zone.left) and not above.contains(zone.right):
            continue
          if zone.left_range and zone.left_range.contains(below.left):
            zone.left_range = None
            zone.left = below.left
            did_insert = True
            break
          elif zone.top != y:
            zone.bottom = y
        if not did_insert:
          self._insert_zone(top=y, left=below.left, right=below.right)
          did_insert = True
      # Check how the right sides of the spans compare to each other.
      if below.right < above.right:
        for zone in self._making:
          if not above.contains(zone.left) and not above.contains(zone.right):
            continue
          if zone.right_range and zone.right_range.contains(below.right):
            zone.right_range = None
            zone.right = below.right
            did_insert = True
          elif zone.top != y:
            zone.bottom = y
        if not did_insert:
          self._insert_zone(top=y, left=below.left, right=below.right)
          did_insert = True
      elif below.right == above.right:
        if want_side:
          want_side.right_range = Span(want_side.right, above.right)
      elif below.right > above.right:
        if not did_insert:
          self._insert_zone(top=y, left=above.right, right=below.right,
                            left_range=Span(below.left, above.right))
          did_insert = True
      # Iterate either a single span, or both spans.
      if below.left < above.left and below.right > above.right:
        i += 1
        continue
      elif below.left > above.left and below.right < above.right:
        j += 1
        continue
      else:
        i += 1
        j += 1
        continue
    # Handle spans from previous line, to the right of anything on this line,
    # which are now all finished.
    while i < len(self._previous):
      above = self._previous[i]
      self._finish_span(y, above)
      i += 1
    # Handle spans from this new line, which are new zones.
    while j < len(spans):
      below = spans[j]
      self._insert_zone(top=y, left=below.left, right=below.right)
      j += 1
    # Collect completed zones.
    i = 0
    while i < len(self._making):
      if self._making[i].bottom is None:
        i += 1
      else:
        self._built.append(self._making[i])
        self._making = self._making[:i] + self._making[i + 1:]
    # Next line.
    self._previous = spans

  def _finish_span(self, y, span):
    for i,elem in enumerate(self._making):
      # Skip zones that were just created.
      if y == elem.top:
        continue
      # Zones that do not exist in the current spans get assigned a bottom.
      L = elem.left.right if isinstance(elem.left, Span) else elem.left
      R = elem.right.left if isinstance(elem.right, Span) else elem.right
      if span.left <= L and span.right >= R:
        elem.bottom = y

  def _insert_zone(self, top=None, left=None, right=None, bottom=None,
                   left_range=None, right_range=None):
    make = Zone(top=top, left=left, right=right, bottom=bottom,
                left_range=left_range, right_range=right_range)
    i = 0
    for i,elem in enumerate(self._making):
      if elem.left >= make.left:
        self._making.insert(i, make)
        return make
    self._making.append(make)
    return make
