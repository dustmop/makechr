import binary_output
import image_processor
import rom_builder
import view_renderer


class Application(object):
  def run(self, img, args):
    processor = image_processor.ImageProcessor()
    processor.process_image(img, args.palette, args.error_outfile)
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
    self.create_views(processor, args, img)
    self.create_output(processor, args)
    self.show_stats(processor, args)

  def create_views(self, processor, args, img):
    if args.palette_view:
      renderer = view_renderer.ViewRenderer()
      renderer.create_palette_view(args.palette_view, processor.palette())
    if args.colorization_view:
      renderer = view_renderer.ViewRenderer()
      renderer.create_colorization_view(args.colorization_view,
          processor.artifacts(), processor.palette(),
          processor.color_manifest())
    if args.reuse_view:
      renderer = view_renderer.ViewRenderer()
      renderer.create_reuse_view(args.reuse_view, processor.artifacts(),
          processor.nt_count())
    if args.nametable_view:
      renderer = view_renderer.ViewRenderer()
      renderer.create_nametable_view(args.nametable_view, processor.artifacts())
    if args.chr_view:
      renderer = view_renderer.ViewRenderer()
      renderer.create_chr_view(args.chr_view, processor.chr_data())
    if args.grid_view:
      renderer = view_renderer.ViewRenderer()
      renderer.create_grid_view(args.grid_view, img)

  def create_output(self, processor, args):
    out_tmpl = args.output or '%s.dat'
    if not '%s' in out_tmpl:
      raise CommandLineArgError('output needs "%s" in its template')
    output = binary_output.BinaryOutput(out_tmpl)
    output.save_nametable(processor.artifacts())
    output.save_chr(processor.chr_data())
    output.save_palette(processor.palette())
    output.save_attribute(processor.artifacts())
    if args.compile:
      builder = rom_builder.RomBuilder()
      builder.build(output, args.compile)

  def show_stats(self, processor, args):
    print('Number of dot-profiles: {0}'.format(processor.dot_manifest().size()))
    print('Number of tiles: {0}'.format(len(processor.chr_data())))
    print('Palette: {0}'.format(processor.palette()))
