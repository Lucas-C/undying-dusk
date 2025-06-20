from collections import defaultdict
from queue import LifoQueue

from .entities import GameMilestone, GameMode
from .js import shop
from .optional_deps import ansi_wrap


ALREADY_LOGGED = defaultdict(list)
QUIET_LOGGING = False


def quiet_logging():
    global QUIET_LOGGING
    QUIET_LOGGING = True


def log(game_state, msg, color=None):
    assert msg
    if QUIET_LOGGING:
        return
    game_state_nofacing = game_state._replace(facing='')
    if msg in ALREADY_LOGGED[game_state_nofacing]:
        return
    if color:
        msg = ansi_wrap(msg, color=color)
    progress = (game_state.armor
              + len(game_state.items)
              + len(game_state.hidden_triggers)
              + game_state.spellbook
              + len(game_state.tile_overrides)
              + len(game_state.triggers_activated)
              + len(game_state.vanquished_enemies)
              + game_state.weapon)
    print(' ' * progress + msg)
    ALREADY_LOGGED[game_state_nofacing].append(msg)


def log_path_to(game_view, actions_only=False, map_as_string=None, stop_at=None, stop_at_cond=None):
    assert actions_only ^ bool(map_as_string)
    for gv, prev_gv in reversed(list(_iter_path_view_logs(game_view, stop_at, stop_at_cond))):
        if map_as_string:
            if gv.state.mode == GameMode.EXPLORE:
                print(map_as_string(gv))
            elif gv.state.mode == GameMode.COMBAT:
                print(_combat_line(gv.state))
            elif gv.state.mode == GameMode.DIALOG:
                _shop = shop()[gv.state.shop_id]
                try:
                    for i, item in enumerate(_shop.item):
                        print(f'{i}: {item.msg1} - {item.msg2}')
                except AttributeError:  # CutScene or class like RoomForTheNight, SageTherel...
                    print(_shop)
        elif actions_only and prev_gv:
            try:
                action_name = next(name for name, next_gv in prev_gv.actions.items() if next_gv == gv)
                _print_action(gv, action_name)
            except StopIteration: pass
        else:
            print(repr(gv.state))

def log_combat(start_gv, skip_rounds=0):
    if not start_gv.state.combat:
        print('GameView is not a combat view: looking for latest combat')
        while not start_gv.state.combat:
            start_gv = start_gv.src_view
    gv_pairs = list(reversed(list(_iter_path_view_logs(start_gv, stop_at_cond=lambda gv: not gv.state.combat or gv.state.milestone))))
    for gv, prev_gv in gv_pairs[skip_rounds:]:
        try:
            action_name = next(name for name, next_gv in prev_gv.actions.items() if next_gv == gv)
        except StopIteration:  # depending on where this utility function is called, not all .actions may be filled:
            action_name = gv.state.combat.action_name
        _print_action(gv, action_name)

def _print_action(gv, action_name):
    action_name = action_name or '<NONE>'
    if gv.state.mode == GameMode.EXPLORE:
        if action_name in ('BURN', 'UNLOCK'):
            print(f'{action_name:>6} @ {gv.state.coords}')
        elif action_name == 'END-COMBAT-AFTER-VICTORY':
            gs = gv.src_view.state
            print(f'{action_name} on {gs.combat.enemy.name} (HP={gs.hp} - +gold={gs.combat.enemy.gold})')
        else:
            print(action_name)
    elif gv.state.mode == GameMode.COMBAT:
        print(f'{action_name:>14} / {gv.state.combat.enemy.name} @ {gv.state.coords}: ' + _combat_line(gv.state))
    else:
        print(f'{action_name} @ shop {gv.state.shop_id}')

def _combat_line(gs):
    combat = gs.combat
    line = f'Round {combat.round:>2}: eHP={combat.enemy.hp:>2}/{combat.enemy.max_hp} aHP={gs.hp:>2}/{gs.max_hp} aMP={gs.mp:>1}'
    if combat.avatar_log:
        line += f' | Hero: {combat.avatar_log.action:<17} {combat.avatar_log.result:<16}'
    if combat.enemy_log:
        line += f' | Enemy: {combat.enemy_log.action} {combat.enemy_log.result}'
    if gs.message:
        line += ' | ' + gs.message.replace('\n', ' / ')
    return line

def _iter_path_view_logs(game_view, stop_at_gv=None, stop_at_cond=None):
    while game_view != stop_at_gv and not (stop_at_cond and stop_at_cond(game_view)):
        yield game_view, game_view.src_view
        game_view = game_view.src_view


def log_victorious_combats(combat_end_gv):
    start_combat_gv = combat_end_gv
    while start_combat_gv.src_view.state.combat:
        start_combat_gv = start_combat_gv.src_view
        if start_combat_gv.state.milestone:
            break
    states_logged = set()
    gvs = LifoQueue()
    gvs.put(start_combat_gv)
    while not gvs.empty():
        gv = gvs.get()
        is_final = False
        for child_gv in gv.actions.values():
            if child_gv:
                if not child_gv.state.combat or child_gv.state.milestone in (GameMilestone.CHECKPOINT, GameMilestone.VICTORY):
                    is_final = True
                else:
                    gvs.put(child_gv)
        if is_final and gv.state not in states_logged:
            log_combat(gv)
            states_logged.add(gv.state)


def log_paths_diff(gv1, gv2, actions_only=False, map_as_string=None):
    ancestor_gv = _common_gv_ancestor(gv1, gv2)
    print()
    print('#######################')
    print('### Common ancestor ###')
    print('#######################')
    print(ancestor_gv.state)
    print()
    print('################')
    print('### 1st path ###')
    print('################')
    log_path_to(gv1, actions_only, map_as_string, stop_at=ancestor_gv)
    if actions_only and gv1 != ancestor_gv:
        print(gv1.state)
    print()
    print('################')
    print('### 2nd path ###')
    print('################')
    log_path_to(gv2, actions_only, map_as_string, stop_at=ancestor_gv)
    if actions_only and gv2 != ancestor_gv:
        print(gv2.state)

def _common_gv_ancestor(gv1, gv2):
    gv1_ancestor_ids = set()
    while gv1:
        gv1_ancestor_ids.add(id(gv1))
        gv1 = gv1.src_view
    while gv2:
        if id(gv2) in gv1_ancestor_ids:
            return gv2
        gv2 = gv2.src_view
    return None


def diff_game_states(gs1, gs2):
    if gs1.coords != gs2.coords:
        print(f'Differing coords: {gs1.coords} != {gs2.coords}')
    if gs1.facing != gs2.facing:
        print(f'Differing facing: {gs1.facing} != {gs2.facing}')
    if gs1.mode != gs2.mode:
        print(f'Differing mode: {gs1.mode} != {gs2.mode}')
    if gs1.hp != gs2.hp:
        print(f'Differing HP: {gs1.hp} != {gs2.hp}')
    if gs1.max_hp != gs2.max_hp:
        print(f'Differing max HP: {gs1.max_hp} != {gs2.max_hp}')
    if gs1.mp != gs2.mp:
        print(f'Differing MP: {gs1.mp} != {gs2.mp}')
    if gs1.max_mp != gs2.max_mp:
        print(f'Differing max MP: {gs1.max_mp} != {gs2.max_mp}')
    if gs1.gold != gs2.gold:
        print(f'Differing gold: {gs1.gold} != {gs2.gold}')
    if gs1.weapon != gs2.weapon:
        print(f'Differing weapon: {gs1.weapon} != {gs2.weapon}')
    if gs1.armor != gs2.armor:
        print(f'Differing armor: {gs1.armor} != {gs2.armor}')
    if gs1.spellbook != gs2.spellbook:
        print(f'Differing spellbook: {gs1.spellbook} != {gs2.spellbook}')
    if gs1.bonus_atk != gs2.bonus_atk:
        print(f'Differing ATK bonus: {gs1.bonus_atk} != {gs2.bonus_atk}')
    if gs1.items != gs2.items:
        print(f'Differing items: {gs1.items} != {gs2.items}')
    if gs1.rolling_boulders != gs2.rolling_boulders:
        print(f'Differing rolling boulders: {gs1.rolling_boulders} != {gs2.rolling_boulders}')
    if gs1.shop_id != gs2.shop_id:
        print(f'Differing shop ID: {gs1.shop_id} != {gs2.shop_id}')
    if gs1.message != gs2.message:
        print(f'Differing message: {gs1.message} != {gs2.message}')
    if gs1.treasure_id != gs2.treasure_id:
        print(f'Differing treasure ID: {gs1.treasure_id} != {gs2.treasure_id}')
    if gs1.combat != gs2.combat:
        print(f'Differing combat: {gs1.combat} != {gs2.combat}')
    if gs1.trick != gs2.trick:
        print(f'Differing trick: {gs1.trick} != {gs2.trick}')
    if gs1.milestone != gs2.milestone:
        print(f'Differing milestone: {gs1.milestone} != {gs2.milestone}')
    if gs1.puzzle_step != gs2.puzzle_step:
        print(f'Differing puzzle_step: {gs1.puzzle_step} != {gs2.puzzle_step}')
    if gs1.hidden_triggers != gs2.hidden_triggers:
        print(f'Differing hidden_triggers: {gs1.hidden_triggers}\n!=\n{gs2.hidden_triggers}')
    if gs1.triggers_activated != gs2.triggers_activated:
        print(f'Differing triggers_activated: {gs1.triggers_activated}\n!=\n{gs2.triggers_activated}')
    if gs1.vanquished_enemies != gs2.vanquished_enemies:
        print(f'Differing vanquished_enemies: {gs1.vanquished_enemies}\n!=\n{gs2.vanquished_enemies}')
    if gs1.tile_overrides != gs2.tile_overrides:
        print(f'Differing tile_overrides: {gs1.tile_overrides}\n!=\n{gs2.tile_overrides}')
    if gs1.secrets_found != gs2.secrets_found:
        print(f'Differing secrets_found: {gs1.secrets_found} != {gs2.secrets_found}')
