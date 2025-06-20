from .js import atlas
from .mapscript import mapscript_tile_script_type
from .mazemap import mazemap_is_exit, mazemap_is_shop
from .optional_deps import ansi_wrap


def map_as_string(game_view):
    rows = []
    _map = atlas().maps[game_view.state.map_id]
    print(_map.name + ":")
    for y, row in enumerate(_map.tiles):
        rows.append(''.join(_tile_as_char(game_view, _map, x, y, content)
                            for x, content in enumerate(row)))
    return '\n'.join(rows)


def _tile_as_char(game_view, _map, x, y, content):
    game_state = game_view.state
    if (x, y) == game_state.coords[1:]:
        return ansi_wrap({
            'south': 'v ',
            'west': '< ',
            'north': '^ ',
            'east': '> ',
        }[game_state.facing], color='blue')
    script_type = mapscript_tile_script_type(game_state.map_id, x, y)
    if script_type == 'message':
        return ansi_wrap('MM', color='green')
    tile_override = game_view.tile_override((game_state.map_id, x, y))
    tile_id = tile_override or content
    out_chars = _TILE_AS_EMOJI[tile_id]
    if script_type == 'enemy' and not game_view.enemy_vanquished((game_state.map_id, x, y)):
        chars = 'EE'
        if tile_id in (8, 9): chars = 'CE'  # chest monster
        if tile_id in (33, 36): chars = 'BE'  # box monster
        if tile_id == 3: chars = 'DE'  # door monster
        return ansi_wrap(chars, color='red')
    if script_type == 'chest' and not tile_override:
        return ansi_wrap(out_chars if out_chars != '  ' else '$$', color='yellow')
    if script_type and 'trigger' in script_type:
        return ansi_wrap(out_chars if out_chars != '  ' else 'TT', color='green')
    if mazemap_is_exit(_map, x, y) or mazemap_is_shop(_map, x, y):
        return ansi_wrap(out_chars if out_chars != '  ' else '<>', color='magenta')
    return out_chars


_TILE_AS_EMOJI = [
    '⬜',                                       #  0: no tile
    '  ',                                      #  1: dungeon_floor
    'XX',                                      #  2: dungeon_wall
    'DD',                                      #  3: dungeon_door
    'II',                                      #  4: pillar_exterior
    '  ',                                      #  5: dungeon_ceiling
    '  ',                                      #  6: grass
    'II',                                      #  7: pillar_interior
    'CC',                                      #  8: chest_interior
    'CC',                                      #  9: chest_exterior
    'XX',                                      # 10: medieval_house
    'DD',                                      # 11: medieval_door
    'AA',                                      # 12: tree_evergreen
    'GC',                                      # 13: grave_cross
    'GS',                                      # 14: grave_stone
    '~~',                                      # 15: water
    ansi_wrap('oo', color='magenta'),          # 16: skull_pile
    '##',                                      # 17: hay_pile
    'Dx',                                      # 18: locked_door
    ansi_wrap('DS', color='red'),              # 19: death_speaker
    # New tiles:
    ansi_wrap('OO', color='cyan'),             # 20: boulder_floor
    ansi_wrap('OO', color='cyan'),             # 21: boulder_ceiling
    ansi_wrap('OO', color='cyan'),             # 22: boulder_grass
    ansi_wrap('SS', color='green'),            # 23: sign
    ansi_wrap('FF', color='yellow'),           # 24: fountain
    'HH',                                      # 25: portcullis_exterior
    'HH',                                      # 26: portcullis_interior
    '@@',                                      # 27: portal_interior
    '@x',                                      # 28: portal_interior_closed
    ansi_wrap('AA', bold=True),                # 29: dead_tree
    ansi_wrap('XX', bold=True),                # 30: dungeon_wall_tagged
    'WW',                                      # 31: well
    ansi_wrap('WT', color='yellow'),           # 32: dungeon_wall_torch
    ansi_wrap('WB', color='green'),            # 33: box_interior
    'BK',                                      # 34: dungeon_wall_bookshelf
    ansi_wrap('BT', color='yellow'),           # 35: dungeon_wall_bookshelf_torch
    ansi_wrap('WB', color='green'),            # 36: box_exterior
    '##',                                      # 37: hay_pile_exterior
    'ST',                                      # 38: statue
    ansi_wrap('SA', color='yellow'),           # 39: statue_with_amulet
    ansi_wrap('FF', color='yellow'),           # 40: fire
    ansi_wrap('XW', color='green'),            # 41: dungeon_wall_small_window
    'AS',                                      # 42: stump
    ansi_wrap('AS', color='yellow'),           # 43: stump_with_bottle
    ansi_wrap('SE', color='magenta'),          # 44: seamus_on_grass
    ansi_wrap('SE', color='magenta'),          # 45: seamus_on_floor
    ansi_wrap('CF', color='yellow'),           # 46: cauldron
    ansi_wrap('XX', bold=True),                # 47: dungeon_wall_with_ivy
    ansi_wrap('WL', bold=True),                # 48: dungeon_wall_lever_slot
    ansi_wrap('WL', bold=True),                # 49: dungeon_wall_lever_down
    ansi_wrap('WL', bold=True),                # 50: dungeon_wall_lever_up
    ansi_wrap('WL', bold=True),                # 51: dungeon_wall_lever_up_with_fish
    ansi_wrap('DD', bold=True),                # 52: dungeon_black_passage
    ansi_wrap('GE', color='cyan', bold=True),  # 53: petrified_gorgon_with_staff
    ansi_wrap('GE', color='cyan'),             # 54: petrified_gorgon
    ansi_wrap('AA', color='yellow'),           # 55: tree_alt
    'Gs',                                      # 56: grave_stone_shield
    '++',                                      # 57: grass_konami
    '()',                                      # 58: dungeon_mirror
    'G+',                                      # 59: grave_stone_cross
    'GP',                                      # 60: grave_stone_pentacle
    'GR',                                      # 61: grave_stone_rip
    'GW',                                      # 62: grave_stone_writing
    '  ',                                      # 63: dungeon_boulder_hole
    ansi_wrap('OO', color='cyan'),             # 64: boulder_hole_boulder
    'Dx',                                      # 65: medieval_locked_door
]
