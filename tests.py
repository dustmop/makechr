import unittest

import app_test
import palette_test
import tile_test


suite = unittest.TestSuite()
suite.addTest(unittest.makeSuite(app_test.AppTests))
suite.addTest(unittest.makeSuite(palette_test.PaletteTests))
suite.addTest(unittest.makeSuite(tile_test.TileTests))
runner = unittest.TextTestRunner()
runner.run(suite)
