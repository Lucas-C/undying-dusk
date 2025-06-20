'Replicates heroine-dusk/release/js/mapscript.js'

import sys

from .entities import CombatState, Enemy, GameMilestone, GameMode, MessagePlacement, RollingBoulder
from .js import atlas, enemy
from .logs import log
from .mazemap import avatar_can_move_to, mazemap_next_pos_facing, mazemap_get_tile


DOOR_TILE_IDS = (3, 11, 18)


def mapscript_exec(game_view, _GameView):
    if game_view.state.bonus_atk:  # Boost decreases over time
        game_view.state = game_view.state._replace(bonus_atk=game_view.state.bonus_atk - 1)
    if game_view.state.bonus_def:  # Boost decreases over time
        game_view.state = game_view.state._replace(bonus_def=game_view.state.bonus_def - 1)
    # Boulder is moved BEFORE triggering scripts,
    # so that it stays still during the state it is added on the map
    if game_view.state.rolling_boulders:
        _mapscript_move_boulders(game_view)
    if game_view.state.coords in SCRIPTS_PER_TILE:
        _, script = SCRIPTS_PER_TILE.get(game_view.state.coords)
        script(game_view, _GameView)


def mapscript_is_tile_scripted(*coords):
    return coords in SCRIPTS_PER_TILE


def mapscript_tile_script_type(*coords):
    if coords in SCRIPTS_PER_TILE:
        return SCRIPTS_PER_TILE.get(coords)[0]
    return None


def mapscript_add_message(coords, message, facing=None, condition=None, msg_place=MessagePlacement.DOWN, extra_render=None):
    assert coords not in SCRIPTS_PER_TILE, f'Tile @ {coords} already scripted, cannot add message'
    def _mapscript_display_message(game_view, _):
        if (facing and game_view.state.facing != facing) or (condition and not condition(game_view.state)):
            return
        game_view.state = game_view.state._replace(message=message, msg_place=msg_place, extra_render=extra_render)
    SCRIPTS_PER_TILE[coords] = ('message', _mapscript_display_message)


def mapscript_add_enemy(coords, name, **kwargs):
    assert coords not in SCRIPTS_PER_TILE
    condition = kwargs.pop('condition', None)
    new_enemy = _make_enemy(name, **kwargs)
    # cf. https://github.com/PyCQA/pylint/issues/3877
    encounter_func = lambda gv, _: _mapscript_encounter_enemy(gv, new_enemy, condition)
    encounter_func.enemy = new_enemy
    encounter_func.condition = condition
    SCRIPTS_PER_TILE[coords] = ('enemy', encounter_func)


def _mapscript_encounter_enemy(game_view, new_enemy, condition=None):
    if game_view.state.combat or game_view.enemy_vanquished_here or (condition and not condition(game_view.state)):
        return
    game_view.state = game_view.state._replace(mode=GameMode.COMBAT,
                                               combat=CombatState(enemy=new_enemy))
    log(game_view.state, (f'facing: {new_enemy.name} @ {game_view.state.coords}'
                          f' with HP={game_view.state.hp} MP={game_view.state.mp}'
                          f' weapon={game_view.state.weapon} items={game_view.state.items}'))


def _make_enemy(name, **kwargs):
    enemy_id = getattr(enemy(), 'ENEMY_'+ name.upper(), None)
    category = kwargs.pop('category', None) or enemy().stats[enemy_id].category
    return Enemy(name=name, type=enemy_id, category=category, max_hp=kwargs['hp'], **kwargs)


def mapscript_get_enemy_at(coords, game_state):
    script = SCRIPTS_PER_TILE.get(coords)
    if script and script[0] == 'enemy' and (not script[1].condition or script[1].condition(game_state)):
        return script[1].enemy
    return None


def mapscript_add_chest(coords, treasure_id, grant_func=None, replace=False):
    assert not (replace ^ (coords in SCRIPTS_PER_TILE)), 'Tile already scripted, cannot add chest'
    SCRIPTS_PER_TILE[coords] = ('chest', lambda gv, _GameView: _mapscript_open_chest(gv, _GameView, treasure_id, grant_func))


def mapscript_remove_chest(coords):
    assert coords in SCRIPTS_PER_TILE
    del SCRIPTS_PER_TILE[coords]


CHEST_OVERRIDES = {
    2: 5,    # wall -> dungeon_ceiling (for 1st hidden scroll)
    8: 5,    # chest_interior -> dungeon_ceiling
    9: 1,    # chest_exterior -> dungeon_floor
    17: 17,  # hay pile -> hay pile | BEWARE: same tile => "already open" detection system won't work
    40: 40,  # fire -> fire | BEWARE: same tile => "already open" detection system won't work
    43: 42,  # stump_with_bottle -> stump
    46: 40,  # cauldron -> fire
    47: 47,  # dungeon_wall_with_ivy -> dungeon_wall_with_ivy | BEWARE: same tile => "already open" detection system won't work
}
def _mapscript_open_chest(game_view, _GameView, treasure_id, grant_func=None):
    if game_view.tile_override(game_view.state.coords):
        return  # chest already opened
    map_id, x, y = game_view.state.coords
    _map = atlas().maps[map_id]
    # display treasure + text & custom logic:
    game_view.state = game_view.state._replace(treasure_id=treasure_id, msg_place=MessagePlacement.UP)
    # Note that the message is placed higher (original logic from explore.js:explore_render())
    # hide the chest: add tile_override
    initial_tile_id = _map.tiles[y][x]
    assert initial_tile_id in CHEST_OVERRIDES, f'Unexpected initial tile id {initial_tile_id} @ {game_view.state.coords}'
    game_view.add_tile_override(CHEST_OVERRIDES[_map.tiles[y][x]])
    if isinstance(treasure_id, str):
        gold_str, gold_found = game_view.state.treasure_id.split('_')
        assert gold_str == 'gold'
        game_view.state = game_view.state._replace(message=f"{gold_found} gold", gold=game_view.state.gold + int(gold_found))
        log(game_view.state, '+' + game_view.state.message + f' ({gold_found})')
    else:
        grant_func = grant_func or getattr(sys.modules[__name__], f'_mapscript_grant_chest_{treasure_id}')
        if grant_func(game_view, _GameView) is not False:
            assert game_view.state.message, f'grant_func for chest @ {game_view.state.coords} must set a .message'
            log(game_view.state, '+' + game_view.state.message.replace('\n', ' '))


def mapscript_add_boulder(trigger_pos, start_at, _dir, facing=None, condition=None, message="You hear a loud thud.\nSomething is approaching"):
    def _mapscript_trigger_boulder(game_view, _):
        game_state = game_view.state
        if trigger_pos in game_state.triggers_activated:
            return
        if (facing and game_view.state.facing != facing) or (condition and not condition(game_view.state)):
            return
        log(game_state, f'+boulder @ {game_state.coords}')
        rolling_boulder = RollingBoulder(start_at, _dir, game_view.tile_override(start_at))
        if rolling_boulder.shadowed_tile_override:  # Removing previous tile override:
            game_view.remove_tile_override(start_at)
        game_view.add_tile_override(_get_boulder_tile_id(start_at), coords=start_at)
        game_view.state = game_view.state.with_trigger_activated(trigger_pos)\
                                         ._replace(rolling_boulders=game_view.state.rolling_boulders + (rolling_boulder,),
                                                   message=message,
                                                   msg_place=MessagePlacement.UP)
    SCRIPTS_PER_TILE[trigger_pos] = ('boulder_trigger', _mapscript_trigger_boulder)


def _mapscript_move_boulders(game_view):
    rolling_boulders = game_view.state.rolling_boulders
    assert rolling_boulders!=()
    next_rolling_boulders = ()
    for rolling_boulder in rolling_boulders:
        map_id, *boulder_pos = rolling_boulder.coords
        next_coords = (map_id, *mazemap_next_pos_facing(*boulder_pos, rolling_boulder.dir))
        if not avatar_can_move_to(game_view, *next_coords) or mazemap_get_tile(game_view, *next_coords) in DOOR_TILE_IDS:
            log(game_view.state, f'-boulder stopped @ {rolling_boulder.coords}, could not move to {next_coords}')
            continue
        game_view.remove_tile_override(rolling_boulder.coords)
        if rolling_boulder.shadowed_tile_override:  # Restoring previous tile override:
            game_view.add_tile_override(rolling_boulder.shadowed_tile_override, coords=rolling_boulder.coords)
        rolling_boulder = rolling_boulder._replace(coords=next_coords,
                                                   shadowed_tile_override=game_view.tile_override(next_coords))
        next_rolling_boulders += (rolling_boulder,)
        if rolling_boulder.shadowed_tile_override:  # Removing previous tile override:
            game_view.remove_tile_override(next_coords)
        boulder_tile_id = _get_boulder_tile_id(next_coords)
        game_view.add_tile_override(boulder_tile_id, coords=next_coords)
        if game_view.state.coords == next_coords:
            game_view.state = game_view.state._replace(hp=0, message='The boulder crushed you', milestone=GameMilestone.GAME_OVER)
            return
    game_view.state = game_view.state._replace(rolling_boulders=next_rolling_boulders)


def _get_boulder_tile_id(coords):
    'Return 20, 21, 22, or 64 depending on the base tile at coords'
    map_id, x, y = coords
    _map = atlas().maps[map_id]
    content = _map.tiles[y][x]
    return {
        1: 20,  # dungeon_floor -> boulder_floor
        5: 21,  # dungeon_ceiling -> boulder_ceiling
        6: 22,  # grass -> boulder_grass
        8: 21,  # chest_interior -> boulder_ceiling
        9: 20,  # chest_exterior -> boulder_floor
        16: 21, # bone_pile -> boulder_ceiling
        63: 64, # dungeon_boulder_hole -> boulder_hole_boulder
    }[content]


def mapscript_add_trigger(trigger_pos, func, condition=None, facing=None, permanent=False):
    def _mapscript_activate_trigger(game_view, _GameView):
        gs = game_view.state
        if trigger_pos in gs.triggers_activated or (condition and not condition(gs)) or (facing and gs.facing != facing):
            return
        if not permanent:
            game_view.state = game_view.state.with_trigger_activated(trigger_pos)
        log(gs, f'+trigger @ {trigger_pos}')
        actions_count = len(game_view.actions)
        func(game_view, _GameView)  # passing _GameView to allow populating .actions
        assert len(game_view.actions) == actions_count or permanent, f'Trigger @ {trigger_pos} add actions: it must be permanent!'
    SCRIPTS_PER_TILE[trigger_pos] = ('trigger', _mapscript_activate_trigger)


def mapscript_remove_all():
    global SCRIPTS_PER_TILE
    SCRIPTS_PER_TILE = {}


SCRIPTS_PER_TILE = {  # key = (map_id, x, y) - Those are the initial items from mapscript.js:
    (2, 1, 1):   ('chest', lambda gv, _GameView: _mapscript_open_chest(gv, _GameView, 10)),
    (3, 2, 1):   ('chest', lambda gv, _GameView: _mapscript_open_chest(gv, _GameView, 11)),
    (4, 2, 2):   ('chest', lambda gv, _GameView: _mapscript_open_chest(gv, _GameView, 13)),
    (5, 7, 10):  ('chest', lambda gv, _GameView: _mapscript_open_chest(gv, _GameView, 'gold_10')),
    (6, 9, 4):   ('chest', lambda gv, _GameView: _mapscript_open_chest(gv, _GameView, 12)),
    (7, 13, 5):  ('chest', lambda gv, _GameView: _mapscript_open_chest(gv, _GameView, 15)),
    (8, 3, 2):   ('chest', lambda gv, _GameView: _mapscript_open_chest(gv, _GameView, 14)),
    (8, 3, 12):  ('chest', lambda gv, _GameView: _mapscript_open_chest(gv, _GameView, 12)),
    (8, 6, 9):   ('chest', lambda gv, _GameView: _mapscript_open_chest(gv, _GameView, 'gold_25')),
    (10, 11, 2): ('chest', lambda gv, _GameView: _mapscript_open_chest(gv, _GameView, 13)),
    (10, 13, 2): ('chest', lambda gv, _GameView: _mapscript_open_chest(gv, _GameView, 'gold_100')),
}


def _mapscript_grant_chest_10(game_view, _):
    game_view.state = game_view.state._replace(message="Wood Stick")
    if game_view.state.weapon == 0:
        game_view.state = game_view.state._replace(weapon=1)


def _mapscript_grant_chest_11(game_view, _):
    game_view.state = game_view.state._replace(message="Spellbook: Heal")
    if game_view.state.spellbook == 0:
        game_view.state = game_view.state._replace(spellbook=1)


def _mapscript_grant_chest_12(game_view, _):
    game_view.state = game_view.state._replace(message="Magic Sapphire (MP Up)",
                                               mp=game_view.state.mp + 2,
                                               max_mp=game_view.state.max_mp + 2)


def _mapscript_grant_chest_13(game_view, _):
    game_view.state = game_view.state._replace(message="Magic Emerald (HP Up)",
                                               hp=game_view.state.hp + 5,
                                               max_hp=game_view.state.max_hp + 5)


def _mapscript_grant_chest_14(game_view, _):
    game_view.state = game_view.state._replace(message="Magic Ruby (Atk Up)",
                                               bonus_atk=game_view.state.bonus_atk + 1)


def _mapscript_grant_chest_15(game_view, _):
    game_view.state = game_view.state._replace(message="Magic Diamond (Def Up)",
                                               bonus_def=game_view.state.bonus_def + 1)
