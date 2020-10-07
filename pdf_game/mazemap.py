from .js import atlas, tileset
from .mod.world import custom_can_move_to


FORWARD_TILE_POS_PER_FACING = {  # replicates avatar.js:avatar_explore (dx, dy) table:
    'north': (0, -1),
    'west': (-1, 0),
    'south': (0, 1),
    'east': (1, 0),
}
FORWARD_RIGHT_TILE_POS_PER_FACING = {
    'north': (1, -1),
    'west': (-1, -1),
    'south': (-1, 1),
    'east': (1, 1),
}
FORWARD_LEFT_TILE_POS_PER_FACING = {
    'north': (-1, -1),
    'west': (-1, 1),
    'south': (1, 1),
    'east': (1, -1),
}
RIGHT_TILE_POS_PER_FACING = {
    'north': (1, 0),
    'west': (0, -1),
    'south': (-1, 0),
    'east': (0, 1),
}
LEFT_TILE_POS_PER_FACING = {
    'north': (-1, 0),
    'west': (0, 1),
    'south': (1, 0),
    'east': (0, -1),
}


def mazemap_is_exit(_map, x, y):
    for _exit in _map.exits:
        if _exit.exit_x == x and _exit.exit_y == y:
            return _exit
    return False


def mazemap_is_shop(_map, x, y):
    for shop in _map.shops:
        if shop.exit_x == x and shop.exit_y == y:
            return shop
    return False


def mazemap_get_tile(game_view, map_id=None, x=None, y=None):
    if map_id is None:
        map_id = game_view.state.map_id
    if x is None and y is None:
        x, y = game_view.state.coords[1:]
    _map = atlas().maps[map_id]
    if not mazemap_bounds_check(_map, x, y):
        return None
    tile_override = game_view.tile_override((map_id, x, y))
    return tile_override or _map.tiles[y][x]


def mazemap_next_pos_facing(x, y, facing, speed=1, render_pos=4):
    assert render_pos in (7, 2, 4, 3, 8)
    if render_pos == 4:
        fwd_dx, fwd_dy = FORWARD_TILE_POS_PER_FACING[facing]
    elif render_pos == 3:
        fwd_dx, fwd_dy = FORWARD_RIGHT_TILE_POS_PER_FACING[facing]
    elif render_pos == 2:
        fwd_dx, fwd_dy = FORWARD_LEFT_TILE_POS_PER_FACING[facing]
    elif render_pos == 8:
        fwd_dx, fwd_dy = RIGHT_TILE_POS_PER_FACING[facing]
    elif render_pos == 7:
        fwd_dx, fwd_dy = LEFT_TILE_POS_PER_FACING[facing]
    return x + speed*fwd_dx, y + speed*fwd_dy


def avatar_can_move_to(game_view, map_id, x, y):
    # replicates avatar.js:avatar_move logic:
    _map = atlas().maps[map_id]
    if not mazemap_bounds_check(_map, x, y):
        return False
    can_move = custom_can_move_to(_map, x, y, game_view.state)
    if can_move is not None:
        return can_move
    tile_id = mazemap_get_tile(game_view, map_id, x, y)
    return tileset().walkable[tile_id]


def mazemap_bounds_check(_map, x, y):
    return 0 <= y < len(_map.tiles) and 0 <= x < len(_map.tiles[0])
