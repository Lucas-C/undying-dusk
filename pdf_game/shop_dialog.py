# Since commit effbb4f on Gitlab, code that handled the original shop items has been removed,
# breaking full compatibility with the original JS shops.
from .entities import DialogButtonType, DialogOption, GameMode
from .explore import enter_map
from .js import atlas, shop
from .logs import log
from .mazemap import mazemap_is_exit, mazemap_is_shop


def dialog_logic(game_view, actions, _GameView):
    assert not actions
    game_state = game_view.state.clean_copy()
    for i, dialog_option in enumerate(build_dialog_options(game_state)):
        if dialog_option.can_buy:
            if dialog_option.btn_type == DialogButtonType.EXIT:
                new_state = dialog_option.buy(_exit_shop(game_state))
            else:
                new_state = dialog_option.buy(game_state)
                if dialog_option.msg:
                    log(new_state, dialog_option.msg.replace('\n', ' '))
            actions[dialog_option.btn_type.action_name(i)] = _GameView(new_state)


def build_dialog_options(game_state):
    _shop = shop()[game_state.shop_id]
    assert _shop, f'shop_id={game_state.shop_id}'
    _shop = resolve_redirect(_shop, game_state)
    try:
        options = list(_shop.dialog_options)
    except (AttributeError, KeyError):
        options = ()
    if not options:
        try:  # handling actual shops:
            options = [item.dialog_option(game_state) for item in _shop.item]
        except AttributeError: #  'CutScene' object has no attribute 'item'
            options = [DialogOption.only_msg(_shop.text)]
    # The last button is always the Next/Exit one:
    try:
        next_scene_id = _shop.next_scene_id
    except (AttributeError, KeyError):
        next_scene_id = None
    if next_scene_id is not None:
        options.append(DialogOption.only_link(DialogButtonType.NEXT, next_scene_id))
    else:
        try:
            no_exit = _shop.no_exit
        except (AttributeError, KeyError):
            no_exit = False
        if not no_exit and not any(opt.btn_type == DialogButtonType.EXIT for opt in options):
            options.append(_exit_option(_shop))
    return options


def resolve_redirect(_shop, game_state):
    # Handling potential redirect to another CutScene:
    while True:
        try:
            redirected_shop = _shop.redirect(game_state)
        except (AttributeError, KeyError, TypeError):  # 'NoneType' object is not callable:
            redirected_shop = None
        if redirected_shop is None:
            return _shop
        _shop = redirected_shop


def _exit_option(_shop):
    try:
        exit_msg = _shop.exit_msg
    except (AttributeError, KeyError):
        exit_msg = "Exit"
    return DialogOption(
        btn_type=DialogButtonType.EXIT,
        msg=exit_msg,
        can_buy=True,
        buy=lambda gs: gs,
    )


def _exit_shop(game_state):
    _map = atlas().maps[game_state.map_id]
    new_game_state = game_state._replace(mode=GameMode.EXPLORE, shop_id=-1)
    map_shop = mazemap_is_shop(_map, game_state.x, game_state.y)
    if map_shop:  # there is one case where the current position is not a shop: the intro screen
        try:
            new_game_state = new_game_state._replace(x=map_shop.dest_x, y=map_shop.dest_y)
        except KeyError:  # for new shops, assuming no dest_x/dest_y means it is also an exit
            new_game_state = enter_map(new_game_state, mazemap_is_exit(_map, game_state.x, game_state.y))
        if map_shop.get('facing') is not None:
            new_game_state = new_game_state._replace(facing=map_shop.facing)
        try:
            if map_shop.ephemeral:
                new_game_state = new_game_state.with_trigger_activated(game_state.coords)
        except (AttributeError, KeyError):  # do nothing if shop does not has an .ephemeral field
            pass
    return new_game_state
