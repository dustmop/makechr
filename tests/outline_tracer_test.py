import unittest

import context
from makechr import outline_tracer
from PIL import Image


class ImageClassifier(object):
  def __init__(self, img):
    self.img = img
    self.pixels = self.img.load()

  def is_clear(self, y, x):
    p = self.pixels[x,y]
    return p[0] == p[1] == p[2]


class OutlineTracerTests(unittest.TestCase):
  def test_outline_tracer(self):
    img = Image.open('testdata/geometric-outlines.png')
    classifier = ImageClassifier(img)
    width, height = img.size
    tracer = outline_tracer.OutlineTracer(height, width, classifier.is_clear)
    regions = tracer.find_regions()
    expect = [
      '#<RegionPerimeter 12 points=[y8,x16 y8,x24 y16,x24 y16,x48 y24,x48 y24,x40 y48,x40 y48,x32 y40,x32 y40,x8 y32,x8 y32,x16]>',

      '#<RegionPerimeter 12 points=[y8,x60 y8,x68 y21,x68 y21,x72 y8,x72 y8,x80 y24,x80 y24,x78 y29,x78 y29,x62 y24,x62 y24,x60]>',

      '#<RegionPerimeter 12 points=[y8,x93 y8,x104 y24,x104 y24,x108 y8,x108 y8,x119 y21,x119 y21,x116 y32,x116 y32,x96 y21,x96 y21,x93]>',

      '#<RegionPerimeter 10 points=[y8,x128 y8,x139 y24,x139 y24,x143 y8,x143 y8,x151 y32,x151 y32,x131 y21,x131 y21,x128]>',

      '#<RegionPerimeter 16 points=[y11,x160 y11,x170 y24,x170 y24,x174 y11,x174 y11,x184 y19,x184 y19,x182 y27,x182 y27,x176 y32,x176 y32,x168 y27,x168 y27,x162 y19,x162 y19,x160]>',

      '#<RegionPerimeter 14 points=[y11,x192 y11,x202 y24,x202 y24,x206 y11,x206 y11,x214 y27,x214 y27,x208 y32,x208 y32,x200 y27,x200 y27,x194 y19,x194 y19,x192]>',

      '#<RegionPerimeter 28 points=[y56,x16 y56,x24 y64,x24 y64,x32 y56,x32 y56,x40 y64,x40 y64,x48 y72,x48 y72,x40 y80,x40 y80,x48 y88,x48 y88,x40 y96,x40 y96,x32 y88,x32 y88,x24 y96,x24 y96,x16 y88,x16 y88,x8 y80,x8 y80,x16 y72,x16 y72,x8 y64,x8 y64,x16]>',

      '#<RegionPerimeter 12 points=[y56,x56 y56,x96 y64,x96 y64,x88 y72,x88 y72,x96 y80,x96 y80,x56 y72,x56 y72,x64 y64,x64 y64,x56]>',

      '#<RegionPerimeter 10 points=[y56,x109 y56,x120 y72,x120 y72,x124 y56,x124 y56,x132 y96,x132 y96,x112 y69,x112 y69,x109]>',

      '#<RegionPerimeter 16 points=[y59,x148 y59,x158 y72,x158 y72,x162 y59,x162 y59,x172 y67,x172 y67,x170 y91,x170 y91,x164 y96,x164 y96,x156 y91,x156 y91,x150 y67,x150 y67,x148]>',

      '#<RegionPerimeter 12 points=[y62,x184 y62,x192 y76,x192 y76,x195 y80,x195 y80,x199 y64,x199 y64,x207 y88,x207 y88,x187 y78,x187 y78,x184]>',

      '#<RegionPerimeter 14 points=[y112,x22 y112,x30 y120,x30 y120,x22 y122,x22 y122,x20 y128,x20 y128,x12 y124,x12 y124,x8 y116,x8 y116,x14 y114,x14 y114,x22]>',

      '#<RegionPerimeter 16 points=[y112,x40 y112,x48 y120,x48 y120,x51 y113,x51 y113,x59 y121,x59 y121,x52 y128,x52 y128,x57 y136,x57 y136,x41 y128,x41 y128,x44 y120,x44 y120,x40]>',

      '#<RegionPerimeter 20 points=[y112,x72 y112,x80 y117,x80 y117,x82 y112,x82 y112,x90 y120,x90 y120,x85 y122,x85 y122,x90 y130,x90 y130,x82 y125,x82 y125,x80 y130,x80 y130,x72 y122,x72 y122,x77 y120,x77 y120,x72]>',

      '#<RegionPerimeter 26 points=[y112,x112 y112,x120 y120,x120 y120,x112 y124,x112 y124,x123 y134,x123 y134,x125 y142,x125 y142,x117 y140,x117 y140,x115 y132,x115 y132,x108 y136,x108 y136,x104 y140,x104 y140,x96 y132,x96 y132,x100 y128,x100 y128,x107 y124,x107 y124,x104 y116,x104 y116,x112]>',

      '#<RegionPerimeter 26 points=[y114,x144 y114,x152 y122,x152 y122,x144 y124,x144 y124,x155 y134,x155 y134,x157 y142,x157 y142,x149 y140,x149 y140,x147 y132,x147 y132,x140 y136,x140 y136,x136 y140,x136 y140,x128 y132,x128 y132,x132 y128,x132 y128,x139 y126,x139 y126,x136 y118,x136 y118,x144]>',

      '#<RegionPerimeter 12 points=[y114,x160 y114,x168 y130,x168 y130,x171 y132,x171 y132,x175 y116,x175 y116,x183 y140,x183 y140,x163 y130,x163 y130,x160]>',

      '#<RegionPerimeter 14 points=[y114,x192 y114,x200 y128,x200 y128,x203 y132,x203 y132,x207 y116,x207 y116,x215 y140,x215 y140,x203 y136,x203 y136,x195 y130,x195 y130,x192]>',

      '#<RegionPerimeter 12 points=[y152,x24 y152,x32 y160,x32 y160,x26 y166,x26 y166,x18 y164,x18 y164,x12 y156,x12 y156,x16 y154,x16 y154,x24]>',

      '#<RegionPerimeter 16 points=[y152,x48 y152,x56 y159,x56 y159,x60 y165,x60 y165,x63 y173,x63 y173,x56 y175,x56 y175,x48 y173,x48 y173,x41 y165,x41 y165,x44 y159,x44 y159,x48]>',

      '#<RegionPerimeter 12 points=[y152,x80 y152,x88 y160,x88 y160,x86 y166,x86 y166,x93 y174,x93 y174,x77 y166,x77 y166,x78 y158,x78 y158,x80]>',

      '#<RegionPerimeter 12 points=[y153,x101 y153,x109 y161,x109 y161,x111 y167,x111 y167,x118 y175,x118 y175,x102 y167,x102 y167,x103 y161,x103 y161,x101]>',

      '#<RegionPerimeter 10 points=[y154,x136 y154,x144 y162,x144 y162,x143 y177,x143 y177,x135 y164,x135 y164,x128 y156,x128 y156,x136]>',

      '#<RegionPerimeter 12 points=[y154,x160 y154,x168 y159,x168 y159,x174 y167,x174 y167,x173 y182,x173 y182,x165 y170,x165 y170,x157 y162,x157 y162,x160]>',

      '#<RegionPerimeter 14 points=[y184,x16 y184,x24 y192,x24 y192,x22 y197,x22 y197,x28 y205,x28 y205,x21 y206,x21 y206,x13 y198,x13 y198,x14 y190,x14 y190,x16]>',

      '#<RegionPerimeter 14 points=[y184,x36 y184,x44 y192,x44 y192,x42 y198,x42 y198,x49 y206,x49 y206,x41 y205,x41 y205,x33 y197,x33 y197,x34 y190,x34 y190,x36]>',

      '#<RegionPerimeter 14 points=[y184,x56 y184,x64 y192,x64 y192,x62 y196,x62 y196,x68 y204,x68 y204,x63 y205,x63 y205,x55 y198,x55 y198,x54 y190,x54 y190,x56]>',

      '#<RegionPerimeter 16 points=[y184,x78 y184,x86 y192,x86 y192,x84 y197,x84 y197,x85 y198,x85 y198,x90 y206,x90 y206,x82 y205,x82 y205,x77 y198,x77 y198,x76 y190,x76 y190,x78]>',

      '#<RegionPerimeter 20 points=[y184,x96 y184,x104 y190,x104 y190,x106 y184,x106 y184,x114 y192,x114 y192,x110 y196,x110 y196,x117 y204,x117 y204,x109 y198,x109 y198,x107 y204,x107 y204,x99 y196,x99 y196,x102 y192,x102 y192,x96]>',
    ]

    for i, r in enumerate(regions):
      self.assertEqual('%s' % r, expect[i])


if __name__ == '__main__':
  unittest.main()
