import collections
import data
import eight_by_sixteen_processor
import errors
import id_manifest
import image_processor
import ppu_memory
import rgb
import span_list_delta
from constants import *


class FreeSpriteProcessor(image_processor.ImageProcessor):
  """Converts free sprites image into data structures of the PPU's memory."""

  def __init__(self, traversal):
    image_processor.ImageProcessor.__init__(self)
    self.traversal = traversal
    self._verbose = False
    self._min_width = 8
    self._regions = []
    self._vert_color_manifest = id_manifest.IdManifest()

  def set_verbose(self, verbose):
    self._verbose = verbose

  def process_image(self, img, palette_text, bg_color_mask, bg_color_fill,
                    is_locked_tiles, lock_sprite_flips, allow_overflow):
    """Process free sprites image, creating the ppu_memory it represents.

    The image represents the entire screen, and is mostly filled with
    bg_color_fill. Anywhere that contains other pixel data is considered to be
    made of sprites. Those sprites are located, treated as tiles, and processed
    to be converted into PPU memory.

    img: Pixel art image.
    palette_text: Optional string representing a palette to be parsed.
    bg_color_mask: Background color that masks existing free sprite tiles.
    bg_color_fill: Background color which fills up the outside space.
    is_locked_tiles: Whether tiles are locked or not.
    allow_overflow: List of components for which to allow overflows.
    """
    self.initialize()
    self.load_image(img)
    config = ppu_memory.PpuMemoryConfig(is_sprite=True,
                                        is_locked_tiles=is_locked_tiles,
                                        lock_sprite_flips=lock_sprite_flips,
                                        allow_overflow=allow_overflow)
    is_tall = '8x16' in self.traversal
    # Scan the image, find corners of each tile based upon region merging.
    try:
      zones = self._find_zones(bg_color_fill)
    except errors.CouldntConvertRGB as e:
      self._err.add(e)
      return None
    # HACK: Assign zones to ppu_memory so that they can be used by the
    # view renderer.
    self._ppu_memory.zones = zones
    # Parse the palette if provided.
    pal = None
    if palette_text or self.img.palette:
      pal = self.parse_palette(palette_text, bg_color_mask)
    # Convert zones into artifacts.
    artifacts = []
    for z in zones:
      vert_color_needs = None
      for sprite_y, sprite_x in z.each_sprite(is_tall):
        (color_needs, dot_profile) = self.process_tile(
          sprite_y / 8, sprite_x / 8, sprite_y % 8, sprite_x % 8)
        cid = self._color_manifest.id(color_needs)
        did = self._dot_manifest.id(dot_profile)
        artifacts.append([cid, did, None, sprite_y, sprite_x])
        if not is_tall:
          continue
        elif vert_color_needs is None:
          vert_color_needs = color_needs
        else:
          try:
            self.combine_color_needs(vert_color_needs, color_needs)
          except errors.PaletteOverflowError as e:
            e.tile_y = sprite_y / 8
            e.tile_x = sprite_x / 8
            self._err.add(e)
            continue
          vcid = self._vert_color_manifest.id(vert_color_needs)
          artifacts[-1][ARTIFACT_VCID] = vcid
          vert_color_needs = None
    if self._err.has():
      return
    self._needs_provider = self._color_manifest
    if is_tall:
      self._needs_provider = self._vert_color_manifest
    # Build the palette.
    if not pal:
      pal = self.make_palette(bg_color_mask, True)
    # Build the PPU memory.
    if not is_tall:
      for cid, did, unused, y, x in artifacts:
        color_needs = self._color_manifest.at(cid)
        (pid, palette_option) = pal.select(color_needs)
        dot_xlat = self.get_dot_xlat(color_needs, palette_option)
        try:
          (chr_num, flip_bits) = self.store_chrdata(dot_xlat, did, config)
        except errors.NametableOverflow as e:
          self._err.add(errors.NametableOverflow(e.chr_num, y, x))
          chr_num = 0
        if (config.is_locked_tiles and self._ppu_memory.chr_set.is_full() and
            chr_num == 0):
          raise errors.ChrPageFull()
        self._ppu_memory.spritelist.append([y - 1, chr_num, pid | flip_bits, x])
    else:
      ebs_processor = eight_by_sixteen_processor.EightBySixteenProcessor()
      ebs_processor.link_from(self)
      for i in xrange(0, len(artifacts), 2):
        (cid_u, did_u, unused, y, x) = artifacts[i]
        (cid_l, did_l, vcid, unused_y, unused_x) = artifacts[i+1]
        color_needs = self._vert_color_manifest.at(vcid)
        (pid, palette_option) = pal.select(color_needs)
        chr_num_u, chr_num_l, flip_bits = ebs_processor.store_vert_pair(
          palette_option, cid_u, did_u, cid_l, did_l, config)
        if (config.is_locked_tiles and self._ppu_memory.chr_set.is_full() and
            chr_num_u == 0 and chr_num_l == 0):
          raise errors.ChrPageFull()
        # TODO: Only add this 1 if the sprite chr order is 1.
        chr_num = chr_num_u + 1
        if not 's' in config.allow_overflow:
          if len(self._ppu_memory.spritelist) >= 0x40:
            self._err.add(errors.SpritelistOverflow(y, x))
            continue
        self._ppu_memory.spritelist.append([y - 1, chr_num, pid | flip_bits, x])
    self._ppu_memory.palette_spr = pal

  def _find_zones(self, fill):
    """Scan the entire image. Calculate the positions of tile corners."""
    if self._verbose:
      print('')
    self._regions = []
    zones = []
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
          spans.append(data.Span(x, None))
        elif nc == fill and is_color:
          is_color = False
          spans[-1].right = x
        x += 1
      # Combine previous and next spans.
      zones += self._combine_spans(y, spans)
    # Display the zones in verbose mode.
    if self._verbose:
      print('----------------------------------------')
      last_bottom = 0
      for z in zones:
        if z.top > last_bottom:
          print('****')
        last_bottom = z.bottom
        print('%r' % z)
      print('****************************************')
    return zones

  def _combine_spans(self, y, spans):
    built = []
    test_prev = str(self._regions)
    delta = span_list_delta.get_delta(spans, self._regions)
    if self._verbose and delta.keys() and delta.keys() != ['same']:
      print('')
      print('* Y=%d Spans: %r, Regions: %r' % (y, spans, self._regions))
      print('* Zones: %r' % ([r.zones for r in self._regions]))
      print('* Delta: %r' % (delta,))
    delta_include = delta.get('include')
    delta_exclude = delta.get('exclude')
    delta_same = delta.get('same')
    delta_merge = delta.get('merge')
    delta_split = delta.get('split')
    delta_diff = delta.get('diff')
    if delta_include:
      self._insert_spans_as_regions(y, delta_include)
    if delta_exclude:
      built += self._exclude_regions_and_make_zones(y, delta_exclude)
    if delta_same:
      pass
    if delta_merge:
      built += self._merge_region_changes(y, delta_merge, )
    if delta_split:
      raise NotImplementedError('TODO: split %r' % delta_split)
    if delta_diff:
      raise NotImplementedError('TODO: diff %r' % delta_diff)
    self._add_zones_to_empty_regions(y)
    built = self._fixup_edges(built)
    if self._verbose and len(built):
      print('> Built: %r' % built)
    return built

  def _insert_spans_as_regions(self, y, include):
    """Insert new regions."""
    for edge in include:
      self._insert_into(data.Region.make_from(y, edge), self._regions)

  def _exclude_regions_and_make_zones(self, y, exclude):
    """Remove the excluded zones and collect their zones."""
    built = []
    k = 0
    for elem in exclude:
      # Finish the zones from any excluded regions.
      zones = elem.zones
      for z in zones:
        z.bottom = y
      built += zones
      # Remove excluded regions.
      while k < len(self._regions):
        region = self._regions[k]
        if elem == region:
          self._regions = self._regions[0:k] + self._regions[k+1:]
          break
        else:
          k += 1
    return built

  def _merge_region_changes(self, y, merge):
    """Handle changes caused by one or more regions being merged into one."""
    built = []
    once = False
    for change in merge:
      old = change['old']
      new = change['new']
      below = new[0]
      collect = []
      if old[0].left == below.left and old[-1].right == below.right:
        for above in old:
          collect += above.zones
          self._regions.remove(above)
        zone = data.Zone(left=below.left, right=below.right, top=y,
                         maybe_left=old[0].right, maybe_right=old[-1].left)
        collect.append(zone)
      else:
        for above in old:
          if below.left < above.left and below.right == above.right:
            zone = data.Zone(left=below.left, right=below.right, top=y,
                             maybe_right=above.left)
            self._insert_into(zone, collect)
          elif below.left == above.left and below.right > above.right:
            zone = data.Zone(left=below.left, right=below.right, top=y,
                             maybe_left=above.right)
            self._insert_into(zone, collect)
          elif below.left == above.left and below.right < above.right:
            built += self._finish_zones_on_the_right(y, above, below.right)
          elif below.left > above.left and below.right == above.right:
            built += self._finish_zones_on_the_left(y, above, below.left)
          elif below.left < above.left and below.right < above.right:
            built += self._cull_static_zones(y, above)
          elif below.left > above.left and below.right > above.right:
            built += self._cull_static_zones(y, above)
          else:
            raise RuntimeError('TODO unknown above=%r below=%r' %
                               (above, below))
          collect += above.zones
          self._regions.remove(above)
      region = data.Region(below.left, below.right)
      region.zones = collect
      self._insert_into(region, self._regions)
    return built

  def _insert_into(self, item, target):
    """Insert an element into a sorted list."""
    for i,each in enumerate(target):
      if item.left < each.left:
        target.insert(i, item)
        return
    else:
      target.append(item)

  def _fixup_edges(self, zones):
    """For each complete zone, pull in ambiguous sides if they overlap."""
    zones.sort(key=lambda x:(x.left,x.maybe_left or x.left))
    limit = None
    for z in zones:
      if limit is None:
        limit = z.right
      elif z.maybe_left and z.left < limit:
        z.left = limit
      limit = z.right
    limit = None
    for z in zones[::-1]:
      if limit is None:
        limit = z.left
      elif z.maybe_right and z.right > limit:
        z.right = limit
      limit = z.left
    return zones

  def _finish_zones_on_the_right(self, y, region, cutoff):
    """Either remove regions or resize their edges based upon the cuttoff."""
    built = []
    j = 0
    while j < len(region.zones):
      z = region.zones[j]
      if cutoff < z.right:
        if z.maybe_right is None or cutoff - z.left < self._min_width:
          if z.maybe_left:
            z.left, z.maybe_left = (z.maybe_left, None)
          z.bottom = y
          built.append(z)
          region.zones = region.zones[0:j] + region.zones[j+1:]
          continue
        else:
          z.right = cutoff
          if z.right == z.maybe_right:
            z.maybe_right = None
          j += 1
          continue
      else:
        j += 1
    return built

  def _finish_zones_on_the_left(self, y, region, cutoff):
    """Either remove regions or resize their edges based upon the cuttoff."""
    built = []
    j = 0
    while j < len(region.zones):
      z = region.zones[j]
      if cutoff > z.left:
        if z.maybe_left is None or z.right - cutoff < self._min_width:
          if z.maybe_right:
            z.right, z.maybe_right = (z.maybe_right, None)
          z.bottom = y
          built.append(z)
          region.zones = region.zones[0:j] + region.zones[j+1:]
          continue
        else:
          z.left = cutoff
          if z.left == z.maybe_left:
            z.maybe_left = None
          j += 1
          continue
      else:
        j += 1
    return built

  def _cull_static_zones(self, y, region):
    """Remove any zones that have no ambiguous sides."""
    built = []
    for z in region.zones:
      if z.maybe_left or z.maybe_right:
        raise RuntimeError('Dont know what to do')
      z.bottom = y
    built = region.zones
    region.zones = []
    return built

  def _add_zones_to_empty_regions(self, y):
    """Regions without zones have a single zone added."""
    for r in self._regions:
      if r.zones == []:
        r.zones.append(data.Zone(left=r.left, right=r.right, top=y))
