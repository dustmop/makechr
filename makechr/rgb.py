import sys


if '--rgb-mapping' not in sys.argv:
  mapping = 'almighty'
else:
  mapping = sys.argv[sys.argv.index('--rgb-mapping') + 1]
if mapping == 'almighty':
  from rgb_almighty import RGB_COLORS
elif mapping == 'fceux':
  from rgb_fceux import RGB_COLORS
elif mapping == 'nesst':
  from rgb_nesst import RGB_COLORS
else:
  sys.stderr.write('Unknown rgb-mapping: "%s"\n' % mapping)
  sys.exit(1)


COLOR_TOLERANCE = 64
BLACK = 0xf


def to_lookup_table(elems):
  answer = {}
  for i,val in enumerate(elems):
    answer[val] = i
  # Set black.
  answer[0] = BLACK
  return answer


RGB_XLAT = to_lookup_table(RGB_COLORS)


def nc_to_rgb(nc):
  color_val = RGB_COLORS[nc]
  r = color_val / 0x10000
  g = (color_val / 0x100) % 0x100
  b = color_val % 0x100
  return (r, g, b)
