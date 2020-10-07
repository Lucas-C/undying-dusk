'This module role is to iterate all the game states reachable by the player.'
from random import shuffle

from .entities import GameMode, GameView
from .render import render_filler_page, render_trick

from .mod.campaign import CHECKPOINTS
from .mod.easteregg import insert_eegggv


START_PAGE_ID = 7  # skipping title, disclaimer & 4 pages of tutorial


def assign_page_ids(game_views, assign_reverse_id=True):
    gv_per_fixed_id = {gv.state.fixed_id: gv for gv in game_views if gv.state and gv.state.fixed_id}
    assert not any(fixed_id > len(game_views) for fixed_id in gv_per_fixed_id.keys()), f'Not enough GameViews ({len(game_views)}) to assign some of them with fixed IDs: {list(gv_per_fixed_id.keys())}'
    attempt = 0
    while True:
        attempt += 1
        if assign_reverse_id:
            print(f'Attempt at assigning reversed page ID: {attempt}')
        shuffle(game_views)  # needed to render pages in a random order
        assigner = Assigner(assign_reverse_id, gv_per_fixed_id)
        if assigner.attempt(game_views):
            return assigner.out_game_views  # reverse ID assignation is valid ! => exiting "while" loop

class Assigner:
    def __init__(self, assign_reverse_id, gv_per_fixed_id):
        self.assign_reverse_id = assign_reverse_id
        self.gv_per_fixed_id = dict(gv_per_fixed_id)  # copy so that we can safely reassign values to None
        self.next_page_id, self.out_game_views, self.reversed_id_gv = START_PAGE_ID, [], None

    def attempt(self, game_views):
        try:
            for game_view in game_views:
                if game_view.state and game_view.state.fixed_id:
                    continue

                # Dead-end useful sanity check:
                if game_view.state:
                    action_names = list(game_view.actions.keys())
                    dead_end_ok = game_view.state.last_checkpoint == len(CHECKPOINTS)
                    assert_error_msg = f'Non game-ending dead-end reached: {action_names} - {game_view}'
                    if game_view.state.mode == GameMode.INFO:
                        assert 'SHOW-INFO' in action_names or dead_end_ok, assert_error_msg
                    else:
                        assert action_names not in ([], ['SHOW-INFO']) or dead_end_ok or game_view.state.milestone >= 2, assert_error_msg

                if game_view.prev_page_trick_game_view:
                    trick = game_view.prev_page_trick_game_view.state.trick
                    assert trick
                    trick_game_view = GameView(renderer=_render_trick(game_view.prev_page_trick_game_view))
                    trick_game_view.set_page_id(self.next_page_id)
                    self.out_game_views.append(trick_game_view)
                    self._increment_next_page_id()
                    for _ in range(trick.filler_pages):
                        filler_game_view = GameView(renderer=render_filler_page)
                        filler_game_view.set_page_id(self.next_page_id)
                        self.out_game_views.append(filler_game_view)
                        self._increment_next_page_id()
                if game_view.state and game_view.state.reverse_id and self.assign_reverse_id:
                    assert not self.reversed_id_gv, 'Current algorithm cannot handle several GameView asking for a .reverse_id'
                    src_page_id = game_view.src_view.page_id
                    if not src_page_id or src_page_id >= self.next_page_id or src_page_id < 100:
                        print(f'reverse ID assignation ABORT - src_page_id={src_page_id} next_page_id={self.next_page_id}')
                        raise StopIteration  # attempting another reverse ID assignation
                    if game_view.src_view.next_page_trick_game_view:
                        src_page_id += 1 + game_view.src_view.next_page_trick_game_view.state.trick.filler_pages
                    reversed_id = _reverse_number(src_page_id)
                    if reversed_id == src_page_id or reversed_id >= len(game_views) or src_page_id % 10 == 0 or reversed_id < self.next_page_id:
                        print(f'reverse ID assignation ABORT - reversed_id={reversed_id}')
                        raise StopIteration  # attempting another reverse ID assignation
                    print(f'ID reversal: {src_page_id} -> {reversed_id}')
                    assert game_view.set_page_id(reversed_id)
                    self.reversed_id_gv = game_view
                else:
                    if game_view.set_page_id(self.next_page_id):
                        self.out_game_views.append(game_view)
                        self._increment_next_page_id()
                    else:  # can happen with the reducer, when trying to assign a page ID,
                           # to a view that already takes its ID from another one
                        assert not self.reversed_id_gv, 'Not implemented'
                        self.out_game_views.append(game_view)
                if game_view.next_page_trick_game_view:
                    trick = game_view.next_page_trick_game_view.state.trick
                    assert trick
                    for _ in range(trick.filler_pages):
                        filler_game_view = GameView(renderer=render_filler_page)
                        filler_game_view.set_page_id(self.next_page_id)
                        self.out_game_views.append(filler_game_view)
                        self._increment_next_page_id()
                    trick_game_view = GameView(renderer=_render_trick(game_view.next_page_trick_game_view))
                    trick_game_view.set_page_id(self.next_page_id)
                    self.out_game_views.append(trick_game_view)
                    self._increment_next_page_id()
        except StopIteration:
            return False
        # Ensure all GV requiring a fixed ID have been processed:
        assert not any(self.gv_per_fixed_id.values())
        return True

    def _increment_next_page_id(self):
        self.next_page_id += 1
        if self.reversed_id_gv and self.next_page_id == self.reversed_id_gv.page_id:
            assert self.next_page_id not in self.gv_per_fixed_id, 'Conflicting need to use this page ID :('
            self.out_game_views.append(self.reversed_id_gv)
            self._increment_next_page_id()
        gv = self.gv_per_fixed_id.get(self.next_page_id)
        if gv:
            gv.set_page_id(self.next_page_id)
            assert gv.state.fixed_id == gv.page_id
            self.out_game_views.append(gv)
            self.gv_per_fixed_id[self.next_page_id] = None
            self._increment_next_page_id()
        easteregg_game_view = insert_eegggv(self.next_page_id)
        if easteregg_game_view:
            easteregg_game_view.set_page_id(self.next_page_id)
            self.out_game_views.append(easteregg_game_view)
            self._increment_next_page_id()


def _render_trick(trick_game_view):
    # Note: inlining this lambda triggers a justified cell-var-from-loop Pylint warning
    return lambda pdf: render_trick(pdf, trick_game_view)


def _reverse_number(number):
    result = 0
    while number:
        result = result*10 + (number % 10)
        number //= 10
    return result
