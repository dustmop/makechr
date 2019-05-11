import app
import argparse
import bg_color_spec
import errno
import errors
import os
from PIL import Image
import sys


__version__ = '1.5'


def allow_overflow_build(text):
  if text == '':
    return []
  elif text == 's':
    return ['s']
  elif text == 'c':
    return ['c']
  elif text in ['cs', 'sc']:
    return ['c', 's']
  else:
    # TODO: Support more types of components.
    raise errors.CommandLineArgError(
      '--allow_overflow only usable with "s" or "c"')


def is_valiant(filename):
  fp = open(filename, 'rb')
  content = fp.read()
  fp.close()
  return content.startswith(b'(VALIANT)')


class BlankLineFormatter(argparse.RawDescriptionHelpFormatter):
  def _split_lines(self, text, width):
    parts = text.split('\n')
    text = parts[0]
    lines = parts[1:]
    lines = argparse.HelpFormatter._split_lines(self, text, width) + lines
    return lines + ['']


def run():
  usage = ''
  parser = argparse.ArgumentParser(
    description='Make CHR data files and other NES graphics components.',
    epilog=('Example: python makechr.py image.png -o build/image.%s.dat '
            '-p P/30-2c-01/'),
    formatter_class=BlankLineFormatter
  )
  parser.add_argument('input', type=str, nargs='?',
                      help='Filename for pixel art image. Should by 256x240.')

  parser.add_argument('--version', dest='version', action='store_true',
                      help=('Show the version number and exit.'))

  parser.add_argument('--verbose', dest='verbose', action='store_true',
                      help=('Show extra messages for debugging.'))

  # Output.
  parser.add_argument('-o', dest='output', metavar='output',
                      help=('Output filename, either a template for binary '
                            'components, or the name of an object file, or '
                            'an image file to render. A template needs to '
                            'have "%%s" in it. An object file needs to end in '
                            '".o". An image file needs to end in ".png". See '
                            'valiant.proto for the format of object files.'))

  parser.add_argument('-c', dest='compile', metavar='rom',
                      help=('Create an NES rom file that just displays the '
                            'original iamge.'))

  parser.add_argument('-e', dest='error_outfile', metavar='image',
                      help=('Output filename for image if there are any '
                            'errors.'))

  # Graphics.
  parser.add_argument('-p', dest='palette', metavar='palette',
                      help=('Palette to use for the input image. Either a '
                            'literal representation, or a file made by '
                            '--makepal, or a switch to control extraction '
                            'from an indexed color image. If none of these '
                            'are set, makechr will automatically derive a '
                            'palette. Syntax for a literal palette looks like '
                            'this: "P/30-16-1c-02/30-2a/", each value is in '
                            'hexadecimal. Switch can be "-" to disable '
                            'palette extraction, or "+" to force palette '
                            'extraction.'))

  parser.add_argument('-b', dest='bg_color', metavar='background_color',
                      type=bg_color_spec.build, default=bg_color_spec.default(),
                      help=('Background color spec for the palette. '
                            'Either a single color, or a pair of colors '
                            'separated by an "=" operator. The first color '
                            'is the "mask" (masking the pixel art), the '
                            'second color is the "fill" (output to the '
                            'palette). If the palette is not provided, the '
                            'derived palette will used this color. If the '
                            'palette is provided, its background color must '
                            'match. Colors must be specified in hexadecimal.'))

  parser.add_argument('-s', dest='is_sprite', action='store_true',
                      help=('Sprite mode, has 3 effects. 1) Nametable and '
                            'attribute components are not output but '
                            'spritelist component is. 2) The palette is '
                            'stored at 0x10-0x1f instead of 0x00-0x0f. 3) The '
                            'default chr_order is set to 0x1000 instead of '
                            '0x000; can be overriden with the -r flag.'))

  parser.add_argument('-ds', dest='decompose_sprites', action='store_true',
                      help=('Decompose sprite mode will take an assembled '
                            'picture object, and decompose it into sprites. '
                            'The result is chr, palette, and json representing '
                            'how to compose the original input picture.'))

  # Flags.
  parser.add_argument('-l', dest='is_locked_tiles', action='store_true',
                      help=('Lock tiles in the pixel art so that they appear '
                            'in CHR at the same position. Useful for tiles '
                            'whose index have some meaningful semantic value. '
                            'Duplicates are not removed. Only first 256 tiles '
                            'in the image are processed. Nametable would '
                            'simply be monotonically increasing, so it is '
                            'not output at all.'))

  parser.add_argument('--lock-sprite-flips', dest='lock_sprite_flips',
                      action='store_true',
                      help=('Locks the vertical and horizontal flip flags '
                            'for sprites, preventing flipped versions being '
                            'merged.'))

  parser.add_argument('-t', dest='traversal_strategy', metavar='strategy',
                      help=('Traverse image using this strategy, when '
                            'generating CHR, nametable, and sprites. Can be '
                            '"horizontal", "block", "vertical", "8x16", '
                            '"free", or "free-8x16". If "horizontal", '
                            'traverse left to right, top to bottom. If '
                            '"block", traverse a block at a time, in a '
                            'zig-zag. If "vertical", traverse top to bottom, '
                            'left to right. If "8x16", traverse in pairs '
                            'left to right, top to bottom. If "free", then '
                            'traverse freely looking for sprites (requires '
                            '-s flag and -b). If "free-8x16", combine both.'))

  parser.add_argument('-r', dest='order', metavar='chr_order', type=int,
                      help=('Order that the CHR data appears in memory, '
                            'relative to other CHR data. Must be 0 or 1. '
                            'If 0 then CHR data appears at 0x0000, if 1 then '
                            'CHR data appears at 0x1000.'))

  parser.add_argument('-z', dest='show_stats', action='store_true',
                      help=('Whether to show statistics at the end of '
                            'processing. Displays number of dot-profiles, '
                            'number of tiles, and the palette.'))

  parser.add_argument('--allow-overflow', dest='allow_overflow',
                      type=allow_overflow_build,
                      help=('Set of components for which to ignore overflow '
                            'errors. Only "c" and "s" are supported, for '
                            '"chr" and "spritelist".'))

  parser.add_argument('--rgb-mapping', dest='rgb_mapping',
                      help=('Mapping between RGB colors and the NES\'s '
                            'native NTSC color signal. Allowed choices are '
                            '"almighty", "fceux", and "nesst".'))

  parser.add_argument('--makepal', dest='makepal', action='store_true',
                      help=('Make palette object file from an image, or '
                            'just output binary data if the file name ends '
                            'in .bin or .dat.'))

  parser.add_argument('--vertical-pixel-display', dest='vertical_pixel_display',
                      action='store_true',
                      help=('Certain platforms, like Arduboy, render pixels '
                            'from top to bottom instead of left to right. '
                            'This flag will change chr storage order to work '
                            'as with this type of display.'))

  parser.add_argument('--select-chr-plane', dest='select_chr_plane',
                      help=('Instead of outputting CHR as a bit-planar bitmap, '
                            'only output plane 0 or plane 1, and ignore the '
                            'other.'))

  # Input
  parser.add_argument('-m', dest='memimport', metavar='memory_dump',
                      help=('Filename for memory dump to import, instead of '
                            'using pixel art image. Can be obtained by '
                            'dumping the memory of an NES emulator.'))

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
                            'tile is used, according to the following key:\n'
                            '1: white (unique tile),\n'
                            '2: yellow,\n'
                            '3: orange,\n'
                            '4: light green,\n'
                            '5: cyan,\n'
                            '6: magenta,\n'
                            '7: red,\n'
                            '8: green,\n'
                            '9: blue,\n'
                            '10: purple,\n'
                            '11+: grey'))

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

  parser.add_argument('--free-zone-view', dest='free_zone_view',
                      metavar='image',
                      help=('Output filename for free zone view to output. '
                            'Will show where zones are according to free '
                            'sprite traversal.'))

  parser.add_argument('--rect-cover-anon-view', dest='rect_cover_anon_view',
                      help=('Output filename for view that anonymizes the '
                            'input image, with rectilinear covering debug '
                            'data displayed on top of it.'))

  parser.add_argument('--rect-cover-steps-view', dest='rect_cover_steps_view',
                      help=('Output filename for view that adds information '
                            'about rectilinear covering\'s algorithm steps '
                            'on top of it.'))

  parser.add_argument('--use-legacy-views', dest='use_legacy_views',
                      action="store_true",
                      help=('Views created using legacy styles. Default is '
                            'false.'))
  args = parser.parse_args()
  if args.version:
    sys.stdout.write('makechr ' + __version__ + '\n')
    sys.exit(0)
  application = app.Application()
  if args.memimport and args.input:
    sys.stderr.write('Cannot both import memory and process input file')
    sys.exit(1)
  elif args.memimport and not os.path.isfile(args.memimport):
    sys.stderr.write('File not found: "%s"\n' % args.memimport)
    sys.exit(1)
  elif args.memimport:
    application.read_memory(args.memimport, 'ram', args)
  elif args.input and not os.path.isfile(args.input):
    sys.stderr.write('File not found: "%s"\n' % args.input)
    sys.exit(1)
  elif args.input and is_valiant(args.input):
    application.read_memory(args.input, 'valiant', args)
  elif args.input:
    try:
      img = Image.open(args.input)
    except IOError as e:
      sys.stderr.write('Not an image file: "%s"\n' % args.input)
      sys.exit(1)
    if args.output and (args.output.endswith('/') or
                        args.output.endswith('/.')):
      if not os.path.isdir(args.output):
        sys.stderr.write('Directory does not exist: "%s"\n' % args.output)
        sys.exit(1)
    try:
      if not application.run(img, args):
        sys.exit(1)
    except errors.CommandLineArgError as e:
      sys.stderr.write('Command-line error: %s\n' % e)
      sys.exit(1)
  else:
    parser.print_usage()
    sys.exit(1)
  sys.exit(0)


if __name__ == '__main__':
  run()
