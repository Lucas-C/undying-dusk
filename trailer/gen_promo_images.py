#!/usr/bin/env python3

# INSTALL: pip install livereload
# USAGE: PYTHONPATH=. trailer/gen_promo_images.py [$id] [--watch-and-rebuild]

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
try:
    from PIL.Image import Resampling
    NEAREST = Resampling.NEAREST
except ImportError:  # for older versions of Pillow:
    # pylint: disable=no-member
    NEAREST = Image.NEAREST
from qrcode import QRCode


PARENT_DIR = os.path.dirname(__file__)
PORT = 5500


def main():
    args = parse_args()
    campaign.script_it()
    fpdf = FPDF()
    if args.id:
        name = args.id.split(".")[0]
        globals()[f"gen_{name}"](fpdf)
    else:
        gen_trailer1(fpdf)
        gen_trailer2(fpdf)
        gen_cover(fpdf)
        gen_card(fpdf)
    if args.watch_and_rebuild:
        sed(f"{PARENT_DIR}/index.html", 'undying-dusk-[^"]+', f"undying-dusk-{args.id}")
        server = Server()
        cmd = ['/usr/bin/env', 'python3', __file__, str(args.id)]
        server.watch(f'{PARENT_DIR}/*.py', lambda: print(check_output(cmd).decode()))
        webbrowser.open(f'http://localhost:{PORT}')
        server.serve(root=PARENT_DIR, port=PORT)

def parse_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("id", nargs="?")
    parser.add_argument("--watch-and-rebuild", action="store_true", help="Livereload GIF in a web browser")
    args = parser.parse_args()
    if args.watch_and_rebuild and not args.id:
        parser.error("An image $id is required with --watch-and-rebuild")
    return args

def gen_trailer1(fpdf):
    tfc = 30  # text frames count
    # Phase 1: STORY EXPOSITION
    images = tfc * seamus(fpdf, 'My respects, my lady.') \
           + tfc * seamus(fpdf, 'Time has frozen\n in an aeternal dusk.') \
           + tfc * seamus(fpdf, 'And people are turning\ninto strange monsters.') \
           + tfc * seamus(fpdf, "It's time to face\nthe Empress\'s curse.") \
           + tfc * seamus(fpdf, 'You are needed.')
    # Phase 2: WHAT TO EXPECT
    images += explore(fpdf, 'A dungeon crawler\nwith 10 maps to explore') \
           + chest(fpdf, 'Many items, weapons\n& spells to collect') \
           + combat(fpdf, 'Many enemies,', 'and always only\none path to victory') \
           + goblin(fpdf, 'Several LucasArts-style\npuzzles') \
           + 40 * [just_text(fpdf, '21 music tracks\n4 hidden secrets\nall spread over\n~150 000 PDF pages')]
    images += trailer_end(fpdf)
    images = scale(4, images)
    images[0].save(f'{PARENT_DIR}/undying-dusk-trailer1.gif', append_images=images[1:],
                   save_all=True, duration=100, loop=0)

def gen_trailer2(fpdf):
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
    images[0].save(f'{PARENT_DIR}/undying-dusk-trailer2.gif', append_images=images[1:],
                   save_all=True, duration=100, loop=0)

def gen_cover(fpdf):
    img, pdf_img = init_pdf_img(fpdf, 'nightsky')
    bitfont_render(pdf_img, 'UNDYING DUSK', 80, 8, Justify.CENTER, size=16)
    info_render_equiplayer(pdf_img, 0, info().TYPE_ARMOR)
    info_render_equiplayer(pdf_img, 1, info().TYPE_ARMOR)
    bitfont_render(pdf_img, 'A free adventure game\nin PDF format!', 80, 90, Justify.CENTER)
    img = scale(4, [img])[0]
    img.save(f'{PARENT_DIR}/undying-dusk-cover.png')

def gen_card(fpdf):
    img, pdf_img = init_pdf_img(fpdf, 'nightsky')
    bitfont_render(pdf_img, 'UNDYING DUSK', 80, 8, Justify.CENTER, size=16)
    info_render_equiplayer(pdf_img, 0, info().TYPE_ARMOR)
    info_render_equiplayer(pdf_img, 1, info().TYPE_ARMOR)
    bitfont_render(pdf_img, 'by\nLucas\nCIMON', 2, 45)
    qrcode = QRCode(box_size=1)
    qrcode.add_data("https://lucas-c.itch.io/undying-dusk")
    qr_img = qrcode.make_image(fill_color="#140c1c", back_color="#deeed6").get_image().convert('RGBA')
    pdf_img.image(qr_img, x=120, y=49)
    bitfont_render(pdf_img, 'A free adventure game\nin PDF format!', 80, 94, Justify.CENTER)
    img = scale(4, [img])[0]
    img.save(f'{PARENT_DIR}/undying-dusk-card.png')

def scale(factor, images):
    return [img.resize((factor * config().VIEW_WIDTH, factor * config().VIEW_HEIGHT),
                       resample=NEAREST) for img in images]

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
    with open(filepath, 'r+', encoding='utf8') as text_file:
        data = text_file.read()
        text_file.seek(0)
        text_file.write(re.sub(pattern, value, data))
        text_file.truncate()


if __name__ == '__main__':
    main()
