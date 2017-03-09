import collections


BgColorSpec = collections.namedtuple('BgColorSpec', ['mask', 'fill'])


def build(text=None):
  """Background color, either a single color, or assignment pair.

  A background spec can be a single color, which is used for processing the
  pixel art image, and for output into the palette.

  Or, a background spec can be a pair using assignment. The lhs is called the
  `mask` color, and is used to process the pixel art image. The rhs is called
  the `fill` color, and is output into the palette."""
  if not text:
    (mask_bg, fill_bg) = [None, None]
  elif not '=' in text:
    (mask_bg, fill_bg) = [None, int(text, 16)]
  else:
    (mask_bg, fill_bg) = [int(e, 16) for e in text.split('=')]
  return BgColorSpec(mask=mask_bg, fill=fill_bg)


def default():
  return BgColorSpec(None, None)
