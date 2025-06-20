from . import Proxy
from .scenes import patch_map_shops


WALKABLE_BONES_AND_BOXES = False  # for --no-script mode
MAUSOLEUM_PORTAL_COORDS = (8, 2, 12)
MAUSOLEUM_EXIT_COORDS = (8, 15, 7)
BOX_MIMIC_POS = (8, 3, 2)
DOOR_MIMIC_POS = (8, 5, 2)
VILLAGE_PORTAL_COORDS = (5, 9, 3)
VILLAGE_INN_COORDS = (5, 8, 8)
CLICK_ZONES = {
    'OPEN_DOOR':            {'x': 62, 'y': 43, 'width': 35, 'height': 54},
    'PASS_BEHIND_IVY':      {'x': 54, 'y': 36, 'width': 49, 'height': 58},
    'PASS_PORTAL':          {'x': 50, 'y': 26, 'width': 60, 'height': 61},
    'RAISE_LEVER':          {'x': 67, 'y': 43, 'width': 21, 'height': 49},
    'PICK_FISH_ON_A_STICK': {'x': 50, 'y': 32, 'width': 38, 'height': 47},
    'PICK_STAFF':           {'x': 43, 'y': 18, 'width': 15, 'height': 79},
    'REFLECT_GORGON':       {'x': 15, 'y': 17, 'width': 46, 'height': 72},
    'TURN_LEVER_0':         {'x': 76, 'y': 25, 'width': 10, 'height': 16},
    'TURN_LEVER_1':         {'x': 98, 'y': 42, 'width': 11, 'height': 15},
    'TURN_LEVER_2':         {'x': 108,'y': 64, 'width': 10, 'height': 15},
    'TURN_LEVER_3':         {'x': 95, 'y': 83, 'width': 12, 'height': 15},
    'TURN_LEVER_4':         {'x': 74, 'y': 83, 'width': 11, 'height': 15},
    'TURN_LEVER_5':         {'x': 56, 'y': 83, 'width': 9,  'height': 15},
    'TURN_LEVER_6':         {'x': 41, 'y': 64, 'width': 15, 'height': 16},
    'TURN_LEVER_7':         {'x': 52, 'y': 42, 'width': 10, 'height': 16},
    'TAKE_MIRROR':          {'x': 68, 'y': 19, 'width': 23, 'height': 40},
}


def custom_can_burn(game_state):
    # We forbid box burning in Mausoleum, where there is a box mimic:
    return game_state.map_id != 8


def custom_can_push(game_state, actions):
    # pylint: disable=import-outside-toplevel
    from ..mazemap import mazemap_next_pos_facing
    next_pos_facing = mazemap_next_pos_facing(*game_state.coords[1:], game_state.facing)
    if (game_state.map_id, *next_pos_facing) == BOX_MIMIC_POS:
        # Facing box mimic in Mausoleum: if the player tries to push it, it triggers a fight!
        return 'PUSH', actions['MOVE-FORWARD']
    return None


def custom_can_move_to(_map, x, y, game_state):
    'Allow to override the default tile walkability on specific coordinates'
    if WALKABLE_BONES_AND_BOXES and _map.tiles[y][x] in (16, 33, 36):  # skull pile or interior/exterior box
        return True
    if _map.name == 'Monastery Trail':
        if (x, y) == (6, 1):
            return False  # removing exit to Monastery
    if _map.name == 'Cedar Village':
        if (x, y) == VILLAGE_PORTAL_COORDS[1:]:
            return game_state.tile_override_at(VILLAGE_PORTAL_COORDS) and not is_instinct_preventing_to_pass_village_portal(game_state)
        if (x, y) == (9, 11):  # south exit
            assert not game_state.tile_override_at(VILLAGE_PORTAL_COORDS), f'No going back to Zuruth Plains once portal is open!\n{game_state}'
        if (x, y) == (6, 6) and 'BOOTS' in game_state.items: # fountain
            return True
    if _map.name == 'Zuruth Plains':
        if (x, y) == (3, 15):
            return True  # dungeon_wall_with_ivy
        if (x, y) == (13, 14) and 'BOOTS' in game_state.items:
            return True  # can enter shallow waters to access the chest
        if (x, y) == (4, 2):
            return not is_instinct_preventing_to_enter_village(game_state)
    if _map.name == 'Canal Boneyard':
        if (x, y) == (3, 2) and 'BOOTS' in game_state.items:
            return True  # can enter shallow waters to access the hint sign
        if (x, y) == (11, 5):
            return False  # forbid to move behind exit to Mausoleum
    if _map.name == 'Mausoleum':
        if (x, y) == (0, 7):
            return False  # forbid to move behind exit to Canal Boneyard
        if _map.tiles[y][x] == 15 and 'BOOTS' in game_state.items:
            return True  # can walk on shallow waters
        if (x, y) == MAUSOLEUM_PORTAL_COORDS[1:]:
            return game_state.tile_override_at(MAUSOLEUM_PORTAL_COORDS) and not is_instinct_preventing_to_pass_mausoleum_portal(game_state)
        if (x, y) == BOX_MIMIC_POS[1:]:  # allow to move on box mimic tile:
            return True
        if (x, y) == (4, 2):  # behind door mimic, not walkable until beaten
            return DOOR_MIMIC_POS in game_state.vanquished_enemies
    return None


def is_instinct_preventing_to_enter_village(game_state):
    # Cedar Village must be accessed from Zuruth Plains 3 times:
    # - when avatar has 2 MP and the scroll, to go see Sage Therel
    # - when avatar has 20 gold, to buy the boots
    # - when avatar has 60 gold, to repair the sword & get a night of rest
    return (game_state.mp < 2 or 'SCROLL' not in game_state.items) and game_state.gold < 10


def is_instinct_preventing_to_pass_mausoleum_portal(game_state):
    # We forbid to get back to village if the heroine has the UNLOCK spell,
    # but hasn't collected all the armor parts yet, or hasn't solved the rotating lever puzzle:
    gs = game_state
    return gs.spellbook == 3 and (gs.items.count('ARMOR_PART') < 4 or not gs.tile_override_at(MAUSOLEUM_EXIT_COORDS))


def is_instinct_preventing_to_pass_village_portal(game_state):
    if not game_state.tile_override_at(VILLAGE_PORTAL_COORDS):
        return False  # No need to display a message when the portal is not open yet
    # We forbid to get back to Mausoleum if the heroine hasn't picked the UNLOCK spell yet,
    # hasn't taken a night of rest at the inn, or hasn't picked up the staff on the petrified gorgon yet:
    has_staff_been_picked_up = 'STAFF' in game_state.items or game_state.tile_override_at(MAUSOLEUM_EXIT_COORDS)
    return game_state.spellbook < 3 or game_state.gold >= 10 or not has_staff_been_picked_up


def patch_tileset(tileset):
    # Defining new tiles "walkablity":
    return Proxy(draw_area=tileset.draw_area, walkable=list(tileset.walkable) + [
                #  0 = void
                #  1 = dungeon_floor
                #  2 = dungeon_wall
                #  3 = dungeon_door
                #  4 = pillar_exterior
                #  5 = dungeon_ceiling
                #  6 = grass
                #  7 = pillar_interior
                #  8 = chest_interior
                #  9 = chest_exterior
                # 10 = medieval_house
                # 11 = medieval_door
                # 12 = tree_evergreen
                # 13 = grave_cross
                # 14 = grave_stone
                # 15 = water
                # 16 = skull_pile
                # 17 = hay_pile
                # 18 = locked_door
                # 19 = death_speaker
        False,  # 20 = boulder_floor
        False,  # 21 = boulder_ceiling
        False,  # 22 = boulder_grass
        True,   # 23 = sign_grass
        False,  # 24 = fountain
        False,  # 25 = portcullis_exterior
        False,  # 26 = portcullis_interior
        True,   # 27 = portal_interior
        False,  # 28 = portal_interior_closed
        False,  # 29 = dead_tree
        False,  # 30 = dungeon_wall_tagged
        False,  # 31 = well
        False,  # 32 = dungeon_wall_torch
        False,  # 33 = box_interior
        False,  # 34 = dungeon_wall_bookshelf
        False,  # 35 = dungeon_wall_bookshelf_torch
        False,  # 36 = box_exterior
        True,   # 37 = hay_pile_exterior
        False,  # 38 = statue
        False,  # 39 = statue_with_amulet
        True,   # 40 = fire
        False,  # 41 = dungeon_wall_small_window
        True,   # 42 = stump
        True,   # 43 = stump_with_bottle
        True,   # 44 = seamus_on_grass
        True,   # 45 = seamus_on_floor
        True,   # 46 = cauldron
        False,  # 47 = dungeon_wall_with_ivy
        False,  # 48 = dungeon_wall_lever_slot
        False,  # 49 = dungeon_wall_lever_down
        False,  # 50 = dungeon_wall_lever_up
        False,  # 51 = dungeon_wall_lever_up_with_fish
        True,   # 52 = dungeon_black_passage
        False,  # 53 = petrified_gorgon_with_staff
        False,  # 54 = petrified_gorgon
        True,   # 55 = tree_alt
        False,  # 56 = grave_stone_shield
        True,   # 57 = grass_konami
        False,  # 58 = dungeon_mirror
        False,  # 59 = grave_stone_cross
        False,  # 60 = grave_stone_pentacle
        False,  # 61 = grave_stone_rip
        False,  # 62 = grave_stone_writing
        True,   # 63 = dungeon_boulder_hole
        False,  # 64 = boulder_hole_boulder
        False,  # 65 = medieval_locked_door
    ])


def patch_atlas(atlas):
    maps = [Proxy(name=_patch_map_name(_map.name),
                  background=_map.background,
                  tiles=_patch_tiles(_map),
                  exits=_patch_exits(_map),
                  shops=patch_map_shops(_map)) for _map in atlas.maps]
    return Proxy(maps=maps)


def _patch_map_name(name):
    if name == 'Serf Quarters':
        return 'Your cell'
    if name == 'Monk Quarters':
        return 'Scriptorium'
    if name == 'Meditation Point':
        return 'Library'
    if name == 'Trade Tunnel':
        return 'Templar Academy'
    return name


def _patch_tiles(_map):
    tiles = [list(row) for row in _map.tiles]
    # if _map.name == 'Serf Quarters':  tiles[3][1] = 34  # test bookshelf
    # if _map.name == 'Serf Quarters':  tiles[3][1] = 48  # test staff-in-lever
    # if _map.name == 'Serf Quarters':  # portals test map (_patch_exits() must also return [])
    #     return [
    #         [2, 2, 2, 2, 2, 2, 2, 2],
    #         [2, 2, 5, 2, 2, 5, 2, 2],
    #         [2, 5, 5, 5, 5, 5, 5, 2],
    #         [2, 5, 6, 6, 6, 6, 5, 2],
    #         [5, 5, 6, 6, 6, 6, 5, 2],
    #         [2, 5, 6, 6, 6, 6, 5, 2],
    #         [2, 5, 5, 5, 5, 5, 5, 2],
    #         [2, 2, 2, 2, 2, 2, 2, 2],
    #     ]
    # if _map.name == 'Serf Quarters':  # levers test map (_patch_exits() must also return [])
    #     return [
    #         [2,  2,  2, 48,  2,  2,  2],
    #         [2,  1,  1, 48,  1,  1,  2],
    #         [2,  1,  1,  1,  1,  1,  2],
    #         [49,49,  1,  1,  1, 50, 50],
    #         [2,  1,  1,  1,  1,  1,  2],
    #         [2,  1,  1, 51,  1,  1,  2],
    #         [2,  2,  2, 51,  2,  2,  2],
    #     ]
    if _map.name == 'Monk Quarters':  # new map: Scriptorium
        return [  # This is meant as a simple enigma & tutorial map
          [ 2, 2, 2,32, 2],
          [ 2, 5,33, 5, 2],
          [ 3, 5,33, 5, 3],
          [ 2, 5,33, 5, 2],
          [ 2,32, 2,41, 2],
        ]
    if _map.name == 'Meditation Point':  # renamed: Library
        return [
          [ 0, 0, 0, 0, 0],
          [ 0,34,34,34, 0],
          [34, 5, 5, 5,34],
          [34, 5, 5, 5,34],
          [ 2, 7, 5, 7, 2],
          [ 2, 2, 3, 2, 2]
        ]
    if _map.name == "Gar'ashi Monastery":
        x, y = 1, 5;   tiles[y][x] = 6   # grass
        x, y = 1, 6;   tiles[y][x] = 31  # well
        x, y = 1, 7;   tiles[y][x] = 6   # grass
    if _map.name == 'Monastery Trail':
        x, y = 6, 1;   tiles[y][x] = 18  # locked door back to monastery
        x, y = 2, 2;   tiles[y][x] = 31  # well
        x, y = 11, 7;  tiles[y][x] = 55  # secret passage through the trees
        x, y = 11, 8;  tiles[y][x] = 55  # secret passage through the trees
        x, y = 11, 9;  tiles[y][x] = 43  # adding stump hidden in the forest
        # x, y = 12, 14; tiles[y][x] = 6   # grass (added to get another whispering wind) (no longer needed, right?)
        x, y = 10,15;  tiles[y][x] = 18  # initially lock the door so the unlock spell functions after getting the tree secret
    if _map.name == 'Cedar Village':
        x, y = 1, 10;  tiles[y][x] = 6   # allowing space for the boulder so that it does not block the passage
        x, y = 2, 3;   tiles[y][x] = 23  # adding a sign
        x, y = 6, 6;   tiles[y][x] = 24  # placing foutain
    if _map.name == 'Zuruth Plains':
        x, y = 1, 9;   tiles[y][x] = 44  # Seamus hidden among the trees on the west
        x, y = 9, 4;   tiles[y][x] = 38  # replacing chest by statue
        x, y = 7, 15;  tiles[y][x] = 32  # torch on left side of door to Templar Academy
        x, y = 9, 15;  tiles[y][x] = 32  # torch on right side of door to Templar Academy
        x, y = 14, 15; tiles[y][x] = 3   # locked door aside chest on south-east
        x, y = 3, 15;  tiles[y][x] = 47  # dungeon_wall_with_ivy
        x, y = 15, 7;  tiles[y][x] = 25  # portcullis.  immediately raised
        # Adding an extra line of dungeon_wall at the bottom of the map, for hidden scroll:
        tiles.append([2]*len(tiles[0]))
    if _map.name == 'Trade Tunnel':
        return [  # Massive redesign of the east (right) side to replace locked doors, chests & shops with a maze:
          [ 2, 2, 3, 2, 2, 2,32, 2, 2, 2, 2, 2, 2, 2, 2, 2],
          [34, 5, 5, 5, 2, 5, 5, 5, 2, 5, 5, 5, 5, 2, 5, 2],
          [32, 5, 5, 5,16, 5,15, 5, 2, 5, 2, 2, 5, 2, 5, 2],
          [34, 5, 5, 5, 2, 5,15, 5, 2, 8, 2, 2, 5, 2, 5, 2],
          [ 2, 2,16, 2, 2, 5,15, 5,18 ,2, 5, 5, 5, 2, 5, 2],
          [34, 5, 5, 5, 2, 5,15, 5, 2, 5, 5, 2, 5, 2, 5, 2],
          [32, 5, 5, 5,32, 5, 1, 5, 2, 5, 2, 5, 5, 2, 5, 2],
          [34, 5, 5, 5, 2, 5,15, 5, 2, 5, 2, 2, 2, 2, 5, 2],
          [ 2, 7, 5, 7, 2, 5,15, 5, 2, 5, 2, 5, 5, 2, 5, 2],
          [34, 5, 5, 5, 2, 5,15, 5, 2, 5, 5, 5, 2, 2, 5, 2],
          [32, 5, 5, 5,32, 5, 1, 5, 2, 5, 2, 5, 5, 5, 5, 2],
          [34, 5, 5, 5, 2, 5,15, 5, 2, 2, 2, 2, 2, 3, 2, 2],
          [ 2, 2, 5, 2, 2, 5,15, 5, 5, 5, 5, 5, 5, 5, 5, 2],
          [34, 8,63,35, 2, 5,15,15, 1,15,15, 1,15,15, 5,32],
          [34, 5, 5,34, 2, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 2],
          [ 2,34,34, 2, 2, 2, 2, 2,32, 2, 2,32, 2, 2, 2, 2],
        ]
    if _map.name == 'Canal Boneyard':
        x, y = 1, 5;   tiles[y][x] = 25  # portcullis blocking the way back
        x, y = 4, 2;   tiles[y][x] = 6   # grass instead of grave, so that sign/water can be reached
        x, y = 2, 2;   tiles[y][x] = 23  # sign in the water
        x, y = 4, 9;   tiles[y][x] = 6   # grass instead of tree, so that glimpse can be seen
        x, y = 12, 5;  tiles[y][x] = 47  # dungeon_wall_with_ivy
        x, y = 13, 5;  tiles[y][x] = 46  # chest_interior -> cauldron
        x, y = 14, 4;  tiles[y][x] = 32  # torch on wall, on left side of chest
        x, y = 14, 6;  tiles[y][x] = 32  # torch on wall, on right side of chest
        x, y = 10, 5;  tiles[y][x] = 5   # passage to Mausoleum (used to be a door)
        x, y = 11, 5;  tiles[y][x] = 5   # passage to Mausoleum (used to be a wall)
        x, y = 8,  7;  tiles[y][x] = 56  # Saint Knight's grave (shield)
        x, y = 6,  6;  tiles[y][x] = 59  # grave with cross
        x, y = 8,  2;  tiles[y][x] = 59  # grave with cross
        x, y = 12, 2;  tiles[y][x] = 59  # grave with cross
        x, y = 12, 9;  tiles[y][x] = 59  # grave with cross
        x, y = 8,  4;  tiles[y][x] = 60  # grave with pentacle
        x, y = 11, 1;  tiles[y][x] = 60  # grave with pentacle
        x, y = 10, 8;  tiles[y][x] = 60  # grave with pentacle
        x, y = 6,  3;  tiles[y][x] = 61  # grave with RIP
        x, y = 13, 1;  tiles[y][x] = 61  # grave with RIP
        x, y = 10, 9;  tiles[y][x] = 61  # grave with RIP
        x, y = 6,  8;  tiles[y][x] = 62  # grave with writing
        x, y = 6,  2;  tiles[y][x] = 62  # grave with writing
        x, y = 10, 1;  tiles[y][x] = 62  # grave with writing
        x, y = 13, 8;  tiles[y][x] = 62  # grave with writing


    if _map.name == 'Mausoleum':
        x, y = 0, 7;   tiles[y][x] = 5   # removing entrance door
        x, y = 1, 6;   tiles[y][x] = 2   # side wall on the entrance, for continuity with the Boneyard passage
        x, y = 1, 8;   tiles[y][x] = 2   # side wall on the entrance, for continuity with the Boneyard passage
        x, y = 4, 6;   tiles[y][x] = 7   # pillar in the entrance hall
        x, y = 4, 8;   tiles[y][x] = 7   # pillar in the entrance hall
        x, y = 6, 0;   tiles[y][x] = 32  # torch on wall
        x, y = 11, 0;  tiles[y][x] = 32  # torch on wall
        x, y = 6, 14;  tiles[y][x] = 32  # torch on wall
        x, y = 11, 14; tiles[y][x] = 32  # torch on wall
        x, y = 3, 5;   tiles[y][x] = 5   # opening to the abyss
        x, y = 3, 9;   tiles[y][x] = 32  # torch on wall
        x, y = 3, 11;  tiles[y][x] = 34  # adding bookshelf
        x, y = 3, 12;  tiles[y][x] = 5   # removing chest
        x, y = 3, 13;  tiles[y][x] = 34  # adding bookshelf
        x, y = MAUSOLEUM_PORTAL_COORDS[1:]; tiles[y][x] = 28  # adding portal, closed (south-west)
        x, y = 4, 2;   tiles[y][x] = 5   # removing bone pile
        x, y = 4, 7;   tiles[y][x] = 5   # removing bone pile
        x, y = 13, 7;  tiles[y][x] = 5   # removing bone pile
        x, y = 11, 5;  tiles[y][x] = 5   # removing bone pile
        x, y = 6, 9;   tiles[y][x] = 5   # moving up chest (mimic) in central room...
        x, y = 7, 3;   tiles[y][x] = 8   # ... to block the path north
#        x, y = 7, 4;   tiles[y][x] = 26  # portcullis
#        x, y = 10, 10; tiles[y][x] = 26  # portcullis
        x, y = 3, 2;   tiles[y][x] = 33  # replacing north-west chest by a box (mimic)
        x, y = 4, 2;   tiles[y][x] = 3   # door (mimic) blocking access to north-west alcove
        x, y = 8, 11;  tiles[y][x] = 58  # starting with mirror wall.  will become hay pile in southern corridor alcove, behind water
        x, y = 2, 2;   tiles[y][x] = 34  # bookshelf
        x, y = 3, 1;   tiles[y][x] = 34  # bookshelf
        x, y = 3, 3;   tiles[y][x] = 30  # dungeon_wall_tagged with FOUNTAIN_HINT
        x, y = 7, 11;  tiles[y][x] = 2   # wall after warp south-west in central room
        x, y = 10, 3;  tiles[y][x] = 2   # wall after warp north-east in central room
        x, y = 12, 7;  tiles[y][x] = 48  # replacing straight path to exit by lever slot
        x, y = 12, 6;  tiles[y][x] = 32  # surrounded by torchs on wall
        x, y = 12, 8;  tiles[y][x] = 32  # surrounded by torchs on wall
        x, y = 14, 4;  tiles[y][x] = 34  # bookshelf, north, in east corridor
        x, y = 14, 10; tiles[y][x] = 34  # bookshelf, south, in east corridor
        x, y = 15, 7;  tiles[y][x] = 26  # portcullis blocking exit
    if _map.name == 'Dead Walkways':
        x, y = 1, 5;   tiles[y][x] = 0   # no going back
        x, y = 4, 8;   tiles[y][x] = 4   # pillar, for symmetry
        x, y = 5, 7;   tiles[y][x] = 4   # pillar, for sokoban puzzle
        x, y = 4, 5;   tiles[y][x] = 18  # locked door
        x, y = 5, 4;   tiles[y][x] = 7   # interior pillar
        x, y = 5, 5;   tiles[y][x] = 5   # removing bone pile
        x, y = 5, 6;   tiles[y][x] = 7   # interior pillar
        x, y = 6, 6;   tiles[y][x] = 37  # hay pile, allow to access sokoban but prevent boxes to go up
        x, y = 5, 7;   tiles[y][x] = 36  # box, for sokoban puzzle
        x, y = 6, 7;   tiles[y][x] = 36  # box, for sokoban puzzle
        x, y = 5, 8;   tiles[y][x] = 36  # box, for sokoban puzzle
        x, y = 6, 8;   tiles[y][x] = 36  # box, for sokoban puzzle
        x, y = 4, 9;   tiles[y][x] = 0   # shifting chest...
        x, y = 6, 9;   tiles[y][x] = 9   # ...here 2 tiles on the right
        x, y = 7, 9;   tiles[y][x] = 0   # useless space
        x, y = 8, 9;   tiles[y][x] = 0   # useless space
        x, y = 7, 2;   tiles[y][x] = 18  # locked door
        x, y = 8, 1;   tiles[y][x] = 7   # interior pillar
        x, y = 8, 3;   tiles[y][x] = 7   # interior pillar
        x, y = 8, 2;   tiles[y][x] = 5   # removing bone pile
        x, y = 9, 3;   tiles[y][x] = 45  # seamus
        x, y = 9, 4;   tiles[y][x] = 6   # grass
        x, y = 9, 5;   tiles[y][x] = 6   # grass
        x, y = 9, 6;   tiles[y][x] = 57  # konami hint grass
        x, y = 10,4;   tiles[y][x] = 60  # grave_stone
        x, y = 10,6;   tiles[y][x] = 13  # grave_cross
        x, y = 11,4;   tiles[y][x] = 13  # grave_cross
        x, y = 11,6;   tiles[y][x] = 62  # grave_stone
        x, y = 12,4;   tiles[y][x] = 56  # grave_stone_shield
        x, y = 12,6;   tiles[y][x] = 13  # grave_cross
        x, y = 12,5;   tiles[y][x] = 60  # grave_stone
    return tiles


def _patch_exits(_map):
    # We introduce a "facing" field on every exit, in order to force the avatar orientation when entering a map.
    # This forbid to enter a fight backward with an enemy on a map doorstep, which can allow to bypass it by running away.
    if _map.name == "Serf Quarters":  # ID: 0 - Renamed: "Your cell"
        return [Proxy(exit_x=0, exit_y=2, dest_map=2, dest_x=3, dest_y=2, facing='SAME')]  # to Scriptorium
    if _map.name == "Monk Quarters":  # ID: 2 - Renamed: Scriptorium
        return [
            Proxy(exit_x=4, exit_y=2, dest_map=0, dest_x=1, dest_y=2, facing='SAME'),  # to Serf Quarters
            Proxy(exit_x=0, exit_y=2, dest_map=1, dest_x=6, dest_y=6, facing='SAME'),  # to Gar'ashi Monastery
        ]
    if _map.name == "Gar'ashi Monastery":  # ID: 1
        return [
            Proxy(exit_x=7, exit_y=6, dest_map=2, dest_x=1, dest_y=2, facing='SAME'),  # to Scriptorium
            # _set_exit_facing(map.exits[0], 'east'),  # to Serf Quarters
            # _set_exit_facing(map.exits[1], 'west'),  # to Monk Quarters
            _set_exit_facing(_map.exits[2]),  # to Library (Meditation Point)
            _set_exit_facing(_map.exits[3]),  # to Monastery Trail
        ]
    if _map.name == "Meditation Point":  # ID: 3 - Renamed: Library
        return [_set_exit_facing(_map.exits[0])]
    if _map.name == "Monastery Trail":  # ID: 4
        return [_set_exit_facing(_map.exits[1])]
    if _map.name == "Cedar Village":  # ID: 5
        return [
            _set_exit_facing(_map.exits[0]),  # to Monastery Trail, basically only used when fighting the shadow soul
            _set_exit_facing(_map.exits[1]),  # to Zuruth Plains
            Proxy(exit_x=9, exit_y=3, dest_map=8, dest_x=3, dest_y=12, facing='east'),   # to Mausoleum through portal
        ]
    if _map.name == "Zuruth Plains":  # ID: 6
        return [
            _set_exit_facing(_map.exits[0]),  # to Cedar Village
            # _set_exit_facing(_map.exits[1], 'east'),   # to Canal Boneyard (unused due to "risking_it_all" CutScene)
            _set_exit_facing(_map.exits[2]),  # to Templar Academy
            Proxy(exit_x=14, exit_y=15, dest_map=10, dest_x=7, dest_y=4, facing='west'),  # to Templar Academy through side door
        ]
    if _map.name == "Canal Boneyard":  # ID: 7
        return [
            _set_exit_facing(_map.exits[0]),  # to Zuruth Plains
            _set_exit_facing(_map.exits[1]),  # to Mausoleum, dest_x changed, replaced by next line
        ]
    if _map.name == "Mausoleum":  # ID: 8
        return [
            Proxy(exit_x=1,  exit_y=7, dest_map=7, dest_x=9, dest_y=5, facing='SAME'),   # to Canal Boneyard
            Proxy(exit_x=15, exit_y=7, dest_map=9, dest_x=2, dest_y=5, facing='east'),   # to Dead Walkways, facing forced east due to combat
            Proxy(exit_x=2, exit_y=12, dest_map=5, dest_x=9, dest_y=4, facing='south'),  # to Cedar Village through portal
        ]
    if _map.name == "Dead Walkways":  # ID: 9
        return [
            _set_exit_facing(_map.exits[0]),  # to Mausoleum
        ]
    if _map.name == "Trade Tunnel":  # ID: 10 - Renamed: Templar Academy
        return [
            _set_exit_facing(_map.exits[0]),  # to Zuruth Plains
            Proxy(exit_x=8, exit_y=4, dest_map=6, dest_x=14, dest_y=14, facing='north'),  # to Zuruth Plains through 2nd door
        ]
    raise RuntimeError(f'Exits "facing" not defined yet for map: {_map.name}')

def _set_exit_facing(_exit, facing='SAME'):
    return Proxy(exit_x=_exit.exit_x, exit_y=_exit.exit_y,
                 dest_map=_exit.dest_map, dest_x=_exit.dest_x, dest_y=_exit.dest_y, facing=facing)


def patch_enemy_name(enemy_name):
    if enemy_name == 'death_speaker':
        return 'empress'
    return enemy_name


def make_bones_and_boxes_walkables():
    global WALKABLE_BONES_AND_BOXES
    WALKABLE_BONES_AND_BOXES = True
