from ..bitfont import bitfont_render, Justify
from ..entities import GameView


EXTRA_BACKGROUNDS = ('blue_trees', 'boat', 'mountains', 'ruins', 'temple')


def insert_eegggv(page_id):
    if page_id % 13 == 0:
        index = page_id // 13 - 1
        if index < len(EXTRA_BACKGROUNDS):
            return GameView(renderer=lambda pdf: _render_eegggv(pdf, index))
    return None


def _render_eegggv(pdf, index):
    pdf.add_page()
    pdf.image(f'assets/backgrounds/{EXTRA_BACKGROUNDS[index]}.png', x=0, y=0)
    bitfont_render(pdf, 'You found an easter egg!', 80, 106, Justify.CENTER)
