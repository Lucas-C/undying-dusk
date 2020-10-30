#!/usr/bin/env python3

# INSTALL: pip install livereload
# USAGE: PYTHONPATH=. trailer/build_gif_trailer.py --watch-and-rebuild

import os, sys, webbrowser
from subprocess import check_output, STDOUT

from pdf_game.bitfont import bitfont_render, Justify
from pdf_game.js import config, REL_RELEASE_DIR
from pdf_game.mod import campaign

from trailer.img_as_pdf import ImageAsPdf
from trailer.scenes import chest, combat, goblin, explore, just_text, seamus

from fpdf import FPDF
from livereload import Server
from PIL import Image


PARENT_DIR = os.path.dirname(__file__)
PORT = 5500


def main():
    campaign.script_it()
    fpdf = FPDF()
    gen_gif(fpdf)
    if '--watch-and-rebuild' in sys.argv:
        server = Server()
        server.watch(f'{PARENT_DIR}/*.py', lambda: print(check_output(['python3', __file__])))
        webbrowser.open(f'http://localhost:{PORT}')
        server.serve(root=PARENT_DIR, port=PORT)

def gen_gif(fpdf):
    tfc = 30  # text frames count
    # Phase 1: STORY EXPOSITION
    images = tfc * [seamus(fpdf, 'My respects, my lady.')] \
           + tfc * [seamus(fpdf, 'Time has frozen\n in an aeternal dusk.')] \
           + tfc * [seamus(fpdf, 'And people are turning\ninto strange monsters.')] \
           + tfc * [seamus(fpdf, "It's time to face\nthe Empress curse.")] \
           + tfc * [seamus(fpdf, 'You are needed.')]
    # Phase 2: WHAT TO EXPECT
    images += explore(fpdf, 'A dungeon crawler\nwith 10 maps to explore') \
           + chest(fpdf, 'Many items, weapons\n& spells to collect') \
           + combat(fpdf, 'Many enemies,', 'and always only\none path to victory') \
           + goblin(fpdf, 'Several LucasArts-style\npuzzles') \
           + 40 * [just_text(fpdf, '21 music tracks\n4 hidden secrets\nall spread over\n~150 000 PDF pages')]
    for _ in range(10):
        # blinking 100ms/1s:
        images += [title_img(fpdf)]*9 + [title_img(fpdf, playable=False)]
    images = scale(4, images)
    images[0].save(f'{PARENT_DIR}/undying-dusk-trailer.gif', append_images=images[1:],
                   save_all=True, duration=100, loop=0)

def scale(factor, images):
    return [img.resize((factor * config().VIEW_WIDTH, factor * config().VIEW_HEIGHT),
                       resample=Image.NEAREST) for img in images]

def title_img(fpdf, playable=True):
    img = Image.open(REL_RELEASE_DIR + 'images/backgrounds/nightsky.png')
    pdf_img = ImageAsPdf(fpdf, img)
    bitfont_render(pdf_img, 'UNDYING DUSK', 80, 8, Justify.CENTER, size=16)
    if playable:
        bitfont_render(pdf_img, 'An adventure game\n& dungeon crawler\nnow playable for free!', 80, 70, Justify.CENTER)
    return img


if __name__ == '__main__':
    main()
