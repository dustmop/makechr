import errors
import rgb
import palette
import partitions
from constants import *


class GuessBestPalette(object):

  def __init__(self):
    self._bg_color = None

  def set_bg_color(self, bg_color):
    self._bg_color = bg_color

  def is_subset(self, subject, target):
    """Return whether subject is a strict subset of target."""
    return set(subject) <= set(target)

  def get_uniq_color_sets(self, color_manifest):
    """Get unique color sets, by removing duplicates and sorting.

    color_manifest: A dict of color sets.
    """
    seen = {}
    for color_needs in color_manifest:
      # Desending order, making it easy to do subset comparisions later.
      ordered_colors = sorted(color_needs, reverse=True)
      name = '-'.join(['%02x' % e for e in ordered_colors])
      seen[name] = ordered_colors
    return sorted(seen.values())

  def get_minimal_colors(self, uniq_color_sets):
    """Merge color sets and return the minimal set of needed color sets.

    uniq_color_sets: List of ordered color sets.
    """
    minimized = []
    for i, color_set in enumerate(uniq_color_sets):
      for j, target in enumerate(uniq_color_sets[i + 1:]):
        if self.is_subset(color_set, target):
          break
      else:
        minimized.append(color_set)
    return minimized

  def merge_color_sets(self, color_set_collection, merge_strategy):
    """Merge some elements of collection, and return a list of sets.

    Given a collection of sets, pick elements according to the strategy to
    return a collection of merged sets. For example, if color_set_collection
    is [A, B, C, D] where A through D are sets, and merge_strategy is
    [set([0, 2]), set([1, 3])] the return value is [merge(A|C), merge(B|D)].

    color_set_collection: Potentional color sets to be merged.
    merge_strategy: List of sets, where each set represents what to merge.
    """
    result = []
    for choices in merge_strategy:
      merged = set()
      for c in choices:
        merged |= set(color_set_collection[c])
      if len(merged) > PALETTE_SIZE:
        return None
      result.append(merged)
    return result

  def get_background_color(self, combined_colors):
    """Determine the global background color.

    Given a list of colors, return the best background color. Prefer
    black if possible, otherwise, use the smallest numerical value.

    combined_colors: List of color needs.
    """
    if not self._bg_color is None:
      return self._bg_color
    possibilities = set(combined_colors[0])
    recommendations = set(possibilities)
    for color_set in combined_colors[1:]:
      if len(color_set) == PALETTE_SIZE:
        possibilities = possibilities & set(color_set)
      recommendations = recommendations & set(color_set)
    if rgb.BLACK in possibilities:
      return rgb.BLACK
    if recommendations:
      return min(recommendations)
    if possibilities:
      return min(possibilities)
    return None

  def colors_have_space_for(self, bg_color, combined_colors):
    for color_set in combined_colors:
      if not bg_color in color_set and len(color_set) == PALETTE_SIZE:
        return False
    return True

  def get_valid_combinations(self, finalized, remaining):
    """Calculate all valid combinations of the palette.

    Some of the color_sets are finalized (full PaletteOptions) the others
    remaining need to be merged. Try all possible combinations, and for each
    one determine the background color. Return all possibilities, at least 1.

    finalized: List of color sets that take up the full size.
    remaining: List of color sets that need to be merged.
    """
    merged_color_possibilities = []
    num_available = NUM_ALLOWED_PALETTES - len(finalized)
    for merge_strategy in partitions.partitions(len(remaining)):
      if len(merge_strategy) > num_available:
        continue
      merged_colors = self.merge_color_sets(remaining, merge_strategy)
      if not merged_colors:
        continue
      combined_colors = finalized + merged_colors
      bg_color = self.get_background_color(combined_colors)
      if bg_color is None:
        continue
      if not self.colors_have_space_for(bg_color, combined_colors):
        continue
      merged_color_possibilities.append([bg_color, combined_colors])
    if not len(merged_color_possibilities):
      raise errors.TooManyPalettesError(finalized, to_merge=remaining)
    return merged_color_possibilities

  def get_merged_color_possibilities(self, minimal_colors):
    """Get all possible merged sets of colors.

    minimal_colors: Set of minimal needed colors.
    """
    finalized = []
    remaining = []
    # We know from earlier steps that minimal_colors is a set of color_sets
    # such that none are subsets of each other. However, some may have some
    # colors in common such that they could be merged. First, let's remove all
    # full palettes, leaving only those that might be mergable.
    for color_set in minimal_colors:
      if len(color_set) == PALETTE_SIZE:
        finalized.append(color_set)
      else:
        remaining.append(color_set)
    if remaining:
      # There are remaining unmerged palettes. Generate all valid combinations
      # of merged palettes, which may fail if there is no way to merge them.
      return self.get_valid_combinations(finalized, remaining)
    elif len(finalized) > NUM_ALLOWED_PALETTES:
      # The number of necessary palettes is more than the number allowed.
      raise errors.TooManyPalettesError(minimal_colors)
    else:
      # There is only one valid combination.
      bg_color = self.get_background_color(finalized)
      return [[bg_color, finalized]]

  def get_palette(self, possibilities):
    """Pick a single palette.

    Given list of possible palettes, just pick and build the first one.

    possibilities: List of possible palettes, must have at least one element.
    """
    (bg_color, color_set_collection) = possibilities[0]
    pal = palette.Palette()
    pal.set_bg_color(bg_color)
    for color_set in color_set_collection:
      pal.add([bg_color] + sorted([c for c in color_set if c != bg_color],
                                  reverse=True))
    return pal

  def guess_palette(self, color_needs_list):
    uniq_color_sets = self.get_uniq_color_sets(color_needs_list)
    minimal_colors = self.get_minimal_colors(uniq_color_sets)
    possibilities = self.get_merged_color_possibilities(minimal_colors)
    return self.get_palette(possibilities)
