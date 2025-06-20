from ..entities import Position, SFX

from .scenes import BASE_MUSIC_URL


MAP_ID = 9            # only possible in Dead Walkways
POS = (9, 6)          # starting point (just before boss fight)
FACING = 'north'      # starting direction

FACING_SIDE = 'west'  # FACING rotated left
POS2 = (9, 5)         # POS 1 tile forward in FACING direction
POS3 = (9, 4)         # POS 2 tiles forward in FACING direction

MSGS = (
    'KO...',
    'KONA...',
    'KONAM...',
    'KONAMI...',
    'KONAMI C...',
    'KONAMI CO...',
    'KONAMI COD...',
)


def custom_explore_logic(action_name, gs, new_gs):
    if gs.map_id != MAP_ID:
        return new_gs
    pos, facing, puzzle_step = gs.coords[1:], gs.facing, gs.puzzle_step
    if pos == POS:
        if facing == FACING:
            if action_name == 'TURN-LEFT':
                if puzzle_step == 6:
                    return gs_with_msg(new_gs, 7)
                if puzzle_step == 4:
                    return gs_with_msg(new_gs, 5)
            elif action_name == 'MOVE-FORWARD' and 'KONAMI_CODE' not in gs.secrets_found:
                return gs_with_msg(new_gs, 1)
        elif facing == FACING_SIDE and action_name == 'TURN-RIGHT':
            if puzzle_step == 7:
                return new_gs.with_secret('KONAMI_CODE')\
                             ._replace(sfx=SFX(id=7, pos=Position(64, 88)),
                                       message='KONAMI CODE!\nYou feel a mystical force!\n(you found a SECRET)',
                                       music=BASE_MUSIC_URL + 'AlexandrZhelanov-TreasuresOfAncientDungeon2.mp3',
                                       music_btn_pos=Position(x=72, y=25))
            if puzzle_step == 5:
                return gs_with_msg(new_gs, 6)
    if (pos, facing) == (POS2, FACING):
        if puzzle_step == 3 and action_name == 'MOVE-BACKWARD':
            return gs_with_msg(new_gs, 4)
        if puzzle_step == 1 and action_name == 'MOVE-FORWARD':
            return gs_with_msg(new_gs, 2)
    if (pos, facing, action_name) == (POS3, FACING, 'MOVE-BACKWARD') and puzzle_step == 2:
        return gs_with_msg(new_gs, 3)
    return new_gs._replace(puzzle_step=0)


def gs_with_msg(gs, step):
    return gs._replace(puzzle_step=step, message=f'The wind whispers:\n"{MSGS[step - 1]}"')
