# makechr

makechr is a tool for generating NES graphics. Its primary operation is to take pixel art images and split it into four components: chr, nametable, palette, and attributes.

The goals of makechr are to be portable (written in python), fast (can process a busy image with 256 tiles and 4 full palettes in about 400ms), powerful, easy to understand, and usable in command-line based builds.

Input images should be 256px wide and 240px high, representing a full nametable, and must follow NES attribute and palette restrictions. An RGB palette is hard-coded in rgb.py, other palettes are not yet supported.

Alternatively, if an input image is exactly 128px by 128px, representing a page of CHR data, and the "-l lock tiles" flag is set, image processing will be limited to 8 blocks square. This will end up with a CHR bank that resembles the input image.

# Example usage

    python makechr.py -X image.png

This will output four files: chr.dat, nametable.dat, palette.dat, attribute.dat. The -X command-line argument enables experimental features, and is required because all of makechr is experimental at the moment. The future plan is to finalize the command-line API, then remove the requirement for this argument.

# Dependencies

    Pillow
    protobuf

After installing protobuf, run build-proto.sh to generate the python protocol buffer library in the gen/ directory.

# Command-line options

    -X               Enable experimental features. Required.

    -c [rom_file]    Create an NES rom file that just displays the image.

    -e [error_file]  Output errors to an image file.

    -p [palette]     Palette to use for the input image. If not set, makechr
                     will attempt to automatically derive a palette. See below
                     for the palette syntax.

    -o [output]      Either an output template or the name of the output object.
                     A template needs to have "%s" in it. An object needs to
                     end in ".o".

    -m [mem_file]    A ppu memory dump, representing the state of ppu ram. Used
                     instead of a pixel art image as a graphics source.

    -l               Lock tiles. Won't remove duplicates, leaving all tiles in
                     the same position they appear in in the pixel art input.
                     Will only process the first 256 tiles in the input. If the
                     image is only 128px by 128px, then only 8 blocks square
                     will be processed.

    --palette-view      [view_file]  Output the palette to an image file.

    --colorization-view [view_file]  Output an image file with the palette for
                                     each blocks according to attributes.

    --reuse-view        [view_file]  Output an image file showing how many times
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

    --nametable-view    [view_file]  Output an image file showing the nametable
                                     value for each position, in hexidecimal.
                                     Positions that have value 0 do not output
                                     anything.

    --chr-view          [view_file]  Output an image file showing the entire
                                     page of chr.

    --grid-view         [view_file]  Output an image file showing the input
                                     pixel art with the grid applied.

# Palette syntax

    palette  = "P/" + (option + "/"){1-4}
    option   = hexcolor + ("-" hexcolor){1-3}
    hexcolor = [0-9a-f]{2}

Example:

    P/0f-10-01-02/0f-10-30/

This is a palette using 2 options. It has the background color $0f (black).
The first option has 4 colors, the second option has only 3 colors.
