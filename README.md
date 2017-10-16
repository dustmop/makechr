# makechr

makechr is a tool for generating NES graphics. Its primary operation is to take pixel art images and split it into components: chr, nametable, palette, attributes, and spritelist.

The goals of makechr are to be portable (written in python), fast (can process a busy image with 256 tiles and 4 full palettes in <300ms), powerful, easy to understand, and usable in command-line based builds. A GUI is available as well, though it is missing a few features.

Windows GUI builds are available in releases.

Input images should be 256px wide and 240px high, representing a full nametable, and must follow NES attribute and palette restrictions. Smaller imagse will have padded nametables, while images with greater width will result in up to 2 nametables, assuming horizontal arrangement.

An RGB palette is hard-coded in rgb.py, other palettes are not yet supported.

# Example usage (command-line)

    makechr image.png

This will output four files: chr.dat, nametable.dat, palette.dat, attribute.dat.

# Dependencies

    Pillow
    protobuf
    wxpython (GUI only)
    watchdog (GUI only)

# Command-line options

Run `makechr -h` to get details on command-line options.

    --version        See the current version number.

    -o [output]      Output filename. Use /dev/null to output nothing.

    -c [rom]         Create an NES rom file that just displays the image.

    -e [error_file]  Output errors to an image file.

    -p [palette]     Palette to use for the input image.

    -b [background_color] | [mask=fill]
                     Background color spec for the palette.

    -s               Sprite mode.

    -l               Lock tiles.

    --lock-sprite-flips
                     Lock vertical and horizontal flip flags for sprites.

    -t [strategy]    Strategy for traversing tiles when making output.

    -r [chr_order]   Order that the CHR data appears in memory.

    -z               Whether to show statistics at the end of processing.

    --allow-overflow [components]
                     Components that allow overflow.

    --makepal        Generate a palette binary file from an image.

    -m [mem_file]    A ppu memory dump, representing the state of ppu ram.

    --palette-view      [image]  Output a view of the palette.

    --colorization-view [image]  Output a view showing the palettes per block.

    --reuse-view        [image]  Output a view showing tile reuse.

    --nametable-view    [image]  Output a view showing the nametable.

    --chr-view          [image]  Output a view showing the entire page of chr.

    --grid-view         [image]  Output the image file with grid.

    --free-zone-view    [image]  Output a view showing free traversal zones.

# Palette literal syntax

    palette  = "P/" + (option + "/"){1-4}
    option   = hexcolor + ("-" hexcolor){1-3}
    hexcolor = [0-9a-f]{2}

Example:

    P/0f-10-01-02/0f-10-30/

This is a palette using 2 options. It has the background color $0f (black).
The first option has 4 colors, the second option has only 3 colors.
