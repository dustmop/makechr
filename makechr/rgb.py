COLOR_TOLERANCE = 64


# From: http://www.thealmightyguru.com/Games/Hacking/Wiki/index.php?title=NES_Palette
                # 00        10        20        30
RGB_COLORS = [[0x7c7c7c, 0xbcbcbc, 0xf8f8f8, 0xfcfcfc], # gray
              [0x0000fc, 0x0078f8, 0x3cbcfc, 0xa4e4fc], # blue
              [0x0000bc, 0x0058f8, 0x6888fc, 0xb8b8f8], # blue dark
              [0x4428bc, 0x6844fc, 0x9878f8, 0xd8b8f8], # purple
              [0x940084, 0xd800cc, 0xf878f8, 0xf8b8f8], # pink
              [0xa80020, 0xe40058, 0xf85898, 0xf8a4c0], # red
              [0xa81000, 0xf83800, 0xf87858, 0xf0d0b0], # orange
              [0x881400, 0xe45c10, 0xfca044, 0xfce0a8], # orange dark
              [0x503000, 0xac7c00, 0xf8b800, 0xf8d878], # yellow
              [0x007800, 0x00b800, 0xb8f818, 0xd8f878], # green light
              [0x006800, 0x00a800, 0x58d854, 0xb8f8b8], # green
              [0x005800, 0x00a844, 0x58f898, 0xb8f8d8], # green dark
              [0x004058, 0x008888, 0x00e8d8, 0x00fcfc], # blue green
              [0x080808, 0x2c2c2c, 0x787878, 0xf8d8f8], # gray dark
              [0x080808, 0x080808, 0x080808, 0x080808], # black 1
              [0x000000, 0x080808, 0x080808, 0x080808], # black 2
              ]



def transpose(matrix):
  return [list(k) for k in zip(*matrix)]


def flatten(matrix):
  return [e for sublist in matrix for e in sublist]


BLACK = 0xf


def to_lookup_table(elems):
  answer = {}
  for i,val in enumerate(elems):
    answer[val] = i
  # Set black.
  answer[0] = BLACK
  return answer


RGB_COLORS = flatten(transpose(RGB_COLORS))
RGB_XLAT = to_lookup_table(RGB_COLORS)
