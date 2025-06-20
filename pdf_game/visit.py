'This module role is to iterate all the game states reachable by the player.'
import sys
from collections import defaultdict
from queue import LifoQueue
from textwrap import indent

from .ascii import map_as_string
from .assigner import assign_page_ids
from .deadends import detect_deadends
from .explore import disable_burn_and_push
from .entities import CutScene, GameMilestone, GameMode, GameState, GameView
from .js import avatar
from .logs import log, log_victorious_combats, log_paths_diff, diff_game_states
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
    return GameState(map_id=avatar().map_id,
                     x=avatar().x,
                     y=avatar().y,
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
                     mode=GameMode.DIALOG,
                     shop_id=8)  # "hardcoded" at heroine-dusk/release/js/title.js:153


def visit_game_views(args):
    global CHECKPOINTS, VICTORY_POS
    initial_state = build_initial_state()

    if args.only_print_map is not None:
        print(map_as_string(GameView(initial_state._replace(map_id=args.only_print_map, x=0, y=0), src_view=None)))
        sys.exit(0)

    start_at_checkpoint = 0
    if args.inbetween_checkpoints:
        start_cp, end_cp = args.inbetween_checkpoints.split('-')
        start_at_checkpoint = int(start_cp) if start_cp else 0
        end_cp = int(end_cp) if end_cp else len(CHECKPOINTS)
        CHECKPOINTS = CHECKPOINTS[:end_cp]
        VICTORY_POS = CHECKPOINTS[-1]

    if args.no_script:  # "spectator" / "empty world" mode
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
        new_gv = game_view_per_state.get(state)
        if not new_gv:
            new_gv = GameView(state, src_view)
            if new_gv.state.mode == GameMode.EXPLORE:
                # We must 1st insert it in game_view_per_state to avoid an infinite recursion:
                game_view_per_state[state] = new_gv
                # Executing it now/there ensures it is only performed once per GV:
                mapscript_exec(new_gv, lambda state: _GameView(state, new_gv))
                # The GameState can be changed by the mapscript:
                if new_gv.state != state:
                    del game_view_per_state[state]
                    existing_gv_for_state = game_view_per_state.get(new_gv.state)
                    if existing_gv_for_state:
                        # This could be problematic if a reference to new_gv has been "captured"
                        # while executing mapscript, for example if "child" _GameView have been created...
                        new_gv = existing_gv_for_state
            game_view_per_state[new_gv.state] = new_gv
        return new_gv

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
                # Extra logging when a checkpoint happens just after a combat:
                if checkpoint_game_views[0].src_view.state.mode == GameMode.COMBAT:
                    print('Combat choices leading to victory:')
                    log_victorious_combats(checkpoint_game_views[0].src_view)
                initial_views = checkpoint_game_views
            else:
                break
        # pylint: disable=undefined-loop-variable
        assert start_view, f'No start view found: maybe due to an invalid --start-at-checkpoint ({start_at_checkpoint}) ? #checkpoints={len(CHECKPOINTS)} last-#GameViews={len(game_views_until_checkpoint)} last-i={i}'
        print(f'{len(game_views)} views have been iterated')

    check_no_duplicate(game_views)

    if args.detect_deadends:
        with trace_time('visit:detect_deadends'):
            detect_deadends(game_views)
            sys.exit(0)

    if not args.no_reducer:
        with trace_time('visit:reduce_views'):
            game_views = reduce_views(game_views, args.print_reduced_views)

    with trace_time('visit:assign_page_ids'):
        game_views = assign_page_ids(game_views)
    assert start_view.page_id

    log_checkpoints_page_ids(game_views)
    log_scenes_page_ids(game_views)

    return start_view, game_views


def log_checkpoints_page_ids(game_views):
    for game_view in game_views:
        game_state = game_view.state
        if game_state and game_state.milestone in (GameMilestone.CHECKPOINT, GameMilestone.VICTORY):
            checkpoint = next(cp for i, cp in enumerate(CHECKPOINTS, start=1)
                              if i == game_state.last_checkpoint)
            print(f'Page ID for checkpoint {game_state.last_checkpoint}: {game_view.page_id} ({game_state.facing}/{"+".join(game_state.secrets_found)}): {checkpoint.description}')
            if game_state.milestone == GameMilestone.VICTORY:
                depth = 1
                while game_view.src_view:
                    depth += 1
                    game_view = game_view.src_view
                print(f'(depth / #states from start: {depth})')

def log_scenes_page_ids(game_views):
    scene_game_states = {}
    for game_view in game_views:
        game_state = game_view.state
        # Excluding actual shops (ID <= 4):
        if game_state and game_state.shop_id > 4 and game_view.src_view and game_view.src_view.state.shop_id == -1:
            scene = CutScene.from_id(game_state.shop_id)
            existing_gs = scene_game_states.get((game_state.facing, game_state.secrets_found))
            print(f'Page ID for scene {game_state.shop_id} {"" if existing_gs else "(first page)"}: {game_view.page_id} ({game_state.facing}/{"+".join(game_state.secrets_found)}) {scene.name}')
            if existing_gs:
                # print('Diff with other GameState leading to this scene:')
                print(indent(existing_gs.differing(game_state), '  '), end='')
            scene_game_states[(game_state.facing, game_state.secrets_found)] = game_state


def iterate_game_views(checkpoint, checkpoint_id, start_views, _GameView):
    game_views, processed, processing = set(), set(), LifoQueue()
    for start_view in start_views:
        processing.put(start_view)
        processed.add(hash(start_view))
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
            if new_game_view.state.mode == checkpoint.mode and checkpoint.matches(new_game_view.state) and new_game_view.state.hp > 0:
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
            if hash(new_game_view) not in processed:
                game_views.add(new_game_view)
                processed.add(hash(new_game_view))  # we need a separate set of GS hashes, as "new_game_view not in game_views" would uses "id(new_game_view)"
                milestone = new_game_view.state.milestone
                if milestone == GameMilestone.GAME_OVER:
                    log_msg = (f'defeated - hp: {new_game_view.state.hp}/{new_game_view.state.max_hp}'
                               f' mp: {new_game_view.state.mp}/{new_game_view.state.max_mp}')
                    if new_game_view.state.combat:
                        combat = new_game_view.state.combat
                        log_msg += f' - on round {combat.round} - {combat.enemy.name} hp: {combat.enemy.hp}'
                        post_defeat = combat.enemy.post_defeat
                        if post_defeat and combat.enemy.post_defeat_condition:
                            should_render_post_defeat = combat.enemy.post_defeat_condition(new_game_view.state)
                        else:
                            should_render_post_defeat = bool(post_defeat)
                        if should_render_post_defeat and not hasattr(post_defeat, 'game_view'):
                            post_defeat.game_view = GameView(src_view=new_game_view, renderer=post_defeat)
                            game_views.add(post_defeat.game_view)
                            processed.add(hash(post_defeat.game_view))
                    if new_game_view.state.rolling_boulders:
                        log_msg += f' - crushed-by-boulder@{new_game_view.state.coords}/{new_game_view.state.facing}'
                    log(new_game_view.state, log_msg)
                elif milestone not in (GameMilestone.CHECKPOINT, GameMilestone.VICTORY) or new_game_view.state.last_checkpoint == start_views[0].state.last_checkpoint:
                    processing.put(new_game_view)
            if not action_name:  # means it is a "secret" action without any link on the page
                del actions[action_name]  # no link will be rendered
    return game_views, checkpoint_game_views


def check_no_duplicate(game_views):
    print('Ensuring no duplicate GameViews exist...')
    gvs_per_hash = defaultdict(list)
    for gv in game_views:
        if gv.state:
            gvs_per_hash[hash(gv)].append(gv)
    duplicate_gvs_str = '\n'.join('\n'.join(map(str, gvs)) for gvs in gvs_per_hash.values() if len(gvs) > 1)
    assert not duplicate_gvs_str, f'Duplicate game views found:\n{duplicate_gvs_str}'
    print('Check passed ✔️')


def _normalized_state(game_view, min_checkpoint_to_ignore_gold=9):
    # Some secrets are achieved by using gold (e.g. fountain):
    gs = game_view.state.clean_copy()
    ignore_gold = gs.last_checkpoint >= min_checkpoint_to_ignore_gold
    return gs._replace(facing='',
                       # Ignoring fields varying due to secrets:
                       gold=0 if ignore_gold else gs.gold,
                       hidden_triggers=(), secrets_found=(),
                       vanquished_enemies=(),  # (e.g. shadow soul secret)
                       tile_overrides=(), triggers_activated=())  # (e.g. shadow soul secret)
