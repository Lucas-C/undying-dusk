'''
An optimizer to reduce the GameViews by identifying the ones that will end up
being rendered exactly the same, including the links.
In practice, this only applies to Game Over death pages, and pages pointing to them.
'''
import os
from contextlib import contextmanager
from textwrap import indent

from fpdf.image_datastructures import ImageCache

from .assigner import assign_page_ids
from .entities import GameMilestone
from .optional_deps import tqdm
from .perfs import disable_tracing, print_memory_stats
from .render import render_page


def reduce_views(game_views, print_reduced_views=False):
    print('Starting views reducer: 1st, assigning page IDs')
    fake_pdf = FakePdfRecorder()
    pass_number, total_views_removed = 1, 0
    # We need to assign page IDs in order to detect pages with identical links:
    game_views = assign_page_ids(game_views, assign_special_pages=False)
    fingerprinted_pages = build_fingerprinted_pages(fake_pdf, game_views)
    while True:
        print(f'Pass {pass_number} - #views removed so far: {total_views_removed}')
        gv_per_page_fingerprint, filtered_fp_pages = {}, []
        print_memory_stats()  # Per safety, this function used to eat up memory
        for fp_page in tqdm(fingerprinted_pages, disable='NO_TQDM' in os.environ):
            existing_matching_gv = gv_per_page_fingerprint.get(fp_page.fingerprint)
            # 2nd condition ensures checkpoints are preserved: removing it would break nothing though.
            # 3rd condition ensures we don't alter secrets_cound in the process.
            if existing_matching_gv and (not fp_page.game_view.state or fp_page.game_view.state.milestone != GameMilestone.CHECKPOINT) and (not fp_page.game_view.state or fp_page.game_view.state.secrets_found == existing_matching_gv.state.secrets_found):
                assert fp_page.game_view.page_id != existing_matching_gv.page_id, f'Infinite loop detected in reducer!\n{fp_page.game_view}\n{existing_matching_gv}'
                if print_reduced_views:
                    gs = fp_page.game_view.state
                    print('- reducer.removes:', f'{gs.coords}/{gs.facing} HP={gs.hp} round={gs.combat and gs.combat.round}')
                    gs = existing_matching_gv.state
                    print('  identical to:   ', f'{gs.coords}/{gs.facing} HP={gs.hp} round={gs.combat and gs.combat.round}')
                    print('  differing:   \n' + indent(fp_page.game_view.state.differing(existing_matching_gv.state), '    '), end='')
                total_views_removed += 1
                fp_page.game_view.page_id_from(existing_matching_gv)
                for incoming_fp_page in fp_page.incoming_pages:
                    incoming_fp_page.fingerprint = compute_fingerprint(fake_pdf, incoming_fp_page.game_view)
            else:
                gv_per_page_fingerprint[fp_page.fingerprint] = fp_page.game_view
                filtered_fp_pages.append(fp_page)
        pass_number += 1
        no_views_removed = len(fingerprinted_pages) == len(filtered_fp_pages)
        fingerprinted_pages = filtered_fp_pages
        if no_views_removed:
            break
    print(f'-{100*total_views_removed/len(game_views):.1f}% of views were removed by the reducer')
    return [fp_page.game_view for fp_page in fingerprinted_pages]


def build_fingerprinted_pages(fake_pdf, game_views):
    print('FingerprintedPages build step 1/2: initialization')
    fp_pages = []
    for game_view in tqdm(game_views, disable='NO_TQDM' in os.environ):
        fp_pages.append(FingerprintedPage(fake_pdf, game_view))
    print('FingerprintedPages build step 2/2: setting .incoming_pages')
    fp_pages_per_page_id = {fp_page.game_view.page_id: fp_page for fp_page in fp_pages}
    for fp_page in tqdm(fp_pages, disable='NO_TQDM' in os.environ):
        for game_view in fp_page.game_view.actions.values():
            if game_view:
                fp_pages_per_page_id[game_view.page_id].incoming_pages.append(fp_page)
    return fp_pages


class FingerprintedPage:
    def __init__(self, fake_pdf, game_view):
        self.game_view = game_view
        self.fingerprint = compute_fingerprint(fake_pdf, game_view)
        self.incoming_pages = []  # FingerprintedPages


def compute_fingerprint(fake_pdf, game_view):
    fake_pdf.reset()
    with disable_tracing():  # avoids perfs._EXEC_TIMES_MS eating memory
        render_page(fake_pdf, game_view, render_victory_noop)
    return fake_pdf.get_fingerprint()


def render_victory_noop(*_): pass


class FakePdfRecorder:
    'Fake fpdf.FPDF class that must implement all the methods used during the pages rendering'
    def __init__(self):
        self.image_cache = ImageCache()
        self._calls = []
        self._links = {}

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

    def image(self, name, x=None, y=None, w=0, h=0, link='', title=None, alt_text=None):
        self._calls.append(('image', name, x, y, w, h, link, title, alt_text))

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

    def link(self, x, y, w, h, link, alt_text=None):
        page_or_url = link if isinstance(link, str) else self._links[link]
        self._calls.append(('link', x, y, w, h, page_or_url, alt_text))

    def reset(self):  # Note that ._links MUST be preserved, otherwise a 1st over-reduce glitch can be seen after talking to Seamus in the Sanitarium
        self._calls = []

    def get_fingerprint(self):
        return hash(tuple(self._calls))
