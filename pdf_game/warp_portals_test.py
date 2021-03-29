from random import choice, randrange

import pytest

from .entities import TileEdge
from .mazemap import mazemap_next_pos_facing
from .warp_portals import warp_portal_add, warp_portal_in_sight, warp_portal_remove_all


@pytest.mark.parametrize('_', range(10))  # repeat test several times
def test_tile_edge(_):
    pos1 = (randrange(10), randrange(10))
    facing = choice(('north', 'west', 'south', 'east'))

    edge = TileEdge.new(pos1, facing)
    pos2 = mazemap_next_pos_facing(*pos1, facing)
    assert edge == TileEdge.from_positions(pos1, pos2)


def test_warp_portal_in_sight1():
    warp_portal_add(map_id=0, pos1=(2, 2), facing1='north', pos2=(2, 12), facing2='south')
    assert warp_portal_in_sight(map_id=0, pos=(2, 2), facing='north', render_pos=4)

def test_warp_portal_in_sight2():
    warp_portal_add(0, (2, 1), 'north', (5, 7), 'north')
    x, y = (2, 1)
    portal_in_sight = warp_portal_in_sight(0, (x, y), 'east', 7)
    assert portal_in_sight
    warp_portal, edge = portal_in_sight
    assert edge == TileEdge.new((2, 0), 'south')
    assert warp_portal.translate(edge, x, y) == (5, 7)


def teardown_method():
    warp_portal_remove_all()
