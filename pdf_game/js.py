from functools import lru_cache as cached

# pylint: disable=no-name-in-module, redefined-outer-name
from pyduktape import DuktapeContext

from .mod import Proxy
from .mod.hero import patch_avatar, patch_info
from .mod.scenes import patch_shop
from .mod.world import patch_atlas, patch_tileset


REL_RELEASE_DIR = 'heroine-dusk/release/'


@cached()
def action():
    context = DuktapeContext()
    context.set_globals(Image=context.get_global('Object'))
    context.eval_js_file(REL_RELEASE_DIR + 'js/action.js')
    context.eval_js('action_init()')
    action = context.get_global('action')
    class Action:
        def __getattr__(self, attr):
            glob = context.get_global(attr)
            return glob if glob is not None else getattr(action, attr)
    return Action()


@cached()
def atlas():
    context = DuktapeContext()
    context.eval_js_file(REL_RELEASE_DIR + 'js/enemy.js')  # dependency due to ENEMY_SHADOW_TENDRILS constant
    context.eval_js_file(REL_RELEASE_DIR + 'js/atlas.js')
    atlas = context.get_global('atlas')
    atlas = patch_atlas(atlas)
    # Commented out as locked doors & skukk piles are placed manually in the mod.
    # for bp in mapscript().bone_piles:
        # atlas.maps[bp.map_id].tiles[bp.y][bp.x] = 16  # skull_pile
    # for ld in mapscript().locked_doors:
        # atlas.maps[ld.map_id].tiles[ld.y][ld.x] = 18  # locked_door
    return atlas


@cached()
def avatar():
    context = DuktapeContext()
    context.eval_js_file(REL_RELEASE_DIR + 'js/avatar.js')
    context.eval_js('avatar_reset()')
    avatar = context.get_global('avatar')
    return patch_avatar(avatar)


@cached()
def bitfont():
    context = DuktapeContext()
    context.set_globals(Image=context.get_global('Object'))
    context.eval_js_file(REL_RELEASE_DIR + 'js/bitfont.js')
    context.eval_js('bitfont_init()')
    return context.get_global('bitfont')


@cached()
def config():
    context = DuktapeContext()
    context.eval_js_file(REL_RELEASE_DIR + 'js/config.js')
    return Proxy(VIEW_WIDTH=context.get_global('VIEW_WIDTH'),
                 VIEW_HEIGHT=context.get_global('VIEW_HEIGHT'))


@cached()
def enemy():
    context = DuktapeContext()
    context.set_globals(Image=context.get_global('Object'))
    context.eval_js_file(REL_RELEASE_DIR + 'js/power.js')  # dependency due to ENEMY_POWER_ATTACK constant
    context.eval_js_file(REL_RELEASE_DIR + 'js/enemy.js')
    context.eval_js('enemy_init()')
    enemy = context.get_global('enemy')
    class Enemy:
        def __getattr__(self, attr):
            glob = context.get_global(attr)
            return glob if glob is not None else getattr(enemy, attr)
    return Enemy()


@cached()
def info():
    context = DuktapeContext()
    context.set_globals(Image=context.get_global('Object'))
    context.eval_js_file(REL_RELEASE_DIR + 'js/info.js')
    context.eval_js('info_init()')
    info = patch_info(context.get_global('info'))
    class Info:
        def __getattr__(self, attr):
            glob = context.get_global(attr)
            return glob if glob is not None else getattr(info, attr)
    return Info()


@cached()
def tileset():
    context = DuktapeContext()
    context.set_globals(Image=context.get_global('Object'))
    context.eval_js_file(REL_RELEASE_DIR + 'js/tileset.js')
    context.eval_js('tileset_init()')
    return patch_tileset(context.get_global('tileset'))


@cached()
def treasure():
    context = DuktapeContext()
    context.set_globals(Image=context.get_global('Object'))
    context.eval_js_file(REL_RELEASE_DIR + 'js/treasure.js')
    context.eval_js('treasure_init()')
    treasure = context.get_global('treasure')
    class Treasure:
        def __getattr__(self, attr):
            glob = context.get_global(attr)
            return glob if glob is not None else getattr(treasure, attr)
    return Treasure()


@cached()
def dialog():
    context = DuktapeContext()
    context.set_globals(Image=context.get_global('Object'))
    context.eval_js_file(REL_RELEASE_DIR + 'js/dialog.js')
    class Dialog:
        def __getattr__(self, attr):
            return context.get_global(attr)
    return Dialog()


@cached()
def shop():
    context = DuktapeContext()
    context.eval_js_file(REL_RELEASE_DIR + 'js/shop.js')
    shop = context.get_global('shop')
    class Shop:
        def __getattr__(self, attr):
            return context.get_global(attr)
        def __getitem__(self, index):
            # pylint: disable=unsubscriptable-object
            return patch_shop(shop[index] if index < len(shop) else None, index)
    return Shop()


@cached()
def mapscript():
    context = DuktapeContext()
    context.eval_js_file(REL_RELEASE_DIR + 'js/mapscript.js')
    return context.get_global('mapscript')


@cached()
def minimap():
    context = DuktapeContext()
    context.set_globals(Image=context.get_global('Object'))
    context.eval_js_file(REL_RELEASE_DIR + 'js/minimap.js')
    minimap = context.get_global('minimap')
    class Minimap:
        def __getattr__(self, attr):
            glob = context.get_global(attr)
            return glob if glob is not None else getattr(minimap, attr)
    return Minimap()
