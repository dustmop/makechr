import image_processor
import ppu_memory
import rom_builder
import view_renderer


class Application(object):
  def run(self, img, args):
    processor = image_processor.ImageProcessor()
    processor.process_image(img, args.palette)
    if processor.err().has():
      es = processor.err().get()
      print('Found {0} error{1}:'.format(len(es), 's'[len(es) == 1:]))
      for e in es:
        print('{0} {1}'.format(type(e).__name__, e))
      if args.error_outfile:
        print('Errors displayed in "{0}"'.format(args.error_outfile))
        errs = processor.err().get(include_dups=True)
        renderer = view_renderer.ViewRenderer()
        renderer.create_error_view(args.error_outfile, img, errs)
      return
    self.create_views(processor.ppu_memory(), processor, args, img)
    self.create_output(processor.ppu_memory(), args)
    self.show_stats(processor.ppu_memory(), processor, args)

  def create_views(self, ppu_memory, processor, args, img):
    if args.palette_view:
      renderer = view_renderer.ViewRenderer()
      renderer.create_palette_view(args.palette_view, ppu_memory)
    if args.colorization_view:
      renderer = view_renderer.ViewRenderer()
      renderer.create_colorization_view(args.colorization_view,
          ppu_memory, processor.artifacts(), processor.color_manifest())
    if args.reuse_view:
      renderer = view_renderer.ViewRenderer()
      renderer.create_reuse_view(args.reuse_view, ppu_memory,
          processor.nt_count())
    if args.nametable_view:
      renderer = view_renderer.ViewRenderer()
      renderer.create_nametable_view(args.nametable_view, ppu_memory)
    if args.chr_view:
      renderer = view_renderer.ViewRenderer()
      renderer.create_chr_view(args.chr_view, ppu_memory)
    if args.grid_view:
      renderer = view_renderer.ViewRenderer()
      renderer.create_grid_view(args.grid_view, img)

  def create_output(self, ppu_memory, args):
    out_tmpl = args.output or '%s.dat'
    if not '%s' in out_tmpl:
      raise CommandLineArgError('output needs "%s" in its template')
    ppu_memory.save(out_tmpl)
    if args.compile:
      builder = rom_builder.RomBuilder()
      builder.build(ppu_memory, args.compile)

  def show_stats(self, ppu_memory, processor, args):
    print('Number of dot-profiles: {0}'.format(processor.dot_manifest().size()))
    print('Number of tiles: {0}'.format(len(ppu_memory.chr_data)))
    print('Palette: {0}'.format(ppu_memory.palette))
