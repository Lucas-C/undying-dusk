from ..entities import GameMode, MessagePlacement, Position
from ..mazemap import mazemap_next_pos_facing, mazemap_get_tile

from .scenes import BASE_MUSIC_URL


def custom_info_logic(game_view, actions, _GameView):
    # This secret can only be achieved the 2nd time the hero visits the village, to avoid exploding #states:
    gs = game_view.state.clean_copy()
    if 'FOUNTAIN_HINT' in gs.hidden_triggers and gs.gold and 'FOUNTAIN_WISH' not in gs.secrets_found:
        next_pos_facing = mazemap_next_pos_facing(*gs.coords[1:], gs.facing)
        if mazemap_get_tile(game_view, gs.map_id, *next_pos_facing) == 24:  # facing a fountain
            next_state = gs.with_secret('FOUNTAIN_WISH')\
                           ._replace(gold=gs.gold - 1,
                                     message='You throw a coin in the water.\nDeep down under your feet\nsomething rumbles in the dark.\n(you found a SECRET)',
                                     mode=GameMode.EXPLORE,
                                     music=BASE_MUSIC_URL + 'AlexandrZhelanov-Insight.mp3',
                                     music_btn_pos=Position(x=72, y=15))
            actions['THROW-COIN'] = _GameView(next_state)
    if game_view.state.coords == (8, 11, 9) and 'FISH' in game_view.state.items:
        items = tuple(i for i in game_view.state.items if i != 'FISH') + ('FISH_ON_A_STICK',)
        message = 'You pick a twig and\nput it in the fish'
        actions['COMBINE_WITH_TWIG'] = _GameView(game_view.state._replace(items=items,
                                                                          treasure_id=31,
                                                                          mode=GameMode.EXPLORE,
                                                                          message=message,
                                                                          msg_place=MessagePlacement.UP))
