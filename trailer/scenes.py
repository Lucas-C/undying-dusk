from contextlib import contextmanager

from pdf_game.bitfont import bitfont_render, bitfont_set_color_red, Justify
from pdf_game.combat import combat_logic
from pdf_game.entities import GameMode, GameView, Position
from pdf_game.js import REL_RELEASE_DIR
from pdf_game.mapscript import mapscript_exec
from pdf_game.render import render_page
from pdf_game.render_treasure import treasure_render_item
from pdf_game.visit import build_initial_state
from pdf_game.mod import Proxy
from pdf_game.mod.scenes import seamus_speaks as _seamus_speaks

from trailer.img_as_pdf import ImageAsPdf

from PIL import Image


def seamus(fpdf, text):
    img, pdf_img = _init_pdf_img(fpdf)
    _seamus_speaks(text)(pdf_img)
    return img

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
        gv, img, pdf_img = gv.actions['ATTACK'], *_init_pdf_img(fpdf)
        combat_logic(gv, gv.actions, GameView)
        render_page(pdf_img, gv, render_victory=None)
    return images

def goblin(fpdf, text, frame_copies=60):
    with _mazemap(fpdf, map_id=8, x=10, y=11, items=('FISH_ON_A_STICK',)) as mz:
        combat_logic(mz.gv, mz.gv.actions, GameView)
        mz.gv = mz.gv.actions['FISH_ON_A_STICK']
    treasure_render_item(mz.pdf_img, 43, pos=Position(64, 17))  # extra
    bitfont_set_color_red(True)
    bitfont_render(mz.pdf_img, text, 80, 22, Justify.CENTER)
    return [mz.img] * frame_copies

def just_text(fpdf, text):
    img, pdf_img = _init_pdf_img(fpdf)
    bitfont_set_color_red(False)
    bitfont_render(pdf_img, text, 80, 22, Justify.CENTER)
    return img

@contextmanager
def _mazemap(fpdf, **kwargs):
    img, pdf_img = _init_pdf_img(fpdf)
    game_view = GameView(build_initial_state()._replace(mode=GameMode.EXPLORE, **kwargs))
    mapscript_exec(game_view, GameView)
    mz = Proxy(gv=game_view, img=img, pdf_img=pdf_img)
    yield mz  # mz.gv can be altered here
    render_page(pdf_img, mz.gv, render_victory=None)

def _init_pdf_img(fpdf):
    img = Image.open(REL_RELEASE_DIR + 'images/backgrounds/black.png')
    pdf_img = ImageAsPdf(fpdf, img)
    return img, pdf_img
