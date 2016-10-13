import app
import argparse
import bg_color_spec
import errno
import errors
from PIL import Image
import sys


__version__ = '1.2'


def run():
  usage = ''
  parser = argparse.ArgumentParser(
    description='Make CHR data files and other NES graphics components.',
    epilog=('Example: python makechr.py image.png -o build/image.%s.dat '
            '-p P/30-2c-01/'))
  parser.add_argument('input', type=str, nargs='?',
                      help='Filename for pixel art image. Should by 256x240.')
  parser.add_argument('--version', dest='version', action='store_true',
                      help=('Show the version number and exit.'))

  # Output.
  parser.add_argument('-o', dest='output', metavar='output',
                      help=('Template for naming output files if outputting '
                            'raw binary, or name of object file. Template must '
                            'contain "%%s". Object file must end in ".o"'))
  parser.add_argument('-c', dest='compile', metavar='rom',
                      help=('Output filename for compiled NES rom. The rom '
                            'just displays the original image when run in '
                            'an emulator.'))
  parser.add_argument('-e', dest='error_outfile', metavar='image',
                      help=('Output filename for image if there are any '
                            'errors.'))

  # Graphics.
  parser.add_argument('-p', dest='palette', metavar='palette',
                      help=('Palette for the pixel art image. Syntax looks '
                            'like this: "P/30-16-1c-02/30-2a/". Each value '
                            'is in hexadecimal.'))
  parser.add_argument('-b', dest='bg_color', metavar='background_color',
                      type=bg_color_spec.build, default=bg_color_spec.default(),
                      help=('Background color spec. Either a single color in '
                            'hexadecimal, or a pair separated by an equals, '
                            'which specify the look (used in the pixel art) '
                            'then the fill (output to the palette).'))
  parser.add_argument('-s', dest='is_sprite', action='store_true',
                      help=('Sprite mode, has 3 effects. 1) Nametable and '
                            'attribute components are not output but '
                            'spritelist component is. 2) The palette is '
                            'stored at 0x10-0x1f instead of 0x00-0x0f. 3) The '
                            'default chr_order is set to 0x1000 instead of '
                            '0x000; can be overriden with the -r flag.'))

  # Flags.
  parser.add_argument('-l', dest='is_locked_tiles', action='store_true',
                      help=('Lock tiles in the pixel art so that they appear '
                            'in CHR at the same position. Useful for tiles '
                            'whose index have some meaningful semantic value. '
                            'Duplicates are not removed. Only first 256 tiles '
                            'in the image are processed. Nametable would '
                            'simply be monotonically increasing, so it is '
                            'not output at all. If image is 128x128 then '
                            'only 8x8 blocks are processed.'))
  parser.add_argument('-t', dest='traversal_strategy', metavar='strategy',
                      help=('Traverse image, when generating CHR and '
                            'nametable, according to this strategy. If '
                            '"horizontal" then traverse left to right, top to '
                            'bottom. If "block" then traverse a block at a '
                            'time, in a zig-zag. If "free" then traverse '
                            'freely looking for sprites (requires -s flag '
                            'and -b). If "8x16" then traverse sprites so '
                            'that they are suitable for 8x16 mode.'))
  parser.add_argument('-r', dest='order', metavar='chr_order', type=int,
                      help=('Order that the CHR data appears in memory, '
                            'relative to other CHR data. Must be 0 or 1. '
                            'If 0 then CHR data appears at 0x0000, if 1 then '
                            'CHR data appears at 0x1000.'))
  parser.add_argument('-z', dest='show_stats', action='store_true',
                      help='Whether to show statistics before exiting.')

  # Input
  parser.add_argument('-m', dest='memimport', metavar='memory_dump',
                      help=('Filename for memory dump to import, instead of '
                            'using pixel art image.'))

  # Views.
  parser.add_argument('--palette-view', dest='palette_view',
                      metavar='image',
                      help=('Output filename for palette view. Will show the '
                            'palette used for output.'))
  parser.add_argument('--colorization-view', dest='colorization_view',
                      metavar='image',
                      help=('Output filename for colorization view. Will show '
                            'palette used for each block according to the '
                            'attributes.'))
  parser.add_argument('--reuse-view', dest='reuse_view',
                      metavar='image',
                      help=('Output filename for reuse view. Will show color '
                            'for each tile based upon how many times the '
                            'tile is used. See README.md for the legend.'))
  parser.add_argument('--nametable-view', dest='nametable_view',
                      metavar='image',
                      help=('Output filename for nametable view to output. '
                            'Will show, for each position in the nametable, '
                            'the tile number in hexadecimal, or blank if 0.'))
  parser.add_argument('--chr-view', dest='chr_view',
                      metavar='image',
                      help=('Output filename for CHR view to output. Will show '
                            'the raw CHR, without color, in the order that '
                            'they appear in memory.'))
  parser.add_argument('--grid-view', dest='grid_view',
                      metavar='image',
                      help=('Output filename for grid view to output. Is the '
                            'input image at x2 resolution with a grid, light '
                            'green for blocks, dark green for tiles.'))
  args = parser.parse_args()
  if args.version:
    sys.stdout.write('makechr ' + __version__ + '\n')
    sys.exit(0)
  application = app.Application()
  if args.memimport and args.input:
    sys.stderr.write('Cannot both import memory and process input file')
    sys.exit(1)
  elif args.memimport:
    application.read_memory(args.memimport, args)
  elif args.input:
    try:
      img = Image.open(args.input)
    except IOError, e:
      if e.errno is None:
        sys.stderr.write('Not an image file: "%s"\n' % args.input)
      elif e.errno == errno.ENOENT:
        sys.stderr.write('Input file not found: "%s"\n' % args.input)
      sys.exit(1)
    try:
      if not application.run(img, args):
        sys.exit(1)
    except errors.CommandLineArgError, e:
      sys.stderr.write('Command-line error: %s\n' % e)
      sys.exit(1)
  else:
    parser.print_usage()


if __name__ == '__main__':
  run()
