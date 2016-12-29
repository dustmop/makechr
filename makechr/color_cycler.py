CURSOR_COLOR_1 = 0xcc44cc
CURSOR_COLOR_2 = 0x00ee44
CURSOR_ANIMATE_TOTAL = 16


class ColorCycler(object):
  def __init__(self):
    self.animate = 0

  def next(self):
    self.animate += 1
    if self.animate >= CURSOR_ANIMATE_TOTAL:
      self.animate = 0

  def get_color(self):
    scale = self.animate
    portion = CURSOR_ANIMATE_TOTAL / 4
    if self.animate < portion:
      # Pink to white
      color = self.scale_color(CURSOR_COLOR_1, 0xffffff, scale)
    elif self.animate < portion * 2:
      # White to green
      color = self.scale_color(0xffffff, CURSOR_COLOR_2, scale - portion)
    elif self.animate < portion * 3:
      # Green to white
      color = self.scale_color(CURSOR_COLOR_2, 0xffffff, scale - (portion * 2))
    else:
      # White to pink
      color = self.scale_color(0xffffff, CURSOR_COLOR_1, scale - (portion * 3))
    return '#%06x' % color

  def scale_color(self, col_a, col_b, scale):
    portion = CURSOR_ANIMATE_TOTAL / 4
    (ra,ga,ba) = (col_a / (0x10000), (col_a / 0x100) % 0x100, col_a % 0x100)
    (rb,gb,bb) = (col_b / (0x10000), (col_b / 0x100) % 0x100, col_b % 0x100)
    r = ((ra * (portion - scale)) + (rb * scale)) / (portion)
    g = ((ga * (portion - scale)) + (gb * scale)) / (portion)
    b = ((ba * (portion - scale)) + (bb * scale)) / (portion)
    color = (r * 0x10000) + (g * 0x100) + b
    return color
