#!/usr/bin/env python3

import sys

from PIL import Image

from pdf_game.render_minimap import parse_gpl_file


def main(img_filepaths):
    palette = set(parse_gpl_file('DawnBringer.gpl').colors.values())
    for img_filepath in img_filepaths:
        img = Image.open(img_filepath)
        if img.mode != 'P':
            assert img.mode in ('RGB', 'RGBA'), img.mode
            colors = set()
            for pixel in img.getdata():
                colors.add(pixel[:3])
            if not colors.issubset(palette):
                print(f'{img_filepath}: {img.mode} #colors={len(colors)}')


if __name__ == '__main__':
    main(sys.argv[1:])
