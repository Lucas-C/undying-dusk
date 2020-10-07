from .power import power_heal

from .mod.info import custom_info_logic


def info_logic(game_view, actions, _GameView):
    game_state = game_view.state.clean_copy()
    assert len(actions.keys()) <= 1, f'Actions: {actions.keys()} - State: {game_state}'  # must be SHOW-INFO or empty (temporarily)
    custom_info_logic(game_view, actions, _GameView)
    # pylint: disable=unreachable
    return  # we forbid using HEAL outside combats, as this would grow the states count exponentially
    if game_state.spellbook >= 1 and game_state.mp:
        next_state = power_heal(game_state)
        if next_state:
            actions['HEAL'] = _GameView(next_state)
