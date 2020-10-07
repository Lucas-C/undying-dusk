from .bitfont import bitfont_render
from .entities import Position
from .js import treasure, REL_RELEASE_DIR
from .render_utils import action_button_render, get_image_info


COLLECTIBLE_IMG_POS = Position(x=130, y=74)
COLLECTIBLE_TXT_POS_X = 147
COLLECTIBLE_TXT_POS_Y = 83


def treasure_render_gold(pdf, total_value):
    # arranged in treasure pile draw order
    if total_value & 128: _treasure_render_gold_icon(pdf, 7)
    if total_value & 512: _treasure_render_gold_icon(pdf, 9)
    if total_value & 32: _treasure_render_gold_icon(pdf, 5)
    if total_value & 16: _treasure_render_gold_icon(pdf, 4)
    if total_value & 8: _treasure_render_gold_icon(pdf, 3)
    if total_value & 1: _treasure_render_gold_icon(pdf, 0)
    if total_value & 4: _treasure_render_gold_icon(pdf, 2)
    if total_value & 64: _treasure_render_gold_icon(pdf, 6)
    if total_value & 2: _treasure_render_gold_icon(pdf, 1)
    if total_value & 256: _treasure_render_gold_icon(pdf, 8)


def _treasure_render_gold_icon(pdf, item_id):
    x, y = treasure().gold_pos[item_id].dest_x, treasure().gold_pos[item_id].dest_y
    _treasure_render(pdf, item_id, x, y)


def treasure_render_item(pdf, treasure_id, pos=None):
    x, y = (pos.x, pos.y) if pos else (treasure().TREASURE_POS_X, treasure().TREASURE_POS_Y)
    _treasure_render(pdf, treasure_id, x, y)


def treasure_render_collectible(pdf, btn_type, count):
    action_button_render(pdf, btn_type, btn_pos=COLLECTIBLE_IMG_POS)
    bitfont_render(pdf, f'x{count}', COLLECTIBLE_TXT_POS_X, COLLECTIBLE_TXT_POS_Y)


def _treasure_render(pdf, treasure_id, x, y, scale=1):
    icon_size = treasure().TREASURE_ICON_SIZE
    if treasure_id < 16:  # Original treasure:
        treasure_img = REL_RELEASE_DIR + treasure().img.src
    else:  # Newly introduced item:
        treasure_id -= 16
        treasure_img = 'assets/extra_treasure.png'
    width, height = 0, 0
    if scale != 1:
        img_info = get_image_info(pdf, treasure_img)
        width, height = img_info['w'] * scale, img_info['h'] * scale
    with pdf.rect_clip(x=x, y=y, w=icon_size * scale, h=icon_size * scale):
        pdf.image(treasure_img, x=x - treasure_id * icon_size * scale, y=y, w=width, h=height)
