import image_processor
from PIL import Image
import sys


def run():
  filename = sys.argv[1]
  img = Image.open(filename)
  processor = image_processor.ImageProcessor()
  processor.process_image(img)


if __name__ == '__main__':
  run()
