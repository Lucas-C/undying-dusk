#!/usr/bin/env python3

# USAGE: PYTHONPATH=. trailer/maze_rand_gen.py
# NEXT: add stuff (optionnal enemy / treasure / sfx...) + make it a cron + use it on a promo page

import os
from random import randrange

from pdf_game.js import REL_RELEASE_DIR
from pdf_game.render import TILES, _DRAW_AREAS

from trailer.img_as_pdf import ImageAsPdf

from fpdf import FPDF
from PIL import Image


PARENT_DIR = os.path.dirname(__file__)


def main():
    img = Image.open(REL_RELEASE_DIR + 'images/backgrounds/black.png')
    pdf = ImageAsPdf(FPDF(), img)
    for render_pos in range(13):
        tile_id = randrange(1, len(TILES))
        # Replicating mazemap_render_tile:
        tile = TILES[tile_id]
        img_filepath = (REL_RELEASE_DIR + f'images/tiles/{tile}.png') if tile_id < 20 else f'assets/tiles/{tile}.png'
        if tile_id == 16: img_filepath = 'assets/tiles/skull_pile2.png'
        draw_area = _DRAW_AREAS[render_pos]
        with pdf.rect_clip(x=draw_area.dest_x, y=draw_area.dest_y, w=draw_area.width, h=draw_area.height):
            pdf.image(img_filepath, x=draw_area.dest_x-draw_area.src_x, y=draw_area.dest_y-draw_area.src_y)
    img.save(f'{PARENT_DIR}/rand_maze.png')


if __name__ == '__main__':
    main()
