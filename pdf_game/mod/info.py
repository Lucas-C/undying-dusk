from ..entities import GameMode, Position
from ..mazemap import mazemap_get_tile

from .scenes import BASE_MUSIC_URL


def custom_info_logic(game_view, actions, _GameView):
    # This secret can only be achieved the 2nd time the hero visits the village, to avoid exploding #states:
    gs = game_view.state.clean_copy()
    if 'FOUNTAIN_HINT' in gs.hidden_triggers and gs.gold and 'FOUNTAIN_WISH' not in gs.secrets_found:
        if mazemap_get_tile(game_view, gs.map_id, *gs.coords[1:]) == 24:  # standing in the fountain
            next_state = gs.with_secret('FOUNTAIN_WISH')\
                           ._replace(gold=gs.gold - 1,
                                     message='You throw a coin\nin the water.\nDeep down under your feet,\nsomething rumbles\nin the dark.\n(you found a SECRET)',
                                     mode=GameMode.EXPLORE,
                                     music=BASE_MUSIC_URL + 'AlexandrZhelanov-Insight.mp3',
                                     music_btn_pos=Position(x=72, y=90))
            actions['THROW-COIN'] = _GameView(next_state)
