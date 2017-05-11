import errors


class WrappedImagePalette(object):
  """Wrap the undocumented and unreliable PIL.ImagePalette.

  PIL.ImagePalette is undocumented and mysterious. It changes behavior between
  different versions of the library. Wrap it, and try to provide a more sane
  interface, by detecting what the provided bytearray actually represents.
  """
  def __init__(self):
    self.palette = None
    self.format = None
    self.elems = None
    self.invert = False

  @staticmethod
  def from_image(img):
    make = WrappedImagePalette()
    make.palette = img.palette.palette
    make.format = img.format
    make._build()
    return make

  def _build(self):
    bytes = self.palette
    # Some file formats reverse the color order.
    if self.format == 'BMP':
      self.invert = True
    bytes = [ord(b) for b in bytes]
    # Some versions of library use 3 bytes per color, other use 4 per color.
    if len(bytes) == 48:
      unit_size = 3
    elif len(bytes) == 64:
      unit_size = 4
    elif len(bytes) == 768:
      unit_size = 3
    elif len(bytes) == 1024:
      unit_size = 4
    else:
      raise errors.PaletteExtractionError('Bad palette size %s' % len(bytes))
    self.elems = [bytes[i*unit_size:i*unit_size+3] for i in xrange(16)]

  def get(self, i):
    if self.invert:
      return self.elems[i][::-1]
    return self.elems[i]
