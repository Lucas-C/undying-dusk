from .entities import GameMode
from .js import atlas, shop
from .logs import log
from .mapscript import mapscript_get_enemy_at
from .mazemap import avatar_can_move_to, mazemap_is_exit, mazemap_is_shop, mazemap_next_pos_facing, mazemap_get_tile
from .power import power_burn, power_unlock
from .warp_portals import warp_portal_teleport

from .mod.books import examine_bookshelf
from .mod.konami import custom_explore_logic
from .mod.world import custom_can_burn, custom_can_push


ROTATIONS_PER_FACING = {
    'south': { 'TURN-LEFT': 'east', 'TURN-RIGHT': 'west' },
    'west': { 'TURN-LEFT': 'south', 'TURN-RIGHT': 'north' },
    'north': { 'TURN-LEFT': 'west', 'TURN-RIGHT': 'east' },
    'east': { 'TURN-LEFT': 'north', 'TURN-RIGHT': 'south' },
}
BURN_AND_PUSH_ALLOWED = True  # for --no-script mode


def explore_logic(game_view, actions, _GameView):
    if game_view.state.map_id < 0:  # indicates the avatar is in a place that cannot be explored
        return
    game_state = game_view.state.clean_copy()
    next_pos_facing = mazemap_next_pos_facing(*game_state.coords[1:], game_state.facing)
    next_tile_facing = mazemap_get_tile(game_view, game_state.map_id, *next_pos_facing)
    # First, handling bookshelves examination / book closing.
    # It must be done first as it can trigger an early return.
    if next_tile_facing in (34, 35):
        book = game_view.state.book
        if book:
            if book.hidden_trigger and book.hidden_trigger not in game_view.state.hidden_triggers:
                game_state = game_state.with_hidden_trigger(book.hidden_trigger)
            if book.next:
                game_state = game_state._replace(book=book.next)
            elif game_view.state.shop_id >= 0:  # Means a CutScene follows this book opening
                game_state = game_state._replace(mode=GameMode.DIALOG, shop_id=game_view.state.shop_id)
            actions['CLOSING-BOOK'] = _GameView(game_state)
            return  # we do not display INFO nor ARROW buttons
        examine_bookshelf(game_state, next_pos_facing, actions, _GameView)
    # Second, allow to display the info screen:
    info_view = _show_info(game_view, game_state, _GameView)
    assert 'SHOW-INFO' not in actions, game_view
    actions['SHOW-INFO'] = info_view
    # Third, considering the 2 rotations always available:
    for action_name, facing in ROTATIONS_PER_FACING[game_state.facing].items():
        actions[action_name] = _GameView(custom_explore_logic(action_name, game_view.state, game_state._replace(facing=facing)))
    # Fourth, considering moving forward/backward:
    _map = atlas().maps[game_state.map_id]
    for action_name in ('MOVE-FORWARD', 'MOVE-BACKWARD'):
        x, y = pos_for_move_action(game_state, action_name)
        x, y = warp_portal_teleport(game_state.coords, (x, y))
        new_coords = (game_state.map_id, x, y)
        if not avatar_can_move_to(game_view, *new_coords):
            continue
        new_facing = game_state.facing
        enemy = mapscript_get_enemy_at(new_coords,game_state)
        if (action_name == 'MOVE-BACKWARD' and enemy and not game_view.enemy_vanquished(new_coords)):
            # We force the player to face the enemy,
            # as otherwise they could "pass through" them.
            turn_around = {"north":"south","south":"north","east":"west","west":"east"}
            new_facing = turn_around[new_facing]
        # Shop have priority over map exits, but they can now be temporary, allowing for one-time cut-scenes:
        map_shop = mazemap_is_shop(_map, x, y)
        if map_shop and not new_coords in game_state.triggers_activated:
            # ^ the 2nd condition means it is an ephemeral shop hat has already been visited
            log(game_state, f'entering shop: {shop()[map_shop.shop_id].name}')
            actions[action_name] = _GameView(game_state._replace(mode=GameMode.DIALOG, shop_id=map_shop.shop_id, x=x, y=y))
            continue
        map_exit = mazemap_is_exit(_map, x, y)
        if map_exit:
            can_enter_map = avatar_can_move_to(game_view, map_exit.dest_map, map_exit.dest_x, map_exit.dest_y)
            if can_enter_map:
                actions[action_name] = _GameView(enter_map(game_state, map_exit))
            else:
                message = "Seems like something\nis blocking the door\nfrom behind"
                actions[action_name] = _GameView(game_state._replace(message=message))
            continue
        actions[action_name] = _GameView(custom_explore_logic(action_name, game_view.state,
                                         game_state._replace(x=x, y=y, facing=new_facing)))
    rolling_boulder_in_front = False
    for rolling_boulder in game_state.rolling_boulders:
        if rolling_boulder.coords == (game_state.map_id, *next_pos_facing):
            rolling_boulder_in_front = True
    if BURN_AND_PUSH_ALLOWED and next_tile_facing in (33, 36, 20, 21, 22) and not rolling_boulder_in_front:  # facing a box or a stationary boulder
        custom = custom_can_push(game_state, actions)
        if custom:
            action_name, next_gv = custom
            actions[action_name] = next_gv
        else:
            next_next_pos_facing = mazemap_next_pos_facing(*next_pos_facing, game_state.facing)
            next_next_tile_facing = mazemap_get_tile(game_view, game_state.map_id, *next_next_pos_facing)
            if next_next_tile_facing in (6, 5, 1, 0, None):  # empty tile behind
                actions['PUSH'] = _GameView(_push_object(game_state, next_pos_facing, next_next_pos_facing, next_tile_facing, next_next_tile_facing))
            else:
                actions['NO_PUSH'] = None
    if BURN_AND_PUSH_ALLOWED and game_state.spellbook >= 2 and next_tile_facing in (16, 33, 36) and custom_can_burn(game_state):  # facing a bone_pile or box with BURN spell
        actions['BURN'] = _GameView(power_burn(game_state, next_pos_facing, next_tile_facing)) if game_state.mp else None
    if game_state.spellbook >= 3 and next_tile_facing == 18:  # facing a locked_door with UNLOCK spell available
        actions['UNLOCK'] = _GameView(power_unlock(game_state, next_pos_facing)) if game_state.mp else None
    if 'MOVE-FORWARD' in actions:  # adding user-friendly click zones in the middle of the screen:
        if next_tile_facing in (3, 11):  # dungeon or village door
            actions['OPEN_DOOR'] = actions['MOVE-FORWARD']
        if next_tile_facing == 27:  # open portal
            actions['PASS_PORTAL'] = actions['MOVE-FORWARD']
        if next_tile_facing == 47:  # ivy - does it make puzzle too easy?
            actions['PASS_BEHIND_IVY'] = actions['MOVE-FORWARD']


def _push_object(game_state, next_pos_facing, next_next_pos_facing, next_tile_facing, next_next_tile_facing):
    log(game_state, f'push_box @ {game_state.coords}: {next_pos_facing} -> {next_next_pos_facing}')
    next_coords_facing = (game_state.map_id, *next_pos_facing)
    next_tile_override = game_state.tile_override_at(next_coords_facing)
    if next_tile_override:
        assert next_tile_override == next_tile_facing
        game_state = game_state.without_tile_override(next_coords_facing)
    _map = atlas().maps[game_state.map_id]
    next_x, next_y = next_pos_facing
    if _map.tiles[next_y][next_x] not in (1, 5, 6):  # initial box position, or opened chest -> masking it
        empty_tile_id = {33: 5, 36: 1, 20: 1, 21: 5, 22: 6}[next_tile_facing]
        game_state = game_state.with_tile_override(empty_tile_id, next_coords_facing)
    if next_next_tile_facing in (0, None) and next_tile_facing in (33,36):
        return game_state._replace(message='The box falls into the void')
    if next_next_tile_facing in (0, None) and next_tile_facing in (20,21,22):
        return game_state._replace(message='The boulder falls to the void')
    next_next_coords_facing = (game_state.map_id, *next_next_pos_facing)
    next_next_tile_override = game_state.tile_override_at(next_next_coords_facing)
    if next_next_tile_override:
        assert next_next_tile_override in (1, 5, 6)
        game_state = game_state.without_tile_override(next_next_coords_facing)
    if next_tile_facing in (33, 36):
        new_tile_id = {1: 36, 5: 33}[next_next_tile_facing]
        return game_state.with_tile_override(new_tile_id, next_next_coords_facing)\
                         ._replace(message='You push the box forward')
    if next_tile_facing in (20, 21, 22):
        new_tile_id = {1: 20, 5: 21, 6: 22}[next_next_tile_facing]
        return game_state.with_tile_override(new_tile_id, next_next_coords_facing)\
                         ._replace(message='You push the boulder forward')
    assert False


def _show_info(game_view, game_state, _GameView):
    info_view = _GameView(game_state._replace(mode=GameMode.INFO))
    if 'SHOW-INFO' in info_view.actions:
        if info_view.actions['SHOW-INFO'].state.message:
            if not game_view.state.message:
                # Prefer a redirect from the INFO page to a page without message:
                del info_view.actions['SHOW-INFO']
                info_view.actions['SHOW-INFO'] = game_view
        elif info_view.actions['SHOW-INFO'].state.milestone:
            if not game_view.state.milestone:
                # Prefer a redirect from the INFO page to a page without milestone:
                del info_view.actions['SHOW-INFO']
                info_view.actions['SHOW-INFO'] = game_view
        elif info_view.actions['SHOW-INFO'].state.trick:
            if not game_view.state.trick:
                # Prefer a redirect from the INFO page to a page without trick:
                del info_view.actions['SHOW-INFO']
                info_view.actions['SHOW-INFO'] = game_view
        elif info_view.actions['SHOW-INFO'].state.extra_render:
            if not game_view.state.extra_render:
                # Prefer a redirect from the INFO page to a page without extra_render:
                del info_view.actions['SHOW-INFO']
                info_view.actions['SHOW-INFO'] = game_view
        elif info_view.actions['SHOW-INFO'].state.puzzle_step is not None:
            if game_view.state.puzzle_step is None:
                # Prefer a redirect from the INFO page to a page without puzzle_step:
                del info_view.actions['SHOW-INFO']
                info_view.actions['SHOW-INFO'] = game_view
        else:
            assert info_view.actions['SHOW-INFO'].state == game_state, f"\n{info_view.actions['SHOW-INFO'].state}\n!=\n{game_state}"
    else:
        # when getting back from the INFO page, we should not have any message displayed, and not get back to a MILESTONE state
        info_view.actions['SHOW-INFO'] = game_view
    return info_view


def enter_map(game_state, map_exit):
    assert map_exit
    message = atlas().maps[map_exit.dest_map].name
    log(game_state, f'entering map: {message}')
    if map_exit.facing == 'SAME':
        facing = game_state.facing
    else:
        facing = map_exit.facing
        assert facing in {'north','east','south','west'}
    return game_state._replace(map_id=map_exit.dest_map,
                               x=map_exit.dest_x,
                               y=map_exit.dest_y,
                               facing=facing,
                               message=message)


def pos_for_move_action(game_state, move_action):
    if move_action not in ('MOVE-FORWARD', 'MOVE-BACKWARD'):
        raise RuntimeError(f'Unsupported move action: {move_action}')
    speed = 1 if (move_action == 'MOVE-FORWARD') else -1
    return mazemap_next_pos_facing(game_state.x, game_state.y, game_state.facing, speed)


def disable_burn_and_push():
    global BURN_AND_PUSH_ALLOWED
    BURN_AND_PUSH_ALLOWED = False
