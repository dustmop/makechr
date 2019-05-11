import collections
import errors
import memory_importer
import os
import pixel_art_renderer
import ppu_memory
import rom_builder
import view_renderer
import sys


eight_by_sixteen_processor = None
free_sprite_processor = None
decompose_sprites_processor = None
image_processor = None
makepal_processor = None


class Application(object):
  def run(self, img, args):
    traversal = self.get_traversal(args.traversal_strategy)
    if args.makepal:
      global makepal_processor
      if not makepal_processor:
        import makepal_processor
      processor = makepal_processor.MakepalProcessor()
      processor.process_image(img, args)
      if processor.err().has():
        self.handle_errors(processor.err(), img, args)
        return False
      processor.create_output(args.output)
      return True
    elif 'free' in traversal:
      # DEPRECATED
      if not args.is_sprite or args.bg_color.fill is None:
        raise errors.CommandLineArgError(
          'Traversal strategy \'%s\' requires -s and -b `mask=fill` flags' % (
            traversal))
      global free_sprite_processor
      if not free_sprite_processor:
        import free_sprite_processor
      processor = free_sprite_processor.FreeSpriteProcessor(traversal)
      processor.set_verbose('--verbose' in sys.argv)
      processor.process_image(img, args.palette, args.bg_color.mask,
                              args.bg_color.fill, args.is_locked_tiles,
                              args.lock_sprite_flips, args.allow_overflow)
    elif args.decompose_sprites:
      # --decompose_sprites is a processor mode, not a traversal style.
      # Can be combined with --free 8x16. Implies -s
      # TODO: Make -b optional, derive it if possible
      if args.bg_color.fill is None:
        raise errors.CommandLineArgError(
          'Decompose sprites mode requires -b `mask=fill` flags')
      global decompose_sprites_processor
      if not decompose_sprites_processor:
        import decompose_sprites_processor
      processor = decompose_sprites_processor.DecomposeSpritesProcessor()
      # TODO: lock_sprite_flags, is_locked_tiles, allow_overflow?
      processor.process_image(img, args.palette,
                              args.bg_color.mask, args.bg_color.fill,
                              {'anon_view': args.rect_cover_anon_view,
                               'steps_view': args.rect_cover_steps_view})
      if processor.err().has():
        self.handle_errors(processor.err(), img, args)
        return False
      args.is_sprite = True
    elif traversal == '8x16':
      if not args.is_sprite:
        raise errors.CommandLineArgError('Traversal strategy \'8x16\' requires '
                                         '-s flag')
      global eight_by_sixteen_processor
      if not eight_by_sixteen_processor:
        import eight_by_sixteen_processor
      processor = eight_by_sixteen_processor.EightBySixteenProcessor()
      processor.process_image(img, args.palette, args.bg_color.mask,
                              args.bg_color.fill, traversal, args.is_sprite,
                              args.is_locked_tiles, args.lock_sprite_flips,
                              args.allow_overflow)
    else:
      global image_processor
      if not image_processor:
        import image_processor
      processor = image_processor.ImageProcessor()
      processor.process_image(img, args.palette, args.bg_color.mask,
                              args.bg_color.fill, traversal, args.is_sprite,
                              args.is_locked_tiles, args.lock_sprite_flips,
                              args.allow_overflow)
    if args.bg_color.fill:
      processor.ppu_memory().override_bg_color(args.bg_color.fill)
    self.create_views(processor.ppu_memory(), args, img)
    if processor.err().has():
      self.handle_errors(processor.err(), img, args)
      return False
    self.create_output(processor.ppu_memory(), args, traversal)
    if args.show_stats:
      self.show_stats(processor.ppu_memory(), processor, args)
    return True

  def get_traversal(self, strategy):
    if not strategy or strategy == 'h' or strategy == 'horizontal':
      return 'horizontal'
    elif strategy == 'v' or strategy == 'vertical':
      return 'vertical'
    elif strategy == 'b' or strategy == 'block':
      return 'block'
    elif strategy == 'f' or strategy == 'free':
      return 'free'
    elif strategy == '8' or strategy == '8x16':
      return '8x16'
    elif strategy == 'free-8x16':
      return 'free-8x16'
    else:
      raise errors.UnknownStrategy(strategy)

  def read_memory(self, filename, kind, args):
    importer = memory_importer.MemoryImporter()
    mem = importer.read(filename, kind)
    img = None
    if args.grid_view:
      renderer = pixel_art_renderer.PixelArtRenderer()
      img = renderer.render(mem)
    self.create_views(mem, args, img)
    self.create_output(mem, args, self.get_traversal(None))

  def create_views(self, mem, args, img, scale=None):
    if args.use_legacy_views:
      renderer = view_renderer.ViewRenderer(is_legacy=True)
    else:
      renderer = view_renderer.ViewRenderer(is_legacy=False, scale=scale)
    if args.palette_view:
      renderer.create_palette_view(args.palette_view, mem, args.is_sprite)
    if args.colorization_view:
      renderer.create_colorization_view(args.colorization_view, mem,
                                        args.is_sprite)
    if args.reuse_view:
      nt_inverter = mem.build_nt_inverter()
      renderer.create_reuse_view(args.reuse_view, mem, nt_inverter)
    if args.nametable_view:
      renderer.create_nametable_view(args.nametable_view, mem)
    if args.chr_view:
      renderer.create_chr_view(args.chr_view, mem)
    if args.grid_view:
      renderer.create_grid_view(args.grid_view, img)
    if args.free_zone_view:
      renderer.create_free_zone_view(args.free_zone_view, img, mem)

  def create_output(self, mem, args, traversal):
    config = ppu_memory.PpuMemoryConfig(
      chr_order=args.order, traversal=traversal, is_sprite=args.is_sprite,
      is_locked_tiles=args.is_locked_tiles,
      lock_sprite_flips=args.lock_sprite_flips,
      select_chr_plane=args.select_chr_plane)
    if args.vertical_pixel_display:
      mem.chr_set.vertical_pixel_display()
    if args.output == '/dev/null':
      # Ignore output.
      pass
    elif args.output and args.output.endswith('.o'):
      # Output as a valiant object file.
      mem.save_valiant(args.output, config)
    elif args.output and args.output.endswith('.png'):
      # Render an image.
      renderer = pixel_art_renderer.PixelArtRenderer()
      img = renderer.render(mem)
      img.save(args.output)
    else:
      # Output as multiple files using a template.
      out_tmpl = args.output or '%s.dat'
      if out_tmpl[-1] == '/' or os.path.isdir(out_tmpl):
        out_tmpl = os.path.join(out_tmpl, '%s.dat')
      if not '%s' in out_tmpl:
        raise errors.CommandLineArgError('output needs "%s" in its template')
      mem.save_template(out_tmpl, config)
    if args.compile:
      # Compile a runnable ROM.
      builder = rom_builder.RomBuilder()
      builder.build(mem, args.compile)

  def show_stats(self, mem, processor, args):
    print('Number of dot-profiles: {0}'.format(len(processor.dot_manifest())))
    print('Number of tiles: {0}'.format(mem.chr_set.size()))
    pal = mem.palette_spr if args.is_sprite else mem.palette_nt
    print('Palette: {0}'.format(pal))

  def handle_errors(self, error_provider, img, args):
    es = error_provider.get()
    sys.stderr.write('Found {0} error{1}:\n'.format(
      len(es), 's'[len(es) == 1:]))
    for e in es:
      sys.stderr.write('{0} {1}\n'.format(type(e).__name__, e))
    if args.error_outfile:
      sys.stderr.write('Errors displayed in "{0}"\n'.format(args.error_outfile))
      errors_with_dups = error_provider.get(include_dups=True)
      renderer = view_renderer.ViewRenderer()
      renderer.create_error_view(args.error_outfile, img, errors_with_dups)
    else:
      sys.stderr.write('To see errors visually, use the ' +
                       '"-e <error_image.png>" command-line option.\n')
