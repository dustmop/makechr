import palette
import rgb


class ExtractIndexedImagePalette(object):
  def __init__(self, parent):
    self.parent = parent

  def extract_palette(self, imgpal, format):
    bytes = imgpal.palette
    if len(bytes) < 0x30:
      return None
    pal = palette.Palette()
    for j in xrange(4):
      p = []
      for k in xrange(4):
        i = j * 4 + k
        nc = self._get_color(bytes[i*3:i*3 + 3], format)
        if nc == -1:
          return None
        if k == 0 and pal.bg_color is None:
          pal.set_bg_color(nc)
        elif k == 0 and pal.bg_color != nc:
          return None
        p.append(nc)
      pal.add(p)
    return pal

  def _get_color(self, triplet, format):
    # TODO: Investigate other formats, and/or generalize.
    if format == 'BMP':
      triplet = triplet[::-1]
    r = ord(triplet[0])
    g = ord(triplet[1])
    b = ord(triplet[2])
    color_val = (r << 16) + (g << 8) + b
    if color_val in rgb.RGB_XLAT:
      nc = rgb.RGB_XLAT[color_val]
    else:
      nc = self.parent.components_to_nescolor(r, g, b)
    return nc
