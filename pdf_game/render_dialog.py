from .bitfont import bitfont_render, Justify
from .entities import DialogButtonType, Position
from .js import dialog, shop, REL_RELEASE_DIR
from .render_info import info_render_gold
from .render_utils import action_button_render, add_link, render_button, sfx_render, tileset_background_render, white_arrow_render
from .render_treasure import treasure_render_item

from .shop_dialog import build_dialog_options, resolve_redirect

BUTTON_IMG = REL_RELEASE_DIR + "images/interface/dialog_buttons.png"
BUTTON_POS = [  # Slightly shift up the original positions
    Position(x=0, y=50),
    Position(x=0, y=75),
    Position(x=0, y=100),
]


def dialog_render(pdf, game_view):
    shop_id = game_view.state.shop_id
    assert shop_id >= 0
    _shop = shop()[shop_id]
    _shop = resolve_redirect(_shop, game_view.state)
    tileset_background_render(pdf, _shop.background)
    bitfont_render(pdf, _shop.name, 80, 5, Justify.CENTER)
    try:
        justify = _shop.justify
    except (AttributeError, KeyError):
        justify = Justify.LEFT

    # only render gold if there is something for sale
    if items_for_sale(_shop):
        info_render_gold(pdf, game_view.state)

    for i, option in enumerate(build_dialog_options(game_view.state)):
        pos = BUTTON_POS[i]
        action_name = option.btn_type.action_name(i)
        if not action_name:
            continue
        page_id = None
        if option.can_buy:
            assert action_name in game_view.actions, f'DialogScene with id={shop_id} name="{_shop.name}" has an action {action_name} but the corresponding GameView does not'
            page_id = game_view.actions[action_name].page_id
        if option.btn_type == DialogButtonType.NEXT:
            white_arrow_render(pdf, 'NEXT', 142, 104, page_id=page_id)
        elif option.btn_type in (DialogButtonType.DRINK_RED, DialogButtonType.DRINK_GREEN):
            x = 37 if option.btn_type == DialogButtonType.DRINK_RED else 110
            y = 76
            color = 'red' if option.btn_type == DialogButtonType.DRINK_RED else 'green'
            pdf.image(f'assets/phial-{color}.png', x=x, y=y)
            add_link(pdf, x, y, width=13, height=28, page_id=page_id, link_alt=option.btn_type.name.replace('_', ' '))
        elif option.btn_type == DialogButtonType.TAKE_CRUCIFIX:
            x, y = 74, 38
            add_link(pdf, x, y, width=21, height=30, page_id=page_id, link_alt=option.btn_type.name.replace('_', ' '))
        elif option.btn_type == DialogButtonType.TALK_WITH_MONK:
            x, y = 0, 59
            add_link(pdf, x, y, width=37, height=61, page_id=page_id, link_alt=option.btn_type.name.replace('_', ' '))
            if not game_view.state.message:  # avoid message overlap
                dialog_render_text(pdf, pos, option, justify, page_id=page_id)
        else:
            button_id = getattr(dialog(), f'DIALOG_BUTTON_{option.btn_type.name}')
            assert button_id is not None, f'DIALOG_BUTTON_{option.btn_type.name}'
            if option.btn_type == DialogButtonType.EXIT:
                assert page_id is not None, f'EXIT button pointing to GV without page ID: {game_view.state} -> {game_view.actions[action_name]}'
                if i < 2:
                    # The EXIT option must always be rendered at a fixed "y" pos, at the bottom:
                    pos = BUTTON_POS[2]
            render_button(pdf, pos, BUTTON_IMG, button_id - 1, page_id=page_id, link_alt=option.btn_type.name.replace('_', ' '))
            dialog_render_text(pdf, pos, option, justify, page_id=page_id)

    if game_view.state.message:
        bitfont_render(pdf, game_view.state.message, 80, 30, Justify.CENTER)

    try:
        treasure_id = _shop.treasure_id
    except (AttributeError, KeyError):
        treasure_id = game_view.state.treasure_id
    if treasure_id:
        assert isinstance(treasure_id, int)
        treasure_render_item(pdf, treasure_id, Position(x=64, y=80))

    try:
        if _shop.sfx:
            sfx_render(pdf, _shop.sfx)
    except (AttributeError, KeyError):
        pass

    try:
        if _shop.music:
            action_button_render(pdf, 'MUSIC', url=_shop.music, btn_pos=Position(2, 30))
    except (AttributeError, KeyError):
        pass
    try:
        _shop.extra_render(pdf)
    except (AttributeError, KeyError, TypeError):  # 'NoneType' object is not callable:
        pass

    try:
        game_view.state.extra_render(pdf)
    except (AttributeError, KeyError, TypeError):  # 'NoneType' object is not callable:
        pass


def items_for_sale(_shop):
    try:
        return any(item.type != shop().SHOP_MESSAGE for item in _shop.item)
    except AttributeError:  # 'CutScene' object has no attribute 'item'
        return False


def dialog_render_text(pdf, pos, option, justify, page_id):
    x = pos.x + 22
    if justify == Justify.CENTER:
        x = 80
    y = pos.y + 10 - option.msg.count('\n') * 8
    for i, line in enumerate(option.msg.split('\n')):
        bitfont_render(pdf, line, x, y + 10*i, justify,
                       page_id=page_id if option.btn_type != DialogButtonType.NONE else None)
