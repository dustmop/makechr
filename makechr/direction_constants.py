DIR_UP = 'up'
DIR_LEFT = 'left'
DIR_RIGHT = 'right'
DIR_DOWN = 'down'


def rotate_dir_cw(dir):
  if dir == DIR_UP:
    return DIR_RIGHT
  elif dir == DIR_RIGHT:
    return DIR_DOWN
  elif dir == DIR_DOWN:
    return DIR_LEFT
  elif dir == DIR_LEFT:
    return DIR_UP


def rotate_dir_counter_cw(dir):
  if dir == DIR_UP:
    return DIR_LEFT
  elif dir == DIR_RIGHT:
    return DIR_UP
  elif dir == DIR_DOWN:
    return DIR_RIGHT
  elif dir == DIR_LEFT:
    return DIR_DOWN


def opposite_dir(dir):
  if dir == DIR_UP:
    return DIR_DOWN
  elif dir == DIR_RIGHT:
    return DIR_LEFT
  elif dir == DIR_DOWN:
    return DIR_UP
  elif dir == DIR_LEFT:
    return DIR_RIGHT



