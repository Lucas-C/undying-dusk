from base64 import urlsafe_b64encode

from .. import __version__
from ..bitfont import bitfont_set_color_red, bitfont_color_red, bitfont_render, Justify
from ..entities import Position
from ..js import REL_RELEASE_DIR
from ..render import arrow_button_render, ARROW_BUTTONS_POS
from ..render_info import info_render_button
from ..render_utils import action_button_render, white_arrow_render


def render_intro_pages(pdf, start_page_id):
    bitfont_set_color_red(False)
    link_to_credits = _render_title(pdf, start_page_id)
    _render_how_to_play(pdf, start_page_id)
    return link_to_credits


def render_victory(pdf, game_state, links_to_credits):
    pdf.image(REL_RELEASE_DIR + 'images/backgrounds/nightsky.png', x=0, y=0)
    for x, y in (
        (80, 40), (95, 35), (50, 20), (30, 32), (17, 65), (40, 70), (65, 67), (70, 84),
        (90, 75), (122, 65), (22, 90), (115, 100), (10, 10), (132, 15), (50, 38), (84, 63),
        (138, 39), (72, 29), (109, 66), (100, 0), (50, 65)
    ):
        pdf.image('assets/yellow-star.png', x=x, y=y)
    bitfont_render(pdf, 'VICTORY !', 80, 48, Justify.CENTER, size=24)
    bitfont_render(pdf, f'Secrets found: {len(game_state.secrets_found)}/4', 80, 80, Justify.CENTER)
    query_param = urlsafe_b64encode(','.join(game_state.secrets_found).encode()).decode()
    url = f'https://chezsoi.org/lucas/undying-dusk/hall-of-fame?v={__version__}&gs={query_param}'
    with bitfont_color_red():
        bitfont_render(pdf, 'Online hall of fame', 80, 90, Justify.CENTER, url=url)
    bitfont_render(pdf, 'Credits', 80, 100, Justify.CENTER, link=links_to_credits)
    if len(game_state.secrets_found) >= 4:
        # as requested in "DAWNLIKE 16x16 Universal Rogue-like tileset v1.81" README.txt ;)
        action_button_render(pdf, 'PLATINO', btn_pos=Position(x=140, y=100))


def render_credit_pages(pdf, links_to_credits):
    bitfont_set_color_red(False)

    pdf.add_page()
    pdf.set_link(links_to_credits, page=pdf.page)
    pdf.image(REL_RELEASE_DIR + 'images/backgrounds/black.png', x=0, y=0)

    white_arrow_render(pdf, 'BACK', 140, 3, page_id=1)

    bitfont_render(pdf, 'THANK YOU FOR PLAYING !', 80, 25, Justify.CENTER)
    bitfont_render(pdf, 'I hope you liked this game ;)', 80, 45, Justify.CENTER)
    bitfont_render(pdf, 'It is free &                       .', 80, 55, Justify.CENTER)
    with bitfont_color_red():
        bitfont_render(pdf, 'open-source', 75, 55, url='https://github.com/Lucas-C/undying-dusk')
    bitfont_render(pdf, 'You can support my work', 80, 65, Justify.CENTER)
    bitfont_render(pdf, 'through a tip on             .', 80, 75, Justify.CENTER)
    with bitfont_color_red():
        bitfont_render(pdf, 'itch.io', 105, 75, url='https://lucas-c.itch.io/undying-dusk')
    bitfont_render(pdf, 'You can also leave a comment', 80, 85, Justify.CENTER)
    bitfont_render(pdf, 'on the                                     .', 80, 95, Justify.CENTER)
    with bitfont_color_red():
        bitfont_render(pdf, 'dedicated subreddit', 43, 95, url='https://www.reddit.com/r/UndyingDuskPdfGame/')
    bitfont_render(pdf, '-Lucas', 80, 105, Justify.CENTER)
    white_arrow_render(pdf, 'NEXT', 140, 105, page_id=pdf.page+1)

    pdf.add_page()
    pdf.image(REL_RELEASE_DIR + 'images/backgrounds/black.png', x=0, y=0)
    y = 5
    bitfont_render(pdf, 'CREDITS', 80, y, Justify.CENTER)
    white_arrow_render(pdf, 'BACK', 140, 3, page_id=pdf.page - 1)

    y+=15; bitfont_render(pdf, 'Game made by', 80, y, Justify.CENTER)
    with bitfont_color_red():
        y+=10; bitfont_render(pdf, 'Lucas Cimon (2020)', 80, y, Justify.CENTER, url='https://chezsoi.org')
        y+=10; bitfont_render(pdf, '& Phoenyx(2024)', 80, y, Justify.CENTER, url='https://www.reddit.com/user/Phoenyx65535/')

    y+=15; bitfont_render(pdf, 'Original game', 80, y, Justify.CENTER)
    with bitfont_color_red():
        y+=10; bitfont_render(pdf, 'Heroine Dusk', 80, y, Justify.CENTER, url='http://heroinedusk.com')
        y+=10; bitfont_render(pdf, 'by Clint Bellinger (2013)', 80, y, Justify.CENTER, url='http://clintbellanger.net')

    y+=15; bitfont_render(pdf, 'This game exists thanks', 80, y, Justify.CENTER)
    y+=10; bitfont_render(pdf, 'to many generous people:', 80, y, Justify.CENTER)
    with bitfont_color_red():
        y+=10; bitfont_render(pdf, '>full credits<', 80, y, Justify.CENTER, url='https://github.com/Lucas-C/undying-dusk#credits--attribution')

    bitfont_render(pdf, f'v{__version__}', 159, 115, Justify.RIGHT, size=4)


def _render_title(pdf, start_page_id):
    pdf.add_page()
    pdf.image(REL_RELEASE_DIR + 'images/backgrounds/nightsky.png', x=0, y=0)
    bitfont_render(pdf, 'UNDYING DUSK', 80, 8, Justify.CENTER, size=14)
    bitfont_render(pdf, 'HOW TO PLAY', 80, 64, Justify.CENTER, page_id=2)
    bitfont_render(pdf, 'START', 80, 76, Justify.CENTER, page_id=start_page_id)
    return bitfont_render(pdf, 'CREDITS', 80, 88, Justify.CENTER, page_id=1)  # creating a dummy link to credits for now


def _render_how_to_play(pdf, start_page_id):
    pdf.add_page()
    pdf.image(REL_RELEASE_DIR + 'images/backgrounds/black.png', x=0, y=0)
    bitfont_render(pdf, 'This is an interactive game.\nYou play it by clicking on', 80, 20, Justify.CENTER)
    with bitfont_color_red():
        bitfont_render(pdf, 'text links', 80, 50, Justify.CENTER, page_id=3)
    bitfont_render(pdf, 'and image links\nlike the arrow below', 80, 70, Justify.CENTER)
    white_arrow_render(pdf, 'NEXT', 142, 104, page_id=3)

    pdf.add_page()
    pdf.image(REL_RELEASE_DIR + 'images/backgrounds/black.png', x=0, y=0)
    bitfont_render(pdf, 'Please do not use\nAdobe Acrobat Reader\nto play this game, as it\nrenders pages too slowly.\n\nuse instead', 80, 10, Justify.CENTER)
    with bitfont_color_red():
        bitfont_render(pdf, 'another PDF reader', 80, 70, Justify.CENTER, url='https://github.com/Lucas-C/undying-dusk#compatible-pdf-readers')
    bitfont_render(pdf, 'and zoom in it in order for', 80, 80, Justify.CENTER)
    bitfont_render(pdf, 'each page to take', 80, 90, Justify.CENTER)
    bitfont_render(pdf, 'the full height', 80, 100, Justify.CENTER)
    white_arrow_render(pdf, 'NEXT', 142, 104, page_id=4)

    pdf.add_page()
    pdf.image(REL_RELEASE_DIR + 'images/backgrounds/black.png', x=0, y=0)
    bitfont_render(pdf, 'Interface buttons to\nnavigate between pages:', 80, 9, Justify.CENTER)
    for direction in ARROW_BUTTONS_POS:
        arrow_button_render(pdf, direction, shift_x=-85, shift_y=38)
    bitfont_render(pdf, 'LEFT/RIGHT :\nturn around', 45, 33)
    bitfont_render(pdf, 'UP/DOWN : move\nforward/backward', 45, 57)
    start_y = 77
    action_button_render(pdf, 'ATTACK', btn_pos=Position(25, start_y))
    bitfont_render(pdf, 'ATTACK', 45, start_y + 6)
    info_render_button(pdf, btn_pos=Position(85, start_y))
    bitfont_render(pdf, 'INFO', 105, start_y + 6)
    bitfont_render(pdf, 'Do NOT use your\nkeyboard arrow keys', 80, 98, Justify.CENTER)
    white_arrow_render(pdf, 'NEXT', 142, 104, page_id=5)

    pdf.add_page()
    pdf.image(REL_RELEASE_DIR + 'images/backgrounds/black.png', x=0, y=0)
    bitfont_render(pdf, 'This icon:', 80, 5, Justify.CENTER)
    action_button_render(pdf, 'MUSIC', btn_pos=Position(72, 12))
    bitfont_render(pdf, 'indicates a music track.', 80, 32, Justify.CENTER)
    bitfont_render(pdf, 'Click on it when you see it!', 80, 50, Justify.CENTER)
    bitfont_render(pdf, 'A song will start in your', 80, 68, Justify.CENTER)
    bitfont_render(pdf, ' web browser. Listen to the', 80, 78, Justify.CENTER)
    bitfont_render(pdf, 'music in the background,', 80, 88, Justify.CENTER)
    bitfont_render(pdf, 'and keep playing!', 80, 98, Justify.CENTER)
    white_arrow_render(pdf, 'NEXT', 142, 104, page_id=6)

    pdf.add_page()
    pdf.image(REL_RELEASE_DIR + 'images/backgrounds/black.png', x=0, y=0)
    bitfont_render(pdf, "Your heroine has 2 stats:", 8, 5)
    bitfont_render(pdf, "HP 15/25", 2, 18)
    bitfont_render(pdf, "-> means you have\n    fifteen health\n    points over 25 max", 45, 18)
    bitfont_render(pdf, "MP 0/1", 2, 53)
    bitfont_render(pdf, "-> means you have\n    zero magic point\n    over 1 max", 45, 53)
    bitfont_render(pdf, "During your adventure, \nyou'll also find weapons,\narmor, items & spells.", 8, 87)
    white_arrow_render(pdf, 'NEXT', 142, 104, page_id=7)

    pdf.add_page()
    pdf.image(REL_RELEASE_DIR + 'images/backgrounds/black.png', x=0, y=0)
    bitfont_render(pdf, 'To save or load your game,\nsimply note the page number', 80, 12, Justify.CENTER)
    with bitfont_color_red():
        bitfont_render(pdf, 'NOW ENTER\nTHE DUNGEON', 80, 37, Justify.CENTER, page_id=start_page_id)
    link = pdf.add_link()
    pdf.set_link(link, page=start_page_id)
    pdf.image('assets/dungeon-door-opening.png', 48, 56, link=link, alt_text='OPEN THE DOOR')


SECRET_ENDING_ID = 1059
def render_secret_ending(pdf):
    bitfont_set_color_red(False)
    pdf.add_page()
    pdf.image('assets/backgrounds/dominik.png', x=0, y=0)
    bitfont_render(pdf, 'I will love you to death', 80, 90, Justify.CENTER)
