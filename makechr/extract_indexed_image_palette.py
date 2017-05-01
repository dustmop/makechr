import errors
import palette
import rgb


class ExtractIndexedImagePalette(object):
  def __init__(self, parent):
    self.parent = parent

  def extract_palette(self, imgpal):
    pal = palette.Palette()
    for j in xrange(4):
      p = []
      for k in xrange(4):
        i = j * 4 + k
        nc = self._to_nescolor(imgpal.get(i))
        if nc == -1:
          raise errors.PaletteExtractionError('Color not found: %s' %
                                              imgpal.get(i))
        if k == 0 and pal.bg_color is None:
          pal.set_bg_color(nc)
        elif k == 0 and pal.bg_color != nc:
          raise errors.PaletteExtractionError(
            'Background color did not match: %s <> %s' %
            (pal.bg_color, nc))
        p.append(nc)
      pal.add(p)
    return pal

  def _to_nescolor(self, triplet):
    (r, g, b) = triplet
    color_val = (r << 16) + (g << 8) + b
    if color_val in rgb.RGB_XLAT:
      nc = rgb.RGB_XLAT[color_val]
    else:
      nc = self.parent.components_to_nescolor(r, g, b)
    return nc
