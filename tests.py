import unittest

import palette_test
import tile_test


suite = unittest.TestSuite()
suite.addTest(unittest.makeSuite(tile_test.TileTests))
suite.addTest(unittest.makeSuite(palette_test.PaletteTests))
runner = unittest.TextTestRunner()
runner.run(suite)
