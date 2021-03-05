from os import makedirs
from os.path import dirname, exists, join, realpath

from PIL import Image

from .bitfont import bitfont_set_color_red, bitfont_render, Justify
from .entities import GameMilestone, GameMode, Position
from .js import action, atlas, config, enemy, tileset, REL_RELEASE_DIR
from .mapscript import mapscript_get_enemy_at, mapscript_get_warped_coords
from .mazemap import mazemap_bounds_check, mazemap_get_tile, mazemap_next_pos_facing
from .render_minimap import minimap_render
from .perfs import trace_time
from .render_dialog import dialog_render
from .render_info import info_render, info_render_button, info_render_gold, info_render_hpmp
from .render_treasure import treasure_render_collectible, treasure_render_gold, treasure_render_item
from .render_utils import add_link, action_button_render, get_image_info, link_from_page_id, portrait_render, sfx_render, tileset_background_render, white_arrow_render, ACTION_BUTTONS

from .mod.world import patch_enemy_name, CLICK_ZONES


TILES = ',dungeon_floor,dungeon_wall,dungeon_door,pillar_exterior,dungeon_ceiling,grass,pillar_interior,chest_interior,chest_exterior,medieval_house,medieval_door,tree_evergreen,grave_cross,grave_stone,water,skull_pile,hay_pile,locked_door,death_speaker,boulder_floor,boulder_ceiling,boulder_grass,sign_grass,fountain,portcullis_exterior,portcullis_interior,portal_interior,portal_interior_closed,dead_tree,dungeon_wall_tagged,well,dungeon_torch,box_interior,dungeon_bookshelf,dungeon_bookshelf_torch,box_exterior,hay_pile_exterior,statue,statue_with_amulet,fire,dungeon_wall_small_window,stump,stump_with_bottle,seamus_on_grass,seamus_on_floor,cauldron,dungeon_wall_with_ivy,dungeon_wall_lever_slot,dungeon_wall_lever_down,dungeon_wall_lever_up,dungeon_wall_lever_up_with_fish,dungeon_black_passage,petrified_gorgon_with_staff,petrified_gorgon'.split(',')
ARROW_BUTTONS_POS = {
    'TURN-LEFT': Position(x=98, y=8, angle=180),
    'TURN-RIGHT': Position(x=114, y=8, angle=0),
    'MOVE-FORWARD': Position(x=106, y=0, angle=90),
    'MOVE-BACKWARD': Position(x=106, y=16, angle=270),
}
ARROW_LINKS_POS = {
    'TURN-LEFT': Position(x=99, y=10),
    'TURN-RIGHT': Position(x=120, y=10),
    'MOVE-FORWARD': Position(x=108, y=1),
    'MOVE-BACKWARD': Position(x=108, y=22),
}
ARROW_LINK_WIDTH = 12
ARROW_LINK_HEIGHT = 9
MINIATURES_DIR_PATH = join(dirname(realpath(__file__)), '..', 'small_enemies')
MINIATURES_ALREADY_GENERATED = set()


def render_page(pdf, game_view, render_victory):
    game_state = game_view.state
    if game_view.renderer:
        game_view.renderer(pdf)
        return
    bitfont_set_color_red(False)
    pdf.add_page()
    if game_state.milestone == GameMilestone.VICTORY:
        render_victory(pdf, game_state)
        return
    if game_state.mode == GameMode.DIALOG:
        with trace_time('render:0:dialog'):
            dialog_render(pdf, game_view)
        return
    bitfont_set_color_red(game_state.hp <= game_state.max_hp/3)
    with trace_time('render:1:mazemap'):
        mazemap_render(pdf, game_view)
    if game_state.combat:
        with trace_time('render:3:combat'):
            combat_render(pdf, game_state)
    # Combat rendering must be done mefore .message rendering, for bribes messages to display well
    # Same with extra rendering: it must be done before displaying .message, e.g. for gorgon
    if game_state.extra_render:
        game_state.extra_render(pdf)
    if game_state.mode == GameMode.INFO:
        with trace_time('render:2:info_page'):
            minimap_render(pdf, game_view)
            info_render(pdf, game_state)
            action_render(pdf, game_state.spellbook, game_state.items)
            if game_state.message:
                bitfont_render(pdf, game_state.message, 2, 30)
    elif game_state.message and (not game_state.combat or (game_state.combat.enemy.bribes and 'END-COMBAT-AFTER-VICTORY' not in game_view.actions)):  # 2nd condition avoid displaying map name when facing an enemy, e.g. for storm dragon, except for bribe messages
        y = 70 if game_state.msg_place else 100  # only handling UP/DOWN for now
        newlines_count = game_state.message.count('\n')
        if newlines_count > 1:
            y = 50 if game_state.msg_place else 80
            y -= 10*newlines_count
        bitfont_render(pdf, game_state.message, 80, y, Justify.CENTER)
    if game_state.music:
        assert game_state.music_btn_pos, f'No music_btn_pos provided:\n{game_state}'
        action_button_render(pdf, 'MUSIC', url=game_state.music, btn_pos=game_state.music_btn_pos)
    if game_state.treasure_id:  # EXPLORE | COMBAT
        if isinstance(game_state.treasure_id, str):
            gold_str, gold_found = game_state.treasure_id.split('_')
            assert gold_str == 'gold'
            treasure_render_gold(pdf, int(gold_found))
        else:
            treasure_render_item(pdf, game_state.treasure_id)
    elif game_state.sfx:  # only used in EXPLORE mode so far
        sfx_render(pdf, game_state.sfx)
    with trace_time('render:4:actions'):
        for action_name, next_game_view in game_view.actions.items():
            if action_name == 'SHOW-INFO':
                info_render_button(pdf, next_game_view.page_id, down=game_state.mode == GameMode.INFO)
            elif action_name == 'THROW-COIN':
                info_render_gold(pdf, game_state,
                                 page_id=next_game_view.page_id if next_game_view else None)
            elif action_name == 'END-COMBAT-AFTER-VICTORY':
                assert game_state.message, f'No end-combat message: {game_state.combat}'
                bitfont_render(pdf, game_state.message, 80, 50, Justify.CENTER,
                               page_id=next_game_view.page_id)
            elif action_name == 'CLOSING-BOOK':
                assert game_state.book
                render_book(pdf, game_state.book, next_game_view.page_id, game_state.treasure_id)
            elif action_name in CLICK_ZONES:
                click_zone = CLICK_ZONES[action_name]
                rotation = click_zone.pop('rotation', 0)
                link_alt = action_name.replace('_', ' ')
                add_link(pdf, **click_zone, rotation=rotation, page_id=next_game_view.page_id, link_alt=link_alt)
            else:
                page_id = next_game_view.page_id if next_game_view else None
                custom_action = game_state.combat and game_state.combat.enemy.custom_action_for(action_name)
                if custom_action:
                    if custom_action.renderer:
                        custom_action.renderer(pdf, page_id)
                    else:
                        action_button_render(pdf, btn_type=custom_action.btn_type, btn_pos=custom_action.btn_pos, page_id=page_id)
                elif action_name in ACTION_BUTTONS:
                    action_button_render(pdf, action_name, page_id=page_id)
                else:
                    arrow_button_render(pdf, action_name, page_id)
    if game_view.state.bonus_atk and game_state.mode in (GameMode.EXPLORE, GameMode.INFO):
        action_button_render(pdf, 'ATK_BOOST')
        bitfont_render(pdf, f'+{game_view.state.bonus_atk}', 10, 90)


def mazemap_render(pdf, game_view):
    map_id, x, y = game_view.state.coords
    tileset_background_render(pdf, atlas().maps[map_id].background)
    facing = game_view.state.facing
    # Drawing is done in this order (a=10, b=11, c=12):
    # ..02431..
    # ..57986..
    # ...acb...
    if facing == "north":
        # back row
        mazemap_render_tile(pdf,game_view,x-2,y-2,0)
        mazemap_render_tile(pdf,game_view,x+2,y-2,1)
        mazemap_render_tile(pdf,game_view,x-1,y-2,2)
        mazemap_render_tile(pdf,game_view,x+1,y-2,3)
        mazemap_render_tile(pdf,game_view,x,  y-2,4)
        # middle row
        mazemap_render_tile(pdf,game_view,x-2,y-1,5)
        mazemap_render_tile(pdf,game_view,x+2,y-1,6)
        mazemap_render_tile(pdf,game_view,x-1,y-1,7)
        mazemap_render_tile(pdf,game_view,x+1,y-1,8)
        mazemap_render_tile(pdf,game_view,x,  y-1,9)
        # front row
        mazemap_render_tile(pdf,game_view,x-1,y, 10)
        mazemap_render_tile(pdf,game_view,x+1,y, 11)
        mazemap_render_tile(pdf,game_view,x,  y, 12)
    elif facing == "south":
        # back row
        mazemap_render_tile(pdf,game_view,x+2,y+2,0)
        mazemap_render_tile(pdf,game_view,x-2,y+2,1)
        mazemap_render_tile(pdf,game_view,x+1,y+2,2)
        mazemap_render_tile(pdf,game_view,x-1,y+2,3)
        mazemap_render_tile(pdf,game_view,x,y+2,4)
        # middle row
        mazemap_render_tile(pdf,game_view,x+2,y+1,5)
        mazemap_render_tile(pdf,game_view,x-2,y+1,6)
        mazemap_render_tile(pdf,game_view,x+1,y+1,7)
        mazemap_render_tile(pdf,game_view,x-1,y+1,8)
        mazemap_render_tile(pdf,game_view,x,y+1,9)
        # front row
        mazemap_render_tile(pdf,game_view,x+1,y,10)
        mazemap_render_tile(pdf,game_view,x-1,y,11)
        mazemap_render_tile(pdf,game_view,x,y,12)
    elif facing == "west":
        # back row
        mazemap_render_tile(pdf,game_view,x-2,y+2,0)
        mazemap_render_tile(pdf,game_view,x-2,y-2,1)
        mazemap_render_tile(pdf,game_view,x-2,y+1,2)
        mazemap_render_tile(pdf,game_view,x-2,y-1,3)
        mazemap_render_tile(pdf,game_view,x-2,y,4)
        # middle row
        mazemap_render_tile(pdf,game_view,x-1,y+2,5)
        mazemap_render_tile(pdf,game_view,x-1,y-2,6)
        mazemap_render_tile(pdf,game_view,x-1,y+1,7)
        mazemap_render_tile(pdf,game_view,x-1,y-1,8)
        mazemap_render_tile(pdf,game_view,x-1,y,9)
        # front row
        mazemap_render_tile(pdf,game_view,x,y+1,10)
        mazemap_render_tile(pdf,game_view,x,y-1,11)
        mazemap_render_tile(pdf,game_view,x,y,12)
    elif facing == "east":
        # back row
        mazemap_render_tile(pdf,game_view,x+2,y-2,0)
        mazemap_render_tile(pdf,game_view,x+2,y+2,1)
        mazemap_render_tile(pdf,game_view,x+2,y-1,2)
        mazemap_render_tile(pdf,game_view,x+2,y+1,3)
        mazemap_render_tile(pdf,game_view,x+2,y,4)
        # middle row
        mazemap_render_tile(pdf,game_view,x+1,y-2,5)
        mazemap_render_tile(pdf,game_view,x+1,y+2,6)
        mazemap_render_tile(pdf,game_view,x+1,y-1,7)
        mazemap_render_tile(pdf,game_view,x+1,y+1,8)
        mazemap_render_tile(pdf,game_view,x+1,y,9)
        # front row
        mazemap_render_tile(pdf,game_view,x,y-1,10)
        mazemap_render_tile(pdf,game_view,x,y+1,11)
        mazemap_render_tile(pdf,game_view,x,y,12)


def mazemap_render_tile(pdf, game_view, x, y, render_pos):
    map_id = game_view.state.map_id
    _map = atlas().maps[map_id]
    if not mazemap_bounds_check(_map, x, y):
        return
    tile_id = mazemap_get_tile(game_view, map_id, x, y)
    if render_pos in (7, 2, 4, 3, 8):
    # We do not handle 9 because we expected warp tiles to be of same type,
    # and the other render_pos because we are lazy :D
        front_pos = mazemap_next_pos_facing(*game_view.state.coords[1:], game_view.state.facing)
        warped_coords = mapscript_get_warped_coords((map_id, *front_pos))
        if warped_coords:  # we display the tile seen through the warp
            seen_pos = mazemap_next_pos_facing(*warped_coords[1:], game_view.state.facing, render_pos=render_pos)
            tile_id = mazemap_get_tile(game_view, warped_coords[0], *seen_pos)
            # print(f'warped_coords! {(map_id, *front_pos)} -> {warped_coords} >BACK(render_pos={render_pos}): {seen_pos} ({tile_id})')
    tile = TILES[tile_id]
    if not tile:
        return
    img_filepath = (REL_RELEASE_DIR + f'images/tiles/{tile}.png') if tile_id < 20 else f'assets/tiles/{tile}.png'
    if tile_id == 16: img_filepath = 'assets/tiles/skull_pile2.png'
    draw_area = _DRAW_AREAS[render_pos]
    # relies on: https://github.com/reingart/pyfpdf/pull/158
    with pdf.rect_clip(x=draw_area.dest_x, y=draw_area.dest_y, w=draw_area.width, h=draw_area.height):
        pdf.image(img_filepath, x=draw_area.dest_x-draw_area.src_x, y=draw_area.dest_y-draw_area.src_y)
    if render_pos == 4:  # center of back row
        next_pos_facing = mazemap_next_pos_facing(x, y, game_view.state.facing)
        # Extra rendering in case of a boulder one tile further:
        if game_view.tile_override((map_id, *next_pos_facing)) in (20, 21, 22):
            pdf.image('assets/boulder_small.png', x=68, y=48)
    if render_pos == 9:  # center of midle row
        _enemy = mapscript_get_enemy_at((map_id, x, y), game_view.state)
        if _enemy and _enemy.show_on_map and not game_view.enemy_vanquished((map_id, x, y)):
            enemy_render_small(pdf, _enemy)


def action_render(pdf, spellbook, items):
    # The HEAL spell is rendered separately,
    # as it is present in the "actions" dict
    for btn_type in ACTION_BUTTONS[2:2+spellbook]:
        action_button_render(pdf, btn_type)
    i = 0
    for btn_type in items:
        if btn_type != 'ARMOR_PART':
            action_button_render(pdf, btn_type, item_index=i)
            i += 1
    # "Hardcoded" rendering of new mod collectible item:
    armor_parts_count = items.count('ARMOR_PART')
    if armor_parts_count:
        treasure_render_collectible(pdf, 'ARMOR', armor_parts_count)


def combat_render(pdf, game_state):
    'Replicates combat_render_input'
    combat = game_state.combat
    _enemy = combat.enemy
    enemy_has_frames = get_image_info(pdf, _enemy_img_filepath(_enemy))['w'] > config().VIEW_WIDTH
    if _enemy.hp > 0 or enemy_has_frames:  # if the enemy visual is made of several frames, assume there is one for its death
        enemy_render(pdf, combat)
        if combat.boneshield_up:
            pdf.image('assets/enemies/bone_shield.png', x=0, y=0)  # Replicates boss_boneshield_render
    if _enemy.hp <= 0 and combat.enemy.gold:
        treasure_render_gold(pdf, combat.enemy.gold)
    if combat.round >= 0:
        render_bar(pdf, _enemy.hp, _enemy.max_hp)
    else:  # == combat round -1
        bitfont_render(pdf, patch_enemy_name(_enemy.name).replace('_', ' '), 80, 2, Justify.CENTER)
        if _enemy.intro_msg:
            bitfont_render(pdf, _enemy.intro_msg, 2, 13)
        if _enemy.music:
            assert not game_state.music
            # Beware not to hide Empress face (around x=72)
            action_button_render(pdf, 'MUSIC', url=_enemy.music, btn_pos=Position(50, 9))
    info_render_hpmp(pdf, game_state)
    combat_render_log(pdf, "You:", combat.avatar_log, 20)
    combat_render_log(pdf, "Enemy:", combat.enemy_log, 60)
    if game_state.hp <= 0:
        next_page_id = _enemy.post_defeat.game_view.page_id if _enemy.post_defeat else 1
        bitfont_render(pdf, 'You are defeated...', 158, 100, Justify.RIGHT, page_id=next_page_id)


def combat_render_log(pdf, prefix, log, start_y):
    if log:
        bitfont_render(pdf, prefix, 2, start_y)
        bitfont_render(pdf, log.action, 2, start_y+10)
        bitfont_render(pdf, log.result, 2, start_y+20)


def enemy_render(pdf, combat):
    _enemy, _round = combat.enemy, combat.round
    combat_round, img_filepath = combat.combat_round, _enemy_img_filepath(_enemy)
    # If the image is larger than the VIEW_WIDTH, it is sliced in frames:
    frame_count = get_image_info(pdf, img_filepath)['w'] / config().VIEW_WIDTH
    # Some enemies explicitely state the frame to display:
    frame = _enemy.enemy_frame and _enemy.enemy_frame(combat)
    if frame is None:
        # Else, the frame corresponding to the current round is used:
        if _round + 1 >= frame_count and not _enemy.loop_frames:
            frame = frame_count - 1  # In case there are more rounds than frames, the last one is used for the remaining rounds:
        else:
            frame = (_round + 1) % frame_count
    pdf.image(img_filepath, x=-frame*config().VIEW_WIDTH, y=0)
    if _round >= 0 and combat_round and combat_round.sfx:
        sfx_render(pdf, combat_round.sfx)


def enemy_render_small(pdf, _enemy, scale=2/3):
    small_img_filepath = f'assets/enemies/small/{_enemy.name}.png'
    if not exists(small_img_filepath):  # fallback to auto-generated miniature:
        small_img_filepath = f'{MINIATURES_DIR_PATH}/{_enemy.name}.png'
        if small_img_filepath not in MINIATURES_ALREADY_GENERATED:
            makedirs(MINIATURES_DIR_PATH, exist_ok=True)
            width, height = config().VIEW_WIDTH, config().VIEW_HEIGHT
            with Image.open(_enemy_img_filepath(_enemy)) as img:
                # Cropping 1st, in case image contains multiple frames:
                img.crop((0, 0, width, height))\
                   .resize((round(width*scale), round(height*scale)), resample=Image.NEAREST)\
                   .save(small_img_filepath)
            MINIATURES_ALREADY_GENERATED.add(small_img_filepath)
    pdf.image(small_img_filepath, x=25, y=18)


def _enemy_img_filepath(_enemy):
    return f'assets/enemies/{_enemy.name}.png'


def render_bar(pdf, value, max_value, y=1, color_index=0):
    start_x = 2
    with pdf.rect_clip(x=start_x, y=y, w=10 + max_value, h=14):
        pdf.image('assets/healthbar.png', x=start_x, y=y)
    with pdf.rect_clip(x=start_x + 10 + max_value, y=y, w=10, h=14):
        pdf.image('assets/healthbar.png', x=start_x + max_value - 140, y=y)
    if value > 0:
        with pdf.rect_clip(x=start_x + 10, y=y, w=value, h=14):
            pdf.image('assets/healthbar.png', x=start_x + 10, y=y-(1 + color_index)*14)


def arrow_button_render(pdf, direction, page_id=None, shift_x=0, shift_y=0):
    btn_pos = ARROW_BUTTONS_POS[direction]
    with pdf.rotation(btn_pos.angle, x=btn_pos.x + _ACTION_BTN_SIZE//2 + shift_x,
                                     y=btn_pos.y + _ACTION_BTN_SIZE//2 + shift_y):
        pdf.image('assets/arrow-right.png', x=btn_pos.x + shift_x, y=btn_pos.y + shift_y)
    if page_id:
        link_pos = ARROW_LINKS_POS[direction]
        flipped = direction in ('MOVE-FORWARD', 'MOVE-BACKWARD')
        link_width = ARROW_LINK_WIDTH if flipped else ARROW_LINK_HEIGHT
        link_height = ARROW_LINK_HEIGHT if flipped else ARROW_LINK_WIDTH
        return add_link(pdf, link_pos.x, link_pos.y, link_width, link_height, page_id=page_id, link_alt=direction)
    return None


def render_book(pdf, book, page_id, treasure_id):
    y = 70 - book.text.count('\n') * 6
    if treasure_id:
        assert not book.img
    else:
        pdf.image('assets/open-book.png', x=15, y=30)
        if book.img:
            pdf.image(book.img, x=32, y=32)
            y += 16
        if book.portrait is not None:
            portrait_render(pdf, book.portrait, x=35, y=33)
        if book.sfx:
            sfx_render(pdf, book.sfx)
        if book.treasure_id:
            treasure_render_item(pdf, book.treasure_id, Position(x=86, y=76))
        if book.music:
            action_button_render(pdf, 'MUSIC', url=book.music, btn_pos=Position(24, 46))
        if book.bird_index is not None:
            link = link_from_page_id(pdf, page_id)
            x, y = 80, 60
            with pdf.rect_clip(x=x, y=y, w=45, h=47):
                pdf.image('assets/black_bird.png', x=x - book.bird_index*45, y=y, link=link)
    bitfont_render(pdf, book.text, 80, y, Justify.CENTER, page_id=page_id)
    if book.next:
        white_arrow_render(pdf, 'NEXT', x=120, y=100, page_id=page_id)


def render_filler_page(pdf, _):
    pdf.add_page()
    pdf.image(REL_RELEASE_DIR + 'images/backgrounds/black.png', x=0, y=0)


def render_trick(pdf, next_game_view):
    trick = next_game_view.state.trick
    pdf.add_page()
    background_img_filepath = f'assets/backgrounds/{trick.background}.png' if trick.background else REL_RELEASE_DIR + 'images/backgrounds/nightsky.png'
    pdf.image(background_img_filepath, x=0, y=0)
    bitfont_render(pdf, trick.message, 80, 60, Justify.CENTER,
                   page_id=next_game_view.page_id if trick.link else None)
    if trick.music:
        action_button_render(pdf, 'MUSIC', url=trick.music, btn_pos=Position(x=72, y=20))


# Those constants are defined for performance reasons,
# to avoid costly calls to pyduktape.JSProxy methods
# that perform costly DuktapeContext._check_thread calls:
from .mod import Proxy
_ACTION_BTN_SIZE = action().BUTTON_SIZE
_DRAW_AREAS = [Proxy(dest_x=draw_area.dest_x, dest_y=draw_area.dest_y,
                     src_x=draw_area.src_x,   src_y=draw_area.src_y,
                     width=draw_area.width,   height=draw_area.height) for draw_area in tileset().draw_area]
_ENEMY_IMG_SRC = [enemy().img[enemy_type].src for enemy_type in range(8)]
