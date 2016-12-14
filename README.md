# makechr

makechr is a tool for generating NES graphics. Its primary operation is to take pixel art images and split it into components: chr, nametable, palette, attributes, and spritelist.

The goals of makechr are to be portable (written in python), fast (can process a busy image with 256 tiles and 4 full palettes in <300ms), powerful, easy to understand, and usable in command-line based builds.

Input images should be 256px wide and 240px high, representing a full nametable, and must follow NES attribute and palette restrictions. An RGB palette is hard-coded in rgb.py, other palettes are not yet supported.

Alternatively, if an input image is exactly 128px by 128px, representing a page of CHR data, and the "-l lock tiles" flag is set, image processing will be limited to 8 blocks square. This will end up with a CHR bank that resembles the input image.

# Example usage

    makechr image.png

This will output four files: chr.dat, nametable.dat, palette.dat, attribute.dat.

# Dependencies

    Pillow
    protobuf

After installing protobuf, run build-proto.sh to generate the python protocol buffer library in the gen/ directory.

# Command-line options

    -o [output]      Either an output template or the name of the output object.
                     A template needs to have "%s" in it. An object needs to
                     end in ".o". See valiant.proto for the format of objects.

    -c [rom]         Create an NES rom file that just displays the image.

    -e [error_file]  Output errors to an image file.

    -p [palette]     Palette to use for the input image, either a literal
                     representation, or a file made by --makepal. If not set,
                     makechr will attempt to automatically derive a palette,
                     or extract a palette if the image uses indexed color. See
                     below for the syntax for literal palettes.

    -b [background_color] | [background_look=background_fill]
                     Background color for the palette. If the palette is not
                     provided, the derived palette will used this color. If the
                     palette is provided, its background color must match.
                     Color must be in hexadecimal. Alternatively, a pair
                     of colors may be provided, separated by an "=" operator.
                     The first color is the "look", which appears in the input
                     image, the second color is the "fill", which is output to
                     the palette.

    -s               Sprite mode. Will prevent nametable and attribute
                     components from being output. Output spritelist component,
                     which is a list of 4-tuples containing sprite data, in the
                     order (y, tile, attribute, x). Write the palette as a
                     sprite palette by using address 0x10 instead of 0x00.
                     Default the chr order to 0x1000 instead of 0x0000.

    -l               Lock tiles. Won't remove duplicates, leaving all tiles in
                     the same position they appear in in the pixel art input.
                     Will only process the first 256 tiles in the input. If the
                     image is only 128px by 128px, then only 8 blocks square
                     will be processed.

    -t [strategy]    Strategy for traversing tile during CHR and nametable
                     generation. Can be "horizontal", "block", "free", or.
                     "8x16". Horizontal will traverse tiles left to right,
                     top to bottom. Block will traverse blocks at a top,
                     top-left to top-right to bottom-left to bottom-right.
                     Free is only usable with sprites and a background color
                     spec, and will look for sprites positioned freely in the
                     image. 8x16 is only usable with sprites and will create
                     data that is suitable for 8x16 mode. (default is
                     horizontal)

    -r [chr_order]   Order that the CHR data appears in memory relative to
                     other CHR data. Can be 0 or 1. If 0, then the CHR data
                     appears at 0x0000. If 1, then the CHR data appears at
                     0x1000. (default is 0, -s can override this)

    -z               Whether to show statistics at the end of processing.
                     Displays number of dot-profiles, number of tiles, and
                     the palette.

    -m [mem_file]    A ppu memory dump, representing the state of ppu ram. Used
                     instead of a pixel art image as a graphics source. Can
                     be obtained by dumping the memory of an NES emulator.

    --makepal        Generate a palette object file from an image, or just
                     output binary data if the file name ends in .bin or .dat.

    --allow-overflow    [comps]  Components that allow overflow. Only "s" for
                                 "spritelist" is currently implemented.

    --palette-view      [image]  Output the palette to an image file.

    --colorization-view [image]  Output an image file with the palette for
                                 each blocks according to attributes.

    --reuse-view        [image]  Output an image file showing how many times
                                 each tile was reused according to the
                                 following key:
                                 1: black (unique tile)
                                 2: dark green
                                 3: light green
                                 4: cyan
                                 5: blue
                                 6: dark purple
                                 7: light purple
                                 8: red
                                 9: orange
                                 10: yellow
                                 11+: white (common tile)

    --nametable-view    [image]  Output an image file showing the nametable
                                 value for each position, in hexidecimal.
                                 Positions that have value 0 do not output
                                 anything.

    --chr-view          [image]  Output an image file showing the entire
                                 page of chr.

    --grid-view         [image]  Output an image file showing the input
                                 pixel art with the grid applied.

    --free-zone-view    [image]  Output an image file showing the zones
                                 created by free sprite traversal.

# Palette literal syntax

    palette  = "P/" + (option + "/"){1-4}
    option   = hexcolor + ("-" hexcolor){1-3}
    hexcolor = [0-9a-f]{2}

Example:

    P/0f-10-01-02/0f-10-30/

This is a palette using 2 options. It has the background color $0f (black).
The first option has 4 colors, the second option has only 3 colors.
