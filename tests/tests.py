import unittest

import app_bin_test
import app_palette_test
import app_sprite_test
import app_valiant_test
import bg_color_spec_test
import chr_data_test
import guess_best_palette_test
import integration_test
import memory_importer_test
import palette_test
import rom_builder_test
import tile_test


suite = unittest.TestSuite()
suite.addTest(unittest.makeSuite(app_bin_test.AppBinTests))
suite.addTest(unittest.makeSuite(app_palette_test.AppPaletteTests))
suite.addTest(unittest.makeSuite(app_sprite_test.AppSpriteTests))
suite.addTest(unittest.makeSuite(app_valiant_test.AppValiantTests))
suite.addTest(unittest.makeSuite(bg_color_spec_test.BgColorSpecTests))
suite.addTest(unittest.makeSuite(chr_data_test.ChrDataTests))
suite.addTest(unittest.makeSuite(guess_best_palette_test.GuessBestPaletteTests))
suite.addTest(unittest.makeSuite(integration_test.IntegrationTests))
suite.addTest(unittest.makeSuite(memory_importer_test.MemoryImporterTests))
suite.addTest(unittest.makeSuite(palette_test.PaletteTests))
suite.addTest(unittest.makeSuite(rom_builder_test.RomBuilderTests))
suite.addTest(unittest.makeSuite(tile_test.TileTests))
runner = unittest.TextTestRunner()
runner.run(suite)
