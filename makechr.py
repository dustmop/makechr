import argparse
import image_processor
from PIL import Image
import sys


def run():
  parser = argparse.ArgumentParser(description='Make chr data files and ' +
                                   'other NES graphics files')
  parser.add_argument('input', type=str, help='filename for pixel art image')
  parser.add_argument('-X', dest='experimental', action='store_true',
                      required=True,
                      help='enable experimental features (required)')
  parser.add_argument('-c', dest='compile', metavar='rom filename',
                      help='filename for compiled NES rom')
  parser.add_argument('-e', dest='error', metavar='image filename',
                      help='filename for error image')
  args = parser.parse_args()

  # TODO: -c flag for compiled rom
  # TODO: -e flag for error image filename
  img = Image.open(args.input)
  processor = image_processor.ImageProcessor()
  processor.process_image(img)


if __name__ == '__main__':
  run()
