'''
An optimizer to reduce the GameViews by identifying the ones that will end up
being rendered exactly the same, including the links.
In practice, this only applies to Game Over death pages, and pages pointing to them.
'''
import os
from contextlib import contextmanager

import fpdf
try:  # Optional dependency:
    from tqdm import tqdm
except ImportError:
    tqdm = lambda _: _

from .assigner import assign_page_ids
from .perfs import print_memory_stats
from .render import render_page


def reduce_views(game_views, multipass=True):
    print('Starting views reducer')
    pdf = fpdf.FPDF()  # a real instance is needed due to the calls to ._parsepng
    pass_number, total_views_removed = 1, 0
    in_game_views = game_views
    while True:
        if multipass:
            print(f'Pass {pass_number} - #views removed so far: {total_views_removed}')
        fake_pdf = FakePdfRecorder(pdf)  # resetting recorder between passes in order to reset links
        gv_per_page_fingerprint, out_game_views = {}, []
        print_memory_stats(detailed=True)
        # We need to assign page IDs in order to detect pages with identical links:
        in_game_views = assign_page_ids(in_game_views, assign_reverse_id=False)
        for game_view in tqdm(in_game_views, disable='NO_TQDM' in os.environ):
            fake_pdf.reset()
            render_page(fake_pdf, game_view, render_victory=lambda *args: None)
            page_fingerprint = fake_pdf.get_fingerprint()
            existing_matching_gv = gv_per_page_fingerprint.get(page_fingerprint)
            if existing_matching_gv:
                # print('- reducer.removes:', f'{gs.coords}/{gs.facing} HP={gs.hp} round={gs.combat and gs.combat.round}')
                game_view.page_id_from(existing_matching_gv)
            else:
                gv_per_page_fingerprint[page_fingerprint] = game_view
                out_game_views.append(game_view)
        views_removed = len(in_game_views) - len(out_game_views)
        total_views_removed += views_removed
        pass_number += 1
        in_game_views = out_game_views
        if not views_removed or not multipass or views_removed < 25:  # Last condition avoid > 20 passes...
            break
    print(f'-{100*(total_views_removed)/len(game_views):0f}% of views were removed by the reducer')
    return out_game_views


class FakePdfRecorder:
    'Fake fpdf.FPDF class that must implement all the methods used during the pages rendering'
    def __init__(self, pdf):
        self.pdf = pdf
        self.images = pdf.images
        self.reset()

    def add_font(self, family, style='', fname='', uni=False):
        pass

    def add_page(self):
        self._calls.append('add_page')

    def set_font(self, family, style='', size=0):
        self._calls.append(('set_font', family, style, size))

    def text(self, x, y, txt=''):
        self._calls.append(('text', x, y, txt))

    def set_text_color(self, r,g=-1,b=-1):
        self._calls.append(('set_text_color', r, g, b))

    def image(self, name, x=None, y=None, w=0, h=0, link=''):
        self._calls.append(('image', name, x, y, w, h, link))

    @contextmanager
    def rect_clip(self, x, y, w, h):
        self._calls.append(('rect_clip', x, y, w, h))
        yield

    @contextmanager
    def rotation(self, angle, x=None, y=None):
        self._calls.append(('rotation', angle, x, y))
        yield

    def add_link(self):
        return len(self._links) + 1

    def set_link(self, link, page=-1):
        self._links[link] = page

    def link(self, x, y, w, h, link, alt_text=''):
        page_or_url = self._links.get(link, link)
        self._calls.append(('link', x, y, w, h, page_or_url, alt_text))

    def _parsepng(self, filename):
        # pylint: disable=protected-access
        return self.pdf._parsepng(filename)

    def reset(self):
        self._calls = []
        self._links = {}

    def get_fingerprint(self):
        return hash(tuple(self._calls))
