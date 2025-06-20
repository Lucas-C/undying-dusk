# pylint: disable=unused-import
import importlib
from .entities import Position
from .js import action, REL_RELEASE_DIR

from fpdf.image_parsing import preload_image
try:
    from fpdf.image_parsing import is_iccp_valid
    # Hack to disable ICC profile embedding for all images:
    importlib.import_module('fpdf.image_parsing').is_iccp_valid = lambda iccp, filename: False
except ImportError:
    pass  # Older version of fpdf2: skipping


BACKGROUNDS = 'black,nightsky,tempest,interior'.split(',')
ACTION_BUTTONS = 'ATTACK,RUN,HEAL,BURN,UNLOCK,LIGHT,FREEZE,REFLECT,HOLY_WATER,SCROLL,BOOTS,PRAY,FISH,BLUE_KEY,MUSIC,BUCKLER,PUSH,EXAMINE,PLATINO,NO_PUSH,EMPTY_BOTTLE,AMULET,CRUCIFIX,TALK,ARMOR,GLIMPSE,FISH_ON_A_STICK,COMBINE_WITH_TWIG,SMOKED_FISH_ON_A_STICK,ATK_BOOST,PUT_STICK_IN_LEVER,STAFF,HAND_MIRROR,SCEPTER,BEHIND_IVY,FULL_BOTTLE'.split(',')  # order matches position in .png
INFO_SCREEN_ITEM_SLOT_POS = (
    Position(x=100, y=88),
    Position(x=120, y=88),
    Position(x=140, y=88),
    # Position(x=140, y=102), # bottom-right corner => it's getting messy, no need for now
)
ACTION_BUTTON_POS = {
    # Unaltered:
    'INFO':    Position(x=140, y=0),
    'ATTACK':  Position(x=120, y=20),
    'RUN':     Position(x=140, y=20),
    # Re-arrange spells to give space to items when rendering INFO:
    'HEAL':    Position(x=100, y=40),
    'BURN':    Position(x=120, y=40),
    'UNLOCK':  Position(x=140, y=40),
    'LIGHT':   Position(x=100, y=60),
    'FREEZE':  Position(x=120, y=60),
    'REFLECT': Position(x=140, y=60),
    # Extra actions
    'TALK':    Position(x=76, y=30),  # aligned with dungeon_wall_small_window sprite
    'PUSH':    Position(x=72, y=60),  # aligned with box sprite
    'NO_PUSH': Position(x=72, y=60),  # aligned with box sprite
    'EXAMINE': Position(x=66, y=72),  # aligned with bookshelf & well sprites
    'GLIMPSE': Position(x=76, y=79),  # aligned with Canal Boneyard water
    'BEHIND_IVY': Position(x=66, y=20),  # aligned with ivy next to cauldron over fire
    'BUCKLER': Position(x=140, y=20),
    'SCEPTER': Position(x=107, y=101),
    # Explore mode contextual actions:
    'AMULET':             Position(x=140, y=88),
    'BLUE_KEY':           Position(x=140, y=88),
    'CRUCIFIX':           Position(x=140, y=88),
    'HAND_MIRROR':        Position(x=140, y=88),
    'EMPTY_BOTTLE':       Position(x=120, y=88),  # can be carried with CRUCIFIX and used at the same place!
    'FULL_BOTTLE':        Position(x=120, y=88),  # can be carried with CRUCIFIX and used at the same place!
    'FISH':               Position(x=140, y=88),
    'FISH_ON_A_STICK':    Position(x=140, y=88),
    'PUT_STICK_IN_LEVER': Position(x=136, y=97),
    'PRAY':               Position(x=100, y=88),
    'STAFF':              Position(x=140, y=88),
    # Bribe items:
    # FISH                -> already present as a contextual action
    # FISH_ON_A_STICK     -> already present as a contextual action
    'SMOKED_FISH_ON_A_STICK': Position(x=140, y=88),
    # Combat items:
    # 'CRUCIFIX'     -> already present as a contextual action
    # 'EMPTY_BOTTLE' -> already present as a contextual action
    # 'FULL_BOTTLE'  -> already present as a contextual action
    'HOLY_WATER':   INFO_SCREEN_ITEM_SLOT_POS[0],
    # Extra display:
    'ATK_BOOST': Position(x=-4, y=82),
}
WHITE_ARROW_NAMES = 'BACK,NEXT'.split(',')  # order matches position in .png
WHITE_ARROW_SIZE = 16


def portrait_render(pdf, portrait_id, x=0, y=0):
    with pdf.rect_clip(x=x, y=y, w=32, h=32):
        pdf.image('assets/portraits.png', x=x - portrait_id * 32, y=y)


def sfx_render(pdf, sfx):
    with pdf.rect_clip(x=sfx.pos.x, y=sfx.pos.y, w=32, h=32):
        pdf.image('assets/sfx.png', x=sfx.pos.x - sfx.id * 32, y=sfx.pos.y)


def tileset_background_render(pdf, bg_id):
    img_filepath = f'assets/backgrounds/{bg_id}.png' if isinstance(bg_id, str) else REL_RELEASE_DIR + f'images/backgrounds/{BACKGROUNDS[bg_id]}.png'
    pdf.image(img_filepath, x=0, y=0)


def action_button_render(pdf, btn_type, page_id=None, url='', btn_pos=None, item_index=None):
    if not btn_pos:
        btn_pos = ACTION_BUTTON_POS[btn_type] if item_index is None else INFO_SCREEN_ITEM_SLOT_POS[item_index]
    img_index = ACTION_BUTTONS.index(btn_type)
    if img_index < 8:  # Original button:
        img_filepath = REL_RELEASE_DIR + action().button_img.src
    else:  # Newly introduced action:
        img_index -= 8
        img_filepath = 'assets/extra_action_buttons.png'
    render_button(pdf, btn_pos, img_filepath, img_index, page_id=page_id, url=url, link_alt=btn_type.replace('_', ' '))


def white_arrow_render(pdf, name, x, y, page_id=None):
    img_index = WHITE_ARROW_NAMES.index(name)
    link = link_from_page_id(pdf, page_id) if page_id else None
    with pdf.rect_clip(x=x, y=y, w=WHITE_ARROW_SIZE, h=WHITE_ARROW_SIZE):
        pdf.image('assets/white_arrows.png', x=x - img_index*WHITE_ARROW_SIZE, y=y, link=link, alt_text=name)


def render_button(pdf, btn_pos, img_filepath, img_index=0, page_id=None, url='', link_alt=None):
    btn_size, btn_offset = action().BUTTON_SIZE, action().BUTTON_OFFSET
    x = btn_pos.x + btn_offset
    y = btn_pos.y + btn_offset
    with pdf.rect_clip(x=x, y=y, w=btn_size, h=btn_size):
        pdf.image(img_filepath, x=x - img_index*btn_size, y=y)  # DEBUG NOTE: passing link= here creates a bug with RUN button
    if page_id or url:
        return add_link(pdf, x, y, btn_size, btn_size, page_id=page_id, url=url, link_alt=link_alt)
    return None


def add_link(pdf, x, y, width, height, rotation=None, page_id=None, url='', link=None, link_alt=None):
    if page_id is not None:
        assert not (link or url)
        link = link_from_page_id(pdf, page_id)
    if url: assert isinstance(url, str)
    if link: assert isinstance(link, int)
    if rotation:
        with pdf.rotation(rotation, x=x+width/2, y=y+height/2):
            pdf.link(x, y, width, height, link or url, link_alt)
    else:
        pdf.link(x, y, width, height, link or url, link_alt)
    return link


def link_from_page_id(pdf, page_id):
    assert page_id and isinstance(page_id, int), page_id
    link = pdf.add_link()
    pdf.set_link(link, page=page_id)
    return link


def get_image_info(pdf, img_filepath):
    _, _, info = preload_image(pdf.image_cache, img_filepath)
    return info
