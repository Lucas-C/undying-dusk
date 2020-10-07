from .bitfont import bitfont_render, Justify
from .js import action, info, REL_RELEASE_DIR
from .render_utils import render_button


def info_render_button(pdf, page_id=None, down=False, btn_pos=None):
    if not btn_pos:
        btn_pos = action().BUTTON_POS_INFO
    render_button(pdf, btn_pos, REL_RELEASE_DIR + info().button_img.src, 1 if down else 0,
                  page_id=page_id, link_alt="INFO")


def info_render(pdf, game_state):
    bitfont_render(pdf, "INFO", 80, 2, Justify.CENTER)
    if game_state.spellbook > 0:
        bitfont_render(pdf, "Spells", 100, 33, Justify.LEFT)
    info_render_equipment(pdf, game_state)
    info_render_hpmp(pdf, game_state)
    info_render_gold(pdf, game_state)
    if game_state.items:
        bitfont_render(pdf, "Items", 100, 83, Justify.LEFT)
    # Note: items & spells are rendered by render.action_render


def info_render_hpmp(pdf, game_state):
    bitfont_render(pdf, f"HP {max(0, game_state.hp)}/{game_state.max_hp}", 2, 100)
    bitfont_render(pdf, f"MP {game_state.mp}/{game_state.max_mp}", 2, 110)


def info_render_gold(pdf, game_state, page_id=None):
    bitfont_render(pdf, f"{game_state.gold} Gold", 158, 110, Justify.RIGHT, page_id=page_id)


def info_render_equipment(pdf, game_state):
    # always draw the base:
    info_render_equiplayer(pdf, 0, info().TYPE_ARMOR)
    # render worn equipment:
    info_render_equiplayer(pdf, game_state.armor, info().TYPE_ARMOR)
    info_render_equiplayer(pdf, game_state.weapon, info().TYPE_WEAPON)
    return   # Removed to make the info screen less dense & cuz' it is not so useful
    # ARMOR:
    item_string = info().armors[game_state.armor].name
    if game_state.bonus_def > 0:
        item_string += f" +{game_state.bonus_def}"
    bitfont_render(pdf, item_string, 2, 65)
    # WEAPON:
    item_string = info().weapons[game_state.weapon].name
    if game_state.bonus_atk > 0:
        item_string += f" +{game_state.bonus_atk}"
    bitfont_render(pdf, item_string, 2, 75)


def info_render_equiplayer(pdf, itemtier, itemtype):
    x, y = info().AVATAR_DRAW_X, info().AVATAR_DRAW_Y
    w, h = info().AVATAR_SPRITE_W, info().AVATAR_SPRITE_H
    with pdf.rect_clip(x=x, y=y, w=w, h=h):
        pdf.image(REL_RELEASE_DIR + info().avatar_img.src,
                  x=x - itemtier * info().AVATAR_SPRITE_W,
                  y=y - itemtype * info().AVATAR_SPRITE_H)
