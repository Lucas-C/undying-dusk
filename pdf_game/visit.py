'This module role is to iterate all the game states reachable by the player.'
import sys
from collections import defaultdict
from queue import LifoQueue

from .ascii import map_as_string
from .assigner import assign_page_ids
from .deadends import detect_deadends
from .explore import disable_burn_and_push
from .entities import GameMilestone, GameMode, GameState, GameView
from .js import avatar
from .logs import log, log_paths_diff, diff_game_states
from .mapscript import mapscript_exec
from .perfs import trace_time
from .reducer import reduce_views

# pylint: disable=unused-import
from .combat import combat_logic
from .explore import explore_logic
from .info import info_logic
from .shop_dialog import dialog_logic

from .mod.campaign import CHECKPOINTS, VICTORY_POS
from .mod.pages import SECRET_ENDING_ID, render_secret_ending
from .mod.world import make_bones_and_boxes_walkables


def build_initial_state():
    return GameState(x=avatar().x,
                     y=avatar().y,
                     map_id=avatar().map_id,
                     facing=avatar().facing,
                     weapon=avatar().weapon,
                     armor=avatar().armor,
                     hp=avatar().hp,
                     max_hp=avatar().max_hp,
                     mp=avatar().mp,
                     max_mp=avatar().max_mp,
                     gold=avatar().gold,
                     bonus_atk=avatar().bonus_atk,
                     bonus_def=avatar().bonus_def,
                     spellbook=avatar().spellbook,
                     mode=GameMode.DIALOG, shop_id=8)  # "hardcoded" at heroine-dusk/release/js/title.js:153


def visit_game_views(inbetween_checkpoints=None, print_only_map_id=None, no_script=False, enable_reducer=True, enable_deadend_detection=True):
    global CHECKPOINTS, VICTORY_POS
    initial_state = build_initial_state()

    if print_only_map_id is not None:
        print(map_as_string(GameView(initial_state._replace(map_id=print_only_map_id, x=0, y=0), src_view=None)))
        sys.exit(0)

    start_at_checkpoint = 0
    if inbetween_checkpoints:
        start_cp, end_cp = inbetween_checkpoints.split('-')
        start_at_checkpoint = int(start_cp) if start_cp else 0
        end_cp = int(end_cp) if end_cp else len(CHECKPOINTS)
        CHECKPOINTS = CHECKPOINTS[:end_cp]
        VICTORY_POS = CHECKPOINTS[-1]

    if no_script:  # "spectator" / "empty world" mode
        CHECKPOINTS = (CHECKPOINTS[-1],)
        # We need to be able to open all doors with the UNLOCK spell:
        initial_state = initial_state._replace(spellbook=3, max_mp=100, mp=100)
        # We make everything un-burnable & boxes un-pushable to avoid the #states count to explode:
        disable_burn_and_push()
        # We make boxes walkable to not be blocked by them:
        make_bones_and_boxes_walkables()

    assert not start_at_checkpoint or start_at_checkpoint <= len(CHECKPOINTS)

    initial_view = GameView(initial_state, src_view=None)
    secret_ending_view = GameView(GameState(fixed_id=SECRET_ENDING_ID), renderer=render_secret_ending)
    game_view_per_state = {initial_state: initial_view}
    def _GameView(state, src_view):  # get existing view for given state or build one
        if state not in game_view_per_state:
            new_gv = GameView(state, src_view)
            game_view_per_state[state] = new_gv
            if new_gv.state.mode == GameMode.EXPLORE:
                # Executing it now/there ensures it is only performed once per GV:
                mapscript_exec(new_gv, lambda state: _GameView(state, new_gv))
                state = new_gv.state  # the GameState can be changed by the mapscript
                if state not in game_view_per_state:
                    game_view_per_state[state] = new_gv
        return game_view_per_state[state]

    with trace_time('visit:iterate_game_views'):
        start_view, initial_views, game_views = None, [initial_view], [initial_view, secret_ending_view]
        for i, checkpoint in enumerate(CHECKPOINTS):
            game_views_until_checkpoint, checkpoint_game_views = iterate_game_views(checkpoint, i + 1, initial_views, _GameView)
            if not start_at_checkpoint or i + 1 >= start_at_checkpoint:
                game_views.extend(game_views_until_checkpoint)
                if not start_view:
                    if start_at_checkpoint:
                        if start_at_checkpoint == i + 1:
                            game_views = checkpoint_game_views
                            if checkpoint_game_views:
                                start_view = checkpoint_game_views[0]
                            else:
                                print('Checkpoint not reached')
                    else:
                        start_view = initial_views[0]
            print(f'Checkpoint {i + 1}: #visited_states={len(game_views_until_checkpoint)} #checkpoint_GVs={len(checkpoint_game_views)}')
            if checkpoint_game_views:
                print(map_as_string(checkpoint_game_views[0]))
                initial_views = checkpoint_game_views
            else:
                break
        assert start_view, f'No start view found: maybe due to an invalid --start-at-checkpoint ({start_at_checkpoint}) ? #checkpoints=({len(CHECKPOINTS)})'
        print(f'{len(game_views)} views have been iterated')

    # duplicate_gvs_str = '\n'.join(str(gv) for gv in game_views if game_views.count(gv) > 1)
    # assert not duplicate_gvs_str, f'There are duplicate game views!\n{duplicate_gvs_str}'  # costly but useful sanity check

    if enable_deadend_detection:
        with trace_time('visit:detect_deadends'):
            detect_deadends(game_views)
            sys.exit(0)

    if enable_reducer:
        with trace_time('visit:reduce_views'):
            game_views = reduce_views(game_views)

    with trace_time('visit:assign_page_ids'):
        game_views = assign_page_ids(game_views)
    assert start_view.page_id

    for game_view in game_views:
        if game_view.state and game_view.state.milestone in (GameMilestone.CHECKPOINT, GameMilestone.VICTORY) and any(cp.matches(game_view.state) for cp in CHECKPOINTS):
            print(f'Page ID for checkpoint {game_view.state.last_checkpoint}: {game_view.page_id} ({game_view.state.facing}/{"+".join(game_view.state.secrets_found)})')

    return start_view, game_views


def iterate_game_views(checkpoint, checkpoint_id, start_views, _GameView):
    game_views, processing = set(), LifoQueue()
    for start_view in start_views:
        processing.put(start_view)
    checkpoint_game_views = []
    while not processing.empty():
        game_view = processing.get()
        game_view.freeze_state = True
        actions = game_view.actions
        logic_for_mode = getattr(sys.modules[__name__], f'{game_view.state.mode.name.lower()}_logic')
        logic_for_mode(game_view, actions, _GameView=lambda state: _GameView(state, game_view))
        for action_name, new_game_view in list(actions.items()):  # list copy as it can be modified in the loop
            if not new_game_view:
                continue
            if new_game_view.state.mode == GameMode.EXPLORE and checkpoint.matches(new_game_view.state) and new_game_view.state.hp > 0:
                milestone = GameMilestone.VICTORY if checkpoint == VICTORY_POS else GameMilestone.CHECKPOINT
                new_gs_marked_as_milestone = new_game_view.state._replace(milestone=milestone, last_checkpoint=checkpoint_id)
                if new_gs_marked_as_milestone not in set(cp_gv.state for cp_gv in checkpoint_game_views):
                    new_game_view.state = new_gs_marked_as_milestone
                    log(new_game_view.state, f"CHECKPOINT: {new_game_view.state}", color='blue')
                    if checkpoint_game_views:
                        new_gv_bare_state = _normalized_state(new_game_view)
                        try:
                            if len(CHECKPOINTS) <= 1: raise StopIteration  # just an edge case with --no-script
                            differing_gv = next(cp_gv for cp_gv in checkpoint_game_views if new_gv_bare_state != _normalized_state(cp_gv))
                            log_paths_diff(differing_gv, new_game_view, actions_only=True)
                            diff_game_states(_normalized_state(differing_gv), new_gv_bare_state)
                            raise RuntimeError(f'CHECKPOINT {checkpoint_id} can be reached by more than one path')
                        except StopIteration:
                            checkpoint_game_views.append(new_game_view)
                    else:
                        checkpoint_game_views = [new_game_view]
            if new_game_view not in game_views and new_game_view not in start_views:
                game_views.add(new_game_view)
                milestone = new_game_view.state.milestone
                if milestone == GameMilestone.GAME_OVER:
                    log_msg = (f'defeated - hp: {new_game_view.state.hp}/{new_game_view.state.max_hp}'
                               f' mp: {new_game_view.state.mp}/{new_game_view.state.max_mp}')
                    if new_game_view.state.combat:
                        combat = new_game_view.state.combat
                        log_msg += f' - on round {combat.round} - {combat.enemy.name} hp: {combat.enemy.hp}'
                        post_defeat = combat.enemy.post_defeat
                        if post_defeat and not hasattr(post_defeat, 'game_view'):
                            post_defeat.game_view = GameView(src_view=game_view, renderer=post_defeat)
                            game_views.add(post_defeat.game_view)
                    if new_game_view.state.rolling_boulder:
                        log_msg += f' - crushed-by-boulder@{new_game_view.state.coords}/{new_game_view.state.facing}'
                    log(new_game_view.state, log_msg)
                elif milestone not in (GameMilestone.CHECKPOINT, GameMilestone.VICTORY) or new_game_view.state.last_checkpoint == start_views[0].state.last_checkpoint:
                    processing.put(new_game_view)
            if not action_name:  # means it is a "secret" action witout any link on the page
                del actions[action_name]  # no link will be rendered
    _ensure_no_duplicates(checkpoint_game_views)
    return game_views, checkpoint_game_views


def _normalized_state(gv, min_checkpoint_to_ignore_gold=9):
    # Some secrets are achieved by using gold (e.g. fountain):
    ignore_gold = gv.state.last_checkpoint >= min_checkpoint_to_ignore_gold
    return gv.state.clean_copy()._replace(facing='',
                                          # Ignoring fields varying due to secrets:
                                          gold=0 if ignore_gold else gv.state.gold,
                                          hidden_triggers=(), secrets_found=(),
                                          vanquished_enemies=(),  # (e.g. shadow soul secret)
                                          tile_overrides=(), triggers_activated=())  # (e.g. shadow soul secret)


def _ensure_no_duplicates(checkpoint_game_views):
    if len(checkpoint_game_views) != len(set(gv.state for gv in checkpoint_game_views)):
        cp_gvs_per_state = defaultdict(list)
        for cp_gv in checkpoint_game_views:
            cp_gvs_per_state[cp_gv.state].append(cp_gv)
        print('Checkpoint GameViews sharing a same state:')
        for cp_gvs in cp_gvs_per_state.values():
            if len(cp_gvs) > 1:
                print('\n'.join(str(cp_gv) for cp_gv in cp_gvs))
                print('---')
        assert False, 'Nooooo! Several GameViews exist for identical GameStates!'
