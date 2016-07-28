import collections


BgColorSpec = collections.namedtuple('BgColorSpec', ['look', 'fill'])


def build(text=None):
  """Background color, either a single color, or assignment pair.

  A background spec can be a single color, which is used for processing the
  pixel art image, and for output into the palette.

  Or, a background spec can be a pair using assignment. The lhs is called the
  `look` color, and is used to process the pixel art image. The rhs is called
  the `fill` color, and is output into the palette."""
  if not text:
    (look_bg, fill_bg) = [None, None]
  elif not '=' in text:
    (look_bg, fill_bg) = [int(text, 16), None]
  else:
    (look_bg, fill_bg) = [int(e, 16) for e in text.split('=')]
  return BgColorSpec(look=look_bg, fill=fill_bg)


def default():
  return BgColorSpec(None, None)
