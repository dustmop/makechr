import app
import argparse
from PIL import Image
import sys


def run():
  parser = argparse.ArgumentParser(description='Make chr data files and '
                                   'other NES graphics files')
  parser.add_argument('input', type=str, nargs='?',
                      help='filename for pixel art image')
  parser.add_argument('-X', dest='experimental', action='store_true',
                      required=True,
                      help='enable experimental features (required)')
  parser.add_argument('-c', dest='compile', metavar='rom filename',
                      help='filename for compiled NES rom')
  parser.add_argument('-e', dest='error_outfile', metavar='image filename',
                      help='filename for error image')
  parser.add_argument('-p', dest='palette', metavar='palette',
                      help='palette for the pixel art image')
  parser.add_argument('-o', dest='output', metavar='output',
                      help='template for naming output files')
  parser.add_argument('-m', dest='memimport', metavar='memory import filename',
                      help='filename for memory import input')
  parser.add_argument('-l', dest='is_locked_tiles', action='store_true',
                      help=('lock tiles into their given positions, if image '
                            'is 128px by 128px will only process 8x8 blocks'))
  parser.add_argument('-r', dest='order', metavar='chr order',
                      help='order that chr appears within all chr data')
  parser.add_argument('--palette-view', dest='palette_view',
                      metavar='image filename',
                      help='filename for palette view')
  parser.add_argument('--colorization-view', dest='colorization_view',
                      metavar='image fileanme',
                      help='filename for colorization view')
  parser.add_argument('--reuse-view', dest='reuse_view',
                      metavar='image fileanme',
                      help='filename for reuse view')
  parser.add_argument('--nametable-view', dest='nametable_view',
                      metavar='image fileanme',
                      help='filename for nametable view')
  parser.add_argument('--chr-view', dest='chr_view',
                      metavar='image fileanme',
                      help='filename for nametable view')
  parser.add_argument('--grid-view', dest='grid_view',
                      metavar='image fileanme',
                      help='filename for grid view')
  args = parser.parse_args()
  application = app.Application()
  if args.memimport:
    application.read_memory(args.memimport, args)
  else:
    try:
      img = Image.open(args.input)
    except IOError:
      sys.stderr.write('Input file not found: "%s"\n' % args.input)
      sys.exit(1)
    application.run(img, args)


if __name__ == '__main__':
  run()
