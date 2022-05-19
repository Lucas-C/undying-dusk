from os import makedirs
from os.path import dirname, join, realpath
from typing import Dict, NamedTuple, Tuple

from PIL import Image

from .js import atlas, minimap, tileset

from .mod.minimap import minimap_is_unknown


class Palette(NamedTuple):
    name: str
    columns: int
    colors: Dict[str, Tuple[int]]


DIR_REL_PATH = join(dirname(realpath(__file__)), '..', 'minimaps')
ALREADY_GENERATED = set()


def minimap_render(pdf, game_view):
    map_id = game_view.state.map_id
    # starting draw location
    left_x = minimap().MINIMAP_MARGIN_LEFT
    top_y = minimap().MINIMAP_MARGIN_TOP
    # render minimap background, pre-rendered
    pdf.image(_get_prerendered_img(map_id, game_view.state), x=left_x, y=top_y)
    # render avatar cursor
    if minimap_is_unknown(*game_view.state.coords):
        return
    btn_size = minimap().MINIMAP_ICON_SIZE
    draw_x = game_view.state.x * btn_size + left_x
    draw_y = game_view.state.y * btn_size + top_y
    cursor_direction = {
        "west": minimap().MINIMAP_CURSOR_WEST,
        "north": minimap().MINIMAP_CURSOR_NORTH,
        "east": minimap().MINIMAP_CURSOR_EAST,
        "south": minimap().MINIMAP_CURSOR_SOUTH,
    }[game_view.state.facing]
    _minimap_render_cursor(pdf, draw_x, draw_y, cursor_direction)


def _get_prerendered_img(map_id, game_state):
    'Pre-render all minimaps as PNG files to make rendering faster'
    _map = atlas().maps[map_id]
    walkablity_changes = _get_walkablity_changing_tile_overrides(map_id, _map, game_state)
    img_filepath = _get_img_filepath(map_id, walkablity_changes)
    if img_filepath not in ALREADY_GENERATED:
        makedirs(DIR_REL_PATH, exist_ok=True)
        icon_size = minimap().MINIMAP_ICON_SIZE
        icon_imgs = _get_icon_images()
        map_height, map_width = len(_map.tiles), len(_map.tiles[0])
        with Image.new('RGB', (map_width * icon_size, map_height * icon_size)) as img:
            # render map
            for i in range(map_width):
                for j in range(map_height):
                    if not minimap_is_unknown(map_id, i, j):
                        tile_id = _map.tiles[j][i]
                        if tile_id == 15:
                            icon_type = 'WATER'
                        else:
                            walkable = walkablity_changes.get((i, j), tileset().walkable[tile_id])
                            icon_type = 'WALKABLE' if walkable else 'NONWALKABLE'
                        img.paste(icon_imgs[icon_type], (i * icon_size, j * icon_size))
            # render exits
            for _exit in _map.exits:
                img.paste(icon_imgs['EXIT'], (_exit.exit_x * icon_size, _exit.exit_y * icon_size))
            # render shops
            for shop in _map.shops:
                img.paste(icon_imgs['EXIT'], (shop.exit_x * icon_size, shop.exit_y * icon_size))
            img.save(img_filepath)
        ALREADY_GENERATED.add(img_filepath)
    return img_filepath


def _get_walkablity_changing_tile_overrides(map_id, _map, game_state):
    walkablity_changes = {}  # (x, y) -> walkable
    for ((_map_id, x, y), tile_override) in game_state.tile_overrides:
        if _map_id != map_id:
            continue
        if game_state.rolling_boulder and (_map_id, x, y) == game_state.rolling_boulder.coords:
            continue
        base_walkablity = tileset().walkable[_map.tiles[y][x]]
        override_walkablity = tileset().walkable[tile_override]
        if base_walkablity != override_walkablity:
            walkablity_changes[(x, y)] = override_walkablity
    return walkablity_changes


def _get_img_filepath(map_id, walkablity_changes):
    suffix = '_'.join(f"{x}-{y}-{1 if w else 0}" for (x, y), w in sorted(walkablity_changes.items()))
    return f'{DIR_REL_PATH}/map_{map_id}_{suffix}.png'


def _get_icon_images():
    palette = parse_gpl_file('DawnBringer.gpl')
    return {
        'WALKABLE': plain_icon(palette.colors['Light8']),
        'NONWALKABLE': plain_icon(palette.colors['Dark1']),
        'EXIT': plain_icon(palette.colors['Light2']),
        'WATER': plain_icon(palette.colors['Light1']),
    }


def parse_gpl_file(gpl_filepath):
    with open(gpl_filepath, encoding='utf8') as gpl_file:
        lines = [line.strip() for line in gpl_file.readlines()]
    assert lines[0] == 'GIMP Palette'
    name = lines[1][len('Name: '):]
    columns = int(lines[2][len('Columns: '):])
    colors = {}
    for line in lines[3:]:
        if not line.startswith('#'):
            rgba, color = line.split('    ')
            colors[color] = tuple(map(int, [c.strip() for c in rgba.split()]))
    return Palette(name=name, columns=columns, colors=colors)


def plain_icon(color):
    icon_size = minimap().MINIMAP_ICON_SIZE
    img = Image.new('RGB', (icon_size, icon_size))
    img.paste(color, (0, 0, *img.size))
    return img


def _minimap_render_cursor(pdf, screen_x, screen_y, icon_type):
    btn_size = minimap().MINIMAP_ICON_SIZE
    img_filepath = 'assets/minimap_cursor.png'
    with pdf.rect_clip(x=screen_x, y=screen_y, w=btn_size, h=btn_size):
        pdf.image(img_filepath, x=screen_x - 2*icon_type*btn_size, y=screen_y)
