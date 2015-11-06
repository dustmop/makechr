import unittest

import app_test
import memory_importer_test
import palette_test
import rom_builder_test
import tile_test


suite = unittest.TestSuite()
suite.addTest(unittest.makeSuite(app_test.AppTests))
suite.addTest(unittest.makeSuite(memory_importer_test.MemoryImporterTests))
suite.addTest(unittest.makeSuite(palette_test.PaletteTests))
suite.addTest(unittest.makeSuite(rom_builder_test.RomBuilderTests))
suite.addTest(unittest.makeSuite(tile_test.TileTests))
runner = unittest.TextTestRunner()
runner.run(suite)
