import errors
import rgb
import palette


NUM_ALLOWED_PALETTES = 4


class GuessBestPalette(object):

  # to_color_set
  #
  # Given a string, often from a hash table key, parse it to make a sorted
  # color set, without any None elements. The order is descending, making it
  # easy to do subset comparisions later.
  #
  # text: A text representation of a color set. Example: '[45, 15, 8, None]'
  def to_color_set(self, color_needs):
    return sorted([e for e in color_needs if not e is None], reverse=True)

  # is_color_subset
  #
  # Return whether subject is a strict subset of target.
  #
  # subject: A color set.
  # target: A color set.
  def is_color_subset(self, subject, target):
    return set(subject) <= set(target)

  # get_uniq_color_sets
  #
  # Given a color manifest, remove duplicates and sort.
  #
  # color_manifest: A dict of color sets.
  def get_uniq_color_sets(self, color_manifest):
    seen = {}
    for color_needs in color_manifest:
      color_set = self.to_color_set(color_needs)
      name = '-'.join(['%02x' % e for e in color_set])
      seen[name] = color_set
    return sorted(seen.values())

  def get_minimal_colors(self, uniq_color_sets):
    minimized = []
    for i, color_set in enumerate(uniq_color_sets):
      for j, target in enumerate(uniq_color_sets[i + 1:]):
        if self.is_color_subset(color_set, target):
          break
      else:
        minimized.append(color_set)
    return minimized

  # get_background_color
  #
  # Given a list of minimal colors, return the best background color. Prefer
  # black if possible, otherwise, use the smallest numerical value.
  #
  # minimal_colors: List of minimal color needs.
  def get_background_color(self, minimal_colors):
    possibilities = set(minimal_colors[0])
    for color_set in minimal_colors[1:]:
      possibilities = possibilities & set(color_set)
    if rgb.BLACK in possibilities:
      return rgb.BLACK
    return min(possibilities)

  def get_palette(self, bg_color, minimal_colors):
    pal = palette.Palette()
    for color_set in minimal_colors:
      pal.add([bg_color] + [c for c in color_set if c != bg_color])
    return pal

  def make_palette(self, color_needs_list):
    uniq_color_sets = self.get_uniq_color_sets(color_needs_list)
    minimal_colors = self.get_minimal_colors(uniq_color_sets)
    if len(minimal_colors) > NUM_ALLOWED_PALETTES:
      raise errors.TooManyPalettesError(len(minimal_colors))
    bg_color = self.get_background_color(minimal_colors)
    return self.get_palette(bg_color, minimal_colors)
