import unittest

import context
from makechr import app, bg_color_spec, image_processor, free_sprite_processor
from makechr import eight_by_sixteen_processor

import filecmp
import os
import sys
import tempfile


class MockArgs(object):
  def __init__(self):
    self.dir = tempfile.mkdtemp()
    self.palette_view = self.tmppng('pal')
    self.colorization_view = self.tmppng('color')
    self.reuse_view = self.tmppng('reuse')
    self.nametable_view = self.tmppng('nt')
    self.chr_view = self.tmppng('chr')
    self.grid_view = self.tmppng('grid')
    self.free_zone_view = None
    self.bg_color = bg_color_spec.default()
    self.platform = None
    self.traversal = 'horizontal'
    self.is_sprite = False
    self.is_locked_tiles = False
    self.lock_sprite_flips = False
    self.allow_overflow = []
    self.use_legacy_views = False
    self.order = None
    self.compile = None
    self.vertical_pixel_display = False
    self.select_chr_plane = None
    self.output = self.tmpfile('actual-%s.dat')

  def clear_views(self):
    self.palette_view = None
    self.colorization_view = None
    self.reuse_view = None
    self.nametable_view = None
    self.chr_view = None
    self.grid_view = None
    self.free_zone_view = None

  def tmppng(self, name):
    return os.path.join(self.dir, 'actual-%s.png' % name)

  def tmpfile(self, template):
    return os.path.join(self.dir, template)


class GeneralAppTests(unittest.TestCase):
  def setUp(self):
    self.args = MockArgs()
    self.golden_file_prefix = 'full-image'

  def process_image(self, img, palette_text=None, auto_sprite_bg=False,
                    traversal=None):
    if 'free' in self.args.traversal:
      self.processor = free_sprite_processor.FreeSpriteProcessor(
        self.args.traversal)
      self.processor.set_verbose('--verbose' in sys.argv)
      self.processor.process_image(img, palette_text,
                                   self.args.bg_color.mask,
                                   self.args.bg_color.fill,
                                   self.args.platform,
                                   self.args.is_locked_tiles,
                                   self.args.lock_sprite_flips,
                                   self.args.allow_overflow)
    elif self.args.traversal == '8x16':
      self.processor = eight_by_sixteen_processor.EightBySixteenProcessor()
      self.processor.process_image(img, palette_text,
                                   self.args.bg_color.mask,
                                   self.args.bg_color.fill,
                                   self.args.platform,
                                   self.args.traversal,
                                   self.args.is_sprite,
                                   self.args.is_locked_tiles,
                                   self.args.lock_sprite_flips,
                                   self.args.allow_overflow)
    else:
      self.processor = image_processor.ImageProcessor()
      if auto_sprite_bg:
        self.processor._test_only_auto_sprite_bg = auto_sprite_bg
      self.processor.process_image(img, palette_text,
                                   self.args.bg_color.mask,
                                   self.args.bg_color.fill,
                                   self.args.platform,
                                   self.args.traversal,
                                   self.args.is_sprite,
                                   self.args.is_locked_tiles,
                                   self.args.lock_sprite_flips,
                                   self.args.allow_overflow)
    self.ppu_memory = self.processor.ppu_memory()
    self.err = self.processor.err()

  def create_output(self):
    a = app.Application()
    if self.args.bg_color.fill:
      self.ppu_memory.override_bg_color(self.args.bg_color.fill)
    a.create_output(self.ppu_memory, self.args, self.args.traversal,
                    self.args.platform)

  def assert_output_result(self, name, golden_suffix=''):
    actual_file = self.args.output % name
    expect_file = self.golden(name + golden_suffix, 'dat')
    self.assert_file_eq(actual_file, expect_file)

  def assert_output_result_json(self, name, golden_suffix=''):
    actual_file = self.args.output % name
    expect_file = self.golden(name + golden_suffix, 'json')
    self.assert_file_eq(actual_file.replace('.dat', '.json'), expect_file)

  def assert_not_exist(self, name):
    missing_file = self.args.output % name
    self.assertFalse(os.path.exists(missing_file))

  def golden(self, name, ext):
    if name:
      return 'testdata/%s-%s.%s' % (self.golden_file_prefix, name, ext)
    else:
      return 'testdata/%s.%s' % (self.golden_file_prefix, ext)

  def assert_file_eq(self, actual_file, expect_file):
    self.assertTrue(filecmp.cmp(actual_file, expect_file, shallow=False),
                    "Files did not match actual:%s expect:%s" % (
                      actual_file, os.path.abspath(expect_file)))
