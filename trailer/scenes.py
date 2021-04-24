import os
from contextlib import contextmanager

from pdf_game.bitfont import bitfont_render, bitfont_set_color_red, Justify
from pdf_game.combat import combat_logic
from pdf_game.entities import GameMode, GameView, Position
from pdf_game.js import REL_RELEASE_DIR
from pdf_game.mapscript import mapscript_exec
from pdf_game.render import dialog_render, render_book, render_page
from pdf_game.render_treasure import treasure_render_item
from pdf_game.visit import build_initial_state
from pdf_game.mod import Proxy
from pdf_game.mod.books import BOOKS
from pdf_game.mod.campaign import render_staff_puzzle
from pdf_game.mod.scenes import seamus_speaks as _seamus_speaks
from pdf_game.mod.world import MAUSOLEUM_PORTAL_COORDS

from trailer.img_as_pdf import ImageAsPdf

from PIL import Image


PARENT_DIR = os.path.dirname(__file__)


def seamus(fpdf, text, controller=False):
    img, pdf_img = init_pdf_img(fpdf)
    _seamus_speaks(text)(pdf_img)
    if controller:
        pdf_img.image(f'{PARENT_DIR}/PongMan-Xbox360.png', x=54, y=74)
    return [img]

def explore(fpdf, text, frame_copies=5):
    images = []
    kwargs = dict(map_id=10, x=2, tile_overrides=(((10, 2, 4), 5),))
    for y in range(1, 9):
        with _mazemap(fpdf, y=y, **kwargs) as mz: pass
        bitfont_render(mz.pdf_img, text, 80, 70, Justify.CENTER)
        images += [mz.img] * frame_copies
    return images

def chest(fpdf, text, frame_copies=5):
    images = []
    for (x, y, facing) in ((11, 1, 'west'), (10, 1, 'west'), (9, 1, 'west'), (9, 1, 'south'), (9, 2, 'south'), (9, 3, 'south')):
        with _mazemap(fpdf, map_id=10, x=x, y=y, facing=facing) as mz: pass
        bitfont_render(mz.pdf_img, text, 80, 70, Justify.CENTER)
        images += [mz.img] * frame_copies
    for _ in range(2):  # staying a bit longer on last frame:
        images += [mz.img] * frame_copies
    return images

def combat(fpdf, text1, text2, frame_copies=10):  # facing zombie blocking Cedar Village exit
    images = []
    with _mazemap(fpdf, map_id=5, x=9, y=10, hp=42, max_hp=50) as mz:
        combat_logic(mz.gv, mz.gv.actions, GameView)
    gv, img, pdf_img = mz.gv, mz.img, mz.pdf_img
    while True:
        bitfont_set_color_red(False)
        bitfont_render(pdf_img, text1, 158, 50, Justify.RIGHT)
        bitfont_render(pdf_img, text2, 158, 80, Justify.RIGHT)
        images += [img] * frame_copies
        if gv.state.hp <= 0: break
        gv, img, pdf_img = gv.actions['ATTACK'], *init_pdf_img(fpdf)
        combat_logic(gv, gv.actions, GameView)
        render_page(pdf_img, gv, render_victory=None)
    return images

def druidic_linguistics(fpdf, frame_copies=20):
    book = BOOKS[(8, 3, 13)]
    with _mazemap(fpdf, map_id=8, x=3, y=12) as mz:
        pass
    render_book(mz.pdf_img, book, page_id=None, treasure_id=None)
    return [mz.img] * frame_copies

def sage_therel_advice(fpdf, frame_copies=20):
    game_view = GameView(build_initial_state()._replace(mode=GameMode.DIALOG, shop_id=3))
    exit_gv = GameView(build_initial_state())
    exit_gv.set_page_id(1)
    game_view.actions['EXIT'] = exit_gv  # required to exist by dialog_render
    img, pdf_img = init_pdf_img(fpdf)
    dialog_render(pdf_img, game_view)
    return [img] * frame_copies

def staff_puzzle(fpdf, frame_copies=20):
    with _mazemap(fpdf, map_id=8, x=13, y=7, facing='west') as mz:
        pass
    render_staff_puzzle(0)(mz.pdf_img)
    return [mz.img] * frame_copies

def druid(fpdf, frame_copies=10):
    with _mazemap(fpdf, map_id=9, x=3, y=7) as mz:
        return [mz.img] * frame_copies

def goblin(fpdf, text, frame_copies=60):
    with _mazemap(fpdf, map_id=8, x=10, y=11, items=('FISH_ON_A_STICK',)) as mz:
        combat_logic(mz.gv, mz.gv.actions, GameView)
        mz.gv = mz.gv.actions['FISH_ON_A_STICK']
    treasure_render_item(mz.pdf_img, 43, pos=Position(64, 17))  # extra
    bitfont_set_color_red(True)
    bitfont_render(mz.pdf_img, text, 80, 22, Justify.CENTER)
    return [mz.img] * frame_copies

def gorgon(fpdf, frame_copies=10):
    with _mazemap(fpdf, map_id=5, x=9, y=9, tile_overrides=((MAUSOLEUM_PORTAL_COORDS, 27),), # enemy condition
                                            vanquished_enemies=((5, 9, 10),)) as mz:         # zombie beaten
        return [mz.img] * frame_copies

def skeleton(fpdf, frame_copies=10):
    with _mazemap(fpdf, map_id=6, x=12, y=7, facing='east') as mz:
        return [mz.img] * frame_copies

def just_text(fpdf, text):
    img, pdf_img = init_pdf_img(fpdf)
    bitfont_set_color_red(False)
    bitfont_render(pdf_img, text, 80, 22, Justify.CENTER)
    return img

@contextmanager
def _mazemap(fpdf, **kwargs):
    img, pdf_img = init_pdf_img(fpdf)
    game_view = GameView(build_initial_state()._replace(mode=GameMode.EXPLORE, **kwargs))
    mapscript_exec(game_view, GameView)
    mz = Proxy(gv=game_view, img=img, pdf_img=pdf_img)
    yield mz  # mz.gv can be altered here
    render_page(pdf_img, mz.gv, render_victory=None)

def init_pdf_img(fpdf, background='black'):
    img = Image.open(REL_RELEASE_DIR + f'images/backgrounds/{background}.png')
    pdf_img = ImageAsPdf(fpdf, img)
    return img, pdf_img
