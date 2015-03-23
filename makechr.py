import argparse
import image_processor
from PIL import Image
import rom_builder
import view_renderer


def run():
  parser = argparse.ArgumentParser(description='Make chr data files and ' +
                                   'other NES graphics files')
  parser.add_argument('input', type=str, help='filename for pixel art image')
  parser.add_argument('-X', dest='experimental', action='store_true',
                      required=True,
                      help='enable experimental features (required)')
  parser.add_argument('-c', dest='compile', metavar='rom filename',
                      help='filename for compiled NES rom')
  parser.add_argument('-e', dest='error_outfile', metavar='image filename',
                      help='filename for error image')
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
  args = parser.parse_args()

  img = Image.open(args.input)
  processor = image_processor.ImageProcessor()
  processor.process_image(img, args.error_outfile)
  if processor.err().has():
    es = processor.err().get()
    print('Found {0} error{1}:'.format(len(es), 's'[len(es) == 1:]))
    for e in es:
      print('{0} {1}'.format(type(e).__name__, e))
    if args.error_outfile:
      print('Errors displayed in "{0}"'.format(args.error_outfile))
      renderer = view_renderer.ViewRenderer()
      renderer.create_error_view(args.error_outfile, img, processor.err().get())
    return
  if args.compile:
    builder = rom_builder.RomBuilder()
    builder.build(args.compile)
  if args.palette_view:
    renderer = view_renderer.ViewRenderer()
    renderer.create_palette_view(args.palette_view, processor.palette())
  if args.colorization_view:
    renderer = view_renderer.ViewRenderer()
    renderer.create_colorization_view(args.colorization_view,
        processor.artifacts(), processor.palette())
  if args.reuse_view:
    renderer = view_renderer.ViewRenderer()
    renderer.create_reuse_view(args.reuse_view, processor.artifacts(),
        processor.nt_count())
  if args.nametable_view:
    renderer = view_renderer.ViewRenderer()
    renderer.create_nametable_view(args.nametable_view, processor.artifacts())


if __name__ == '__main__':
  run()
