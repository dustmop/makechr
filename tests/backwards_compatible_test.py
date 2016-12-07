import general_app_test_util
import unittest

import context
from makechr.gen import valiant_pb2 as valiant #errors, image_processor

import os
from PIL import Image
import tempfile


def downgrade_to_deprecated_proto(obj):
  # Future version
  if not obj.HasField('body'):
    return
  body = obj.body
  # Deprecated version
  data = obj.data
  data_settings = data.settings
  data_settings.bg_color = body.settings.bg_color
  # Each packet
  for i,packet in enumerate(body.packets):
    binary = data.binaries.add()
    binary.CopyFrom(packet.binary)
    component = data.components.add()
    component.role = packet.role
    component.binary_index = i
    if packet.name:
      component.name = packet.name
    metadata = packet.metadata
    if metadata.HasField('chr_metadata'):
      data_settings.chr_metadata.add().CopyFrom(metadata.chr_metadata)
    if metadata.HasField('palette_metadata'):
      data_settings.palette_metadata.add().CopyFrom(metadata.palette_metadata)
  # Clean-up
  obj.ClearField('body')


def save_proto(obj, outfile):
  serialized = obj.SerializeToString()
  fp = open(outfile, 'wb')
  fp.write(serialized)
  fp.close()



class BackwardsCompatibleTests(general_app_test_util.GeneralAppTests):
  def test_basic(self):
    self.assertDowngrade('full-image.o')

  def test_bg_color(self):
    self.assertDowngrade('full-image-bg-color.o')

  def test_order1(self):
    self.assertDowngrade('full-image-order1.o')

  def test_traverse_block(self):
    self.assertDowngrade('full-image-traverse-block.o')

  def test_offset_normal(self):
    self.assertDowngrade('offset-image-normal.o')

  def test_offset_locked(self):
    self.assertDowngrade('offset-image-locked.o')

  def test_reticule(self):
    self.assertDowngrade('reticule.o')

  def test_reticule_more(self):
    self.assertDowngrade('reticule-more.o')

  def test_reticule_8x16(self):
    self.assertDowngrade('reticule-8x16.o')

  def assertDowngrade(self, basename):
    future_file = os.path.join('testdata/', basename)
    fp = open(future_file, 'r')
    content = fp.read()
    fp.close()
    obj = valiant.ObjectFile()
    obj.ParseFromString(content)
    downgraded_file = os.path.join(tempfile.mkdtemp(), basename)
    downgrade_to_deprecated_proto(obj)
    save_proto(obj, downgraded_file)
    deprecated_file = os.path.join('testdata/deprecated/', basename)
    self.assert_file_eq(downgraded_file, deprecated_file)


if __name__ == '__main__':
  unittest.main()
