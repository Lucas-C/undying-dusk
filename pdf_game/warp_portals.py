from collections import defaultdict

from .entities import TileEdge, WarpPortal
from .mazemap import DX_DY_PER_FACING_AND_RENDER_POS


WARP_PORTALS_PER_MAP = defaultdict(list)


def warp_portal_teleport(prev_coords, new_pos):
    map_id, prev_pos = prev_coords[0], prev_coords[1:]
    map_warp_portals = WARP_PORTALS_PER_MAP[map_id]
    if not map_warp_portals:
        return new_pos
    crossed_edge = TileEdge.from_positions(prev_pos, new_pos)
    for warp_portal in map_warp_portals:
        if warp_portal.has_edge(crossed_edge):
            return warp_portal.translate(crossed_edge, *new_pos)
    return new_pos


def warp_portal_add(map_id, pos1, facing1, pos2, facing2):
    """
    A warp is a portal, a tile side that communicates with another tile side somewhere else:
    +--+--+--+    +--+--+--+
    |  |XX|XX|    |XX|XX|  |
    +--+--+--+    +--+--+--+
    |  |  ]XX| -> |XX|XX[  |
    +--+--+--+    +--+--+--+
    |  |XX|XX|    |XX|XX|  |
    +--+--+--+    +--+--+--+

    Warp portals are internal to a single map.
    Warp portals are always "two-ways".
    """
    edge1 = TileEdge.new(pos1, facing1)
    edge2 = TileEdge.new(pos2, facing2)
    assert edge1.facing == edge2.facing, 'Orthogonal warp portals are not supported!'
    WARP_PORTALS_PER_MAP[map_id].append(WarpPortal.new(edge1, edge2))


def warp_portal_in_sight(map_id, pos, facing, render_pos=4):
    "Return a single WarpPortal, if there is any of its edges in sight."
    for edge in _edges_in_sight(pos, facing, render_pos):
        for warp_portal in WARP_PORTALS_PER_MAP[map_id]:
            if warp_portal.has_edge(edge):
                return warp_portal, edge
    return None


def _edges_in_sight(pos, facing, render_pos):
    x, y = pos
    dx_dy_per_render_pos = DX_DY_PER_FACING_AND_RENDER_POS[facing]
    for render_pos1, render_pos2 in _RENDER_POS_EDGES_IN_SIGHT[render_pos]:
        dx1, dy1 = dx_dy_per_render_pos[render_pos1]
        dx2, dy2 = dx_dy_per_render_pos[render_pos2]
        pos1 = (x + dx1, y + dy1)
        pos2 = (x + dx2, y + dy2)
        yield TileEdge.from_positions(pos1, pos2)


# "render_pos" that consitute the field of view (from mazemap.js):
# +--+--+--+--+--+
# | 0| 2| 4| 3| 1|
# +--+--+--+--+--+
# | 5| 7| 9| 8| 6|
# +--+--+--+--+--+
# |  | a| c| b|  |
# +--+--+--+--+--+
# ("c=12" is the current position)
_RENDER_POS_EDGES_IN_SIGHT = (
    (( 0,  2), ( 0,  5), ( 2,  7), ( 7, 10), ( 9, 12), (10, 12),         ), # render_pos=0
    (( 1,  3), ( 1,  6), ( 3,  8), ( 8, 11), ( 9, 12), (11, 12),         ), # render_pos=1
    (( 2,  4), ( 2,  7), ( 4,  9), ( 7,  9), ( 7, 10), ( 9, 12), (10, 12)), # render_pos=2
    (( 3,  4), ( 3,  8), ( 4,  9), ( 8,  9), ( 8, 11), ( 9, 12), (11, 12)), # render_pos=3
    (( 4,  9), ( 9, 12),                                                 ), # render_pos=4
    (( 5,  7), ( 7, 10), (10, 12),                                       ), # render_pos=5
    (( 6,  8), ( 8, 11), (11, 12),                                       ), # render_pos=6
    (( 7,  9), ( 7, 10), ( 9, 12), (10, 12),                             ), # render_pos=7
    (( 8,  9), ( 8, 11), ( 9, 12), (11, 12),                             ), # render_pos=8
    (( 9, 12),                                                           ), # render_pos=9
    (( 10, 12),                                                          ), # render_pos=10
    (( 11, 12),                                                          ), # render_pos=11
    (                                                                    ), # render_pos=12
)


def warp_portal_remove_all():
    global WARP_PORTALS_PER_MAP
    WARP_PORTALS_PER_MAP = defaultdict(list)
