#!/usr/bin/env python3

# INSTALL: pip install livereload
# USAGE: PYTHONPATH=. trailer/gen_promo_images.py $id [--watch-and-rebuild]

import argparse, os, re, webbrowser
from subprocess import check_output

from pdf_game.bitfont import bitfont_render, Justify
from pdf_game.render_info import info_render_equiplayer
from pdf_game.js import config, info
from pdf_game.mod import campaign

from trailer.scenes import (chest, combat, druid, druidic_linguistics, goblin, gorgon, explore,
                            init_pdf_img, just_text, sage_therel_advice, staff_puzzle, skeleton, seamus)

from fpdf import FPDF
from livereload import Server
from PIL import Image


PARENT_DIR = os.path.dirname(__file__)
PORT = 5500
FILENAME_PER_ID = {
    1: "undying-dusk-trailer1.gif",
    2: "undying-dusk-trailer2.gif",
    3: "undying-dusk-cover.png",
}


def main():
    args = parse_args()
    out_filename = FILENAME_PER_ID[args.id]
    sed(f"{PARENT_DIR}/index.html", 'undying-dusk-[^"]+', out_filename)
    campaign.script_it()
    fpdf = FPDF()
    globals()[f"gen_img_{args.id}"](fpdf, out_filename)
    if args.watch_and_rebuild:
        server = Server()
        cmd = ['/usr/bin/env', 'python3', __file__, str(args.id)]
        server.watch(f'{PARENT_DIR}/*.py', lambda: print(check_output(cmd).decode()))
        webbrowser.open(f'http://localhost:{PORT}')
        server.serve(root=PARENT_DIR, port=PORT)

def parse_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("id", type=int)
    parser.add_argument("--watch-and-rebuild", action="store_true", help="Livereload GIF in a web browser")
    return parser.parse_args()

def gen_img_1(fpdf, out_filename):
    tfc = 30  # text frames count
    # Phase 1: STORY EXPOSITION
    images = tfc * seamus(fpdf, 'My respects, my lady.') \
           + tfc * seamus(fpdf, 'Time has frozen\n in an aeternal dusk.') \
           + tfc * seamus(fpdf, 'And people are turning\ninto strange monsters.') \
           + tfc * seamus(fpdf, "It's time to face\nthe Empress curse.") \
           + tfc * seamus(fpdf, 'You are needed.')
    # Phase 2: WHAT TO EXPECT
    images += explore(fpdf, 'A dungeon crawler\nwith 10 maps to explore') \
           + chest(fpdf, 'Many items, weapons\n& spells to collect') \
           + combat(fpdf, 'Many enemies,', 'and always only\none path to victory') \
           + goblin(fpdf, 'Several LucasArts-style\npuzzles') \
           + 40 * [just_text(fpdf, '21 music tracks\n4 hidden secrets\nall spread over\n~150 000 PDF pages')]
    images += trailer_end(fpdf)
    images = scale(4, images)
    images[0].save(f'{PARENT_DIR}/{out_filename}', append_images=images[1:],
                   save_all=True, duration=100, loop=0)

def gen_img_2(fpdf, out_filename):
    # Trying to have a text frames count proportional to text length:
    images = []
    images += 20 * title_screen(fpdf, "Welcome stranger")
    images += 40 * title_screen(fpdf, 'You may be wondering:\n\n"why should I play this game?"')
    images += title_screen(fpdf, 'Reason #1:\n\nRetro aesthetics', sizes=list(range(4, 13)))
    images += 10* [Image.open('assets/backgrounds/cloudy_town.png')]
    images += 10* [Image.open('assets/backgrounds/distant_castle.png')]
    images += 10* [Image.open('assets/backgrounds/hangman.png')]
    images += druid(fpdf)
    images += skeleton(fpdf)
    images += gorgon(fpdf)
    images += title_screen(fpdf, 'Reason #2:\n\nSharp puzzles', sizes=list(range(4, 13)))
    images += sage_therel_advice(fpdf)
    images += druidic_linguistics(fpdf)
    images += staff_puzzle(fpdf)
    images += title_screen(fpdf, 'Reason #3:\n\nEnter the\nhall of fame of the\nfirst video game PDF', sizes=list(range(4, 13)))
    images += 40 * seamus(fpdf, 'There is one thing\nyou really should NOT expect\nthough...')
    images += 30 * seamus(fpdf, 'ergonomics', controller=True)
    images += trailer_end(fpdf)
    images = scale(4, images)
    images[0].save(f'{PARENT_DIR}/{out_filename}', append_images=images[1:],
                   save_all=True, duration=100, loop=0)

def gen_img_3(fpdf, out_filename):
    img, pdf_img = init_pdf_img(fpdf, 'nightsky')
    bitfont_render(pdf_img, 'UNDYING DUSK', 80, 8, Justify.CENTER, size=16)
    info_render_equiplayer(pdf_img, 0, info().TYPE_ARMOR)
    info_render_equiplayer(pdf_img, 1, info().TYPE_ARMOR)
    bitfont_render(pdf_img, 'A free adventure game\nin PDF format!', 80, 90, Justify.CENTER)
    img = scale(4, [img])[0]
    img.save(f'{PARENT_DIR}/{out_filename}')


def scale(factor, images):
    return [img.resize((factor * config().VIEW_WIDTH, factor * config().VIEW_HEIGHT),
                       resample=Image.NEAREST) for img in images]

def title_screen(fpdf, text, sizes=(8,)):
    assert sizes
    if len(sizes) > 1:
        assert text
    images = []
    for size in sizes:
        img, pdf_img = init_pdf_img(fpdf, 'nightsky')
        bitfont_render(pdf_img, 'UNDYING DUSK', 80, 8, Justify.CENTER, size=16)
        if text:
            bitfont_render(pdf_img, text, 80, 70, Justify.CENTER, size=size)
        images.append(img)
    if len(sizes) > 1:
        images.extend([images[-1]] * 20)
    return images

def trailer_end(fpdf):
    images = []
    title_text = 'An adventure game\n& dungeon crawler\nplayable for free!'
    for _ in range(10):  # blinking 100ms/1s:
        images += title_screen(fpdf, title_text)*9 + title_screen(fpdf, text=None)
    return images

def sed(filepath, pattern, value):
    with open(filepath, 'r+') as text_file:
        data = text_file.read()
        text_file.seek(0)
        text_file.write(re.sub(pattern, value, data))
        text_file.truncate()


if __name__ == '__main__':
    main()
