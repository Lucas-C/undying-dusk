from math import floor

from .entities import CombatLog, CustomCombatAction, GameMode, Position, SFX
from .js import atlas, enemy, info
from .logs import log


def power_enemy_attack(game_state, parry_item=None):
    '''
    Modded function to make combats fully predictable
    Return: (next_state, extra_actions)
    '''
    combat = game_state.combat
    _round = combat.combat_round
    if _round.run_away:
        assert not (_round.ask_for_mercy or _round.miss or _round.atk or _round.hp_drain or _round.mp_drain or _round.heal or _round.boneshield_up)
        return game_state._replace(combat=combat._replace(enemy=combat.enemy._replace(hp=0, gold=0, reward=None),
                                                          avatar_log=CombatLog(action="Attack!", result="Dodged!")),
                                   message='The enemy ran away'), {}
    if _round.ask_for_mercy:
        assert not (_round.miss or _round.atk or _round.hp_drain or _round.mp_drain or _round.heal or _round.boneshield_up)
        assert combat.enemy.hp > 0, f'Dead enemies cannot ask for mercy: {game_state.coords} round={combat.round} eHP={combat.enemy.hp}'
        offer_msg, agreed_func = _round.ask_for_mercy
        next_state = game_state._replace(message=f'\n{offer_msg}')
        state_if_agreed = next_state._replace(combat=combat._replace(avatar_log=None,
                enemy=combat.enemy._replace(hp=0, gold=0, reward=None)))
        extra_actions = {'END-COMBAT-AFTER-VICTORY': agreed_func(state_if_agreed)}
        return next_state, extra_actions
    attack_damage, log_result = 0, ''
    if _round.miss:
        assert not (_round.atk or _round.hp_drain or _round.mp_drain or _round.heal or _round.boneshield_up)
        log_result = "Miss!"
    elif _round.mp_drain:
        assert not (_round.atk or _round.hp_drain or _round.heal or _round.boneshield_up)
        log_result = "-0 MP"
        if game_state.mp > 0:
            game_state = game_state._replace(mp=game_state.mp - 1)
            log_result = "-1 MP"
    elif _round.heal:
        new_hp = min(combat.enemy.hp + _round.heal, combat.enemy.max_hp)
        log_result = f"+{new_hp - combat.enemy.hp} HP"
        combat = combat._replace(enemy=combat.enemy._replace(hp=new_hp))
    elif _round.atk:
        armor_def = info().armors[game_state.armor]['def']
        attack_damage = max(1, _round.atk - armor_def)
        log_result = f"{attack_damage} damage"
        if parry_item:
            parry_outcome = True
            if parry_item.logic:
                parry_outcome = parry_item.logic(game_state, _round)
                if parry_outcome:
                    game_state = parry_outcome
                    combat = game_state.combat
                else:
                    combat = combat._replace(avatar_log=CombatLog(action='Parry', result='Inadequate!'))
        if parry_item and parry_outcome:
            log_result += ' avoided'
            parries = combat.parries + 1
            combat = combat._replace(parries=parries)
            if parries == parry_item.max_parries:
                game_state = game_state._replace(items=tuple(item for item in game_state.items if item != combat.action_name))
                # Notify the player about the broken parry item:
                combat = combat._replace(avatar_log=CombatLog(action=f'{combat.action_name} destroyed', result='(too many hits)'))
            elif parry_outcome is True:  # else is a GameState and parry_item.logic has already set avatar_log
                combat = combat._replace(avatar_log=CombatLog(action='Parry', result='Blocked!'))
        else:
            game_state = game_state._replace(hp=game_state.hp - attack_damage)
            if _round.hp_drain:
                new_hp = min(combat.enemy.hp + attack_damage, combat.enemy.max_hp)
                combat = combat._replace(enemy=combat.enemy._replace(hp=new_hp))
        if _round.boneshield_up:
            combat = combat._replace(boneshield_up=True)
    if combat.enemy.hp > 0 or log_result == "-1 MP" or _round.heal or attack_damage:
        # Minor rendering optim: not rendering final enemy log on combat victory page,
        # if avatar suffered no harm during this last round (makes flying_demon combat end better)
        combat = combat._replace(enemy_log=CombatLog(action=_round.attack_name, result=log_result))
    return game_state._replace(combat=combat), {}


def power_hero_attack(game_state):
    'Modded function to make combats fully predictable'
    combat = game_state.combat
    _round = combat.combat_round
    log_action = "Attack!"
    if _round.dodge:
        assert not _round.hero_crit  # we prevent wasted critical hit for now
        log_result = "Dodged!"
    elif combat.boneshield_up:
        # Replicates boss_boneshield_heroattack
        assert not _round.hero_crit  # we prevent wasted critical hit for now
        log_result = "Absorbed!"
    else:
        weapon = info().weapons[game_state.weapon]
        atk_min = weapon.atk_min + game_state.bonus_atk
        atk_max = weapon.atk_max + game_state.bonus_atk
        attack_damage = floor((atk_max + atk_min) / 2)
        # check crit: hero crits add max damage
        if _round.hero_crit:
            attack_damage *= 2
            log_action = "Critical hit!"
        if combat.enemy.withstand_logic:
            game_state, log_result = combat.enemy.withstand_logic(game_state, attack_damage)
            combat = game_state.combat
        else:
            combat = combat._replace(enemy=combat.enemy._replace(hp=combat.enemy.hp - attack_damage))
            log_result = f"{attack_damage} damage"
    combat = combat._replace(avatar_log=CombatLog(action=log_action, result=log_result))
    return game_state._replace(combat=combat)


def power_heal(game_state):
    'Modded function to make spell fully predictable'
    max_hp = game_state.max_hp  # Note: always 25 or 30 (with emerald)
    if game_state.mp == 0 or game_state.hp == max_hp:
        return None
    heal_amount, log_action = 20, 'Cast "Heal"'  # Original: floor(max_hp / 2) + floor(random() * max_hp / 2)
    new_hp = min(game_state.hp + heal_amount, max_hp)
    log(game_state, f"HEAL+{heal_amount}: hp={new_hp}/{max_hp}")
    game_state = game_state._replace(hp=new_hp, mp=game_state.mp - 1)
    assert game_state.mode == GameMode.COMBAT
    combat = game_state.combat._replace(avatar_log=CombatLog(action=log_action, result=f"+{heal_amount} HP"))
    return game_state._replace(combat=combat, sfx=SFX(id=9, pos=Position(64, 2)))


def power_burn(game_state, next_pos_facing=None, next_tile_facing=None):
    'Modded function to make spell fully predictable'
    if game_state.mp == 0:
        return None
    if game_state.mode == GameMode.COMBAT:
        combat = game_state.combat
        _enemy, _round = combat.enemy, combat.combat_round
        attack_damage, log_action = 0, 'Cast "Burn"'
        if _round.dodge:
            assert not _round.hero_crit
            log_result = "Miss!"
        else:
            attack_damage = 8  # as much as the Steel Sword. Original logic: base damage = weapon damage
            if _enemy.category == enemy().ENEMY_CATEGORY_UNDEAD:
                attack_damage *= 2  # damages are doubled against undeads
            elif _enemy.category == enemy().ENEMY_CATEGORY_DEMON:
                attack_damage //= 2  # damages are halved against demons
            if _round.hero_crit:
                attack_damage *= 2  # damages are doubled in case of a critical hit
                log_action = "Critical " + log_action
            if combat.enemy.withstand_logic:
                game_state, log_result = combat.enemy.withstand_logic(game_state, attack_damage)
                combat = game_state.combat
            else:
                combat = combat._replace(enemy=combat.enemy._replace(hp=combat.enemy.hp - attack_damage))
                log_result = f"{attack_damage} damage"
        combat = combat._replace(avatar_log=CombatLog(action=log_action, result=log_result), boneshield_up=False)
        game_state = game_state._replace(combat=combat)
        log(game_state, f"BURN: {attack_damage} damage")
    else:
        assert game_state.mode == GameMode.EXPLORE and next_pos_facing and next_tile_facing
        next_coords_facing = (game_state.map_id, *next_pos_facing)
        next_tile_override = game_state.tile_override_at(next_coords_facing)
        if next_tile_override:
            assert next_tile_override == next_tile_facing
            game_state = game_state.without_tile_override(next_coords_facing)
        _map = atlas().maps[game_state.map_id]
        next_x, next_y = next_pos_facing
        if _map.tiles[next_y][next_x] not in (1, 5):  # initial bone pile/box position, or box over opened chest -> masking it
            empty_tile_id = {16: 5, 33: 5, 36: 1}[next_tile_facing]
            game_state = game_state.with_tile_override(empty_tile_id, next_coords_facing)
        game_state = game_state._replace(message="Burn!\nPath cleared", mode=GameMode.EXPLORE)
        log(game_state, f"BURN tile {next_tile_facing} @ {next_coords_facing}")
    return game_state._replace(mp=game_state.mp - 1, sfx=SFX(id=10, pos=Position(64, 44)))


def power_unlock(game_state, next_pos_facing=None):
    'Modded function to make spell fully predictable'
    if game_state.mp == 0:
        return None
    if game_state.mode == GameMode.COMBAT:
        combat = game_state.combat
        _enemy, _round = combat.enemy, combat.combat_round
        attack_damage, log_action = 0, 'Cast "Unlock"'
        if _round.dodge:
            assert not _round.hero_crit
            log_result = "Miss!"
        else:
            if _enemy.category == enemy().ENEMY_CATEGORY_AUTOMATON:
                attack_damage = 100
            if _round.hero_crit:
                attack_damage *= 2  # damages are doubled in case of a critical hit
                log_action = "Critical " + log_action
            if combat.enemy.withstand_logic:
                game_state, log_result = combat.enemy.withstand_logic(game_state, attack_damage)
                combat = game_state.combat
            else:
                combat = combat._replace(enemy=combat.enemy._replace(hp=combat.enemy.hp - attack_damage))
                log_result = f"{attack_damage} damage"
        combat = combat._replace(avatar_log=CombatLog(action=log_action, result=log_result))
        game_state = game_state._replace(combat=combat, sfx=SFX(id=11, pos=Position(64, 4)))
        log(game_state, f"UNLOCK: {attack_damage} damage")
    else:
        assert game_state.mode == GameMode.EXPLORE and next_pos_facing  # assume target tile is locked_door
        new_tile_id = 3  # dungeon door
        coords = (game_state.map_id, *next_pos_facing)
        game_state = game_state.with_tile_override(new_tile_id, coords)
        game_state = game_state._replace(message="Unlock!\nDoor Opened!", mode=GameMode.EXPLORE, sfx=SFX(id=11, pos=Position(64, 46)))
        log(game_state, f"UNLOCK locked door @ {coords}")
    return game_state._replace(mp=game_state.mp - 1)


def item_crucifix(game_state):
    combat = game_state.combat._replace(avatar_log=CombatLog(action="throw crucifix", result="enemy dodged it"))
    new_items = tuple(item for item in game_state.items if item != 'CRUCIFIX')
    return game_state._replace(combat=combat, items=new_items)


def item_bottle(game_state):
    'No effect - Same when using EMPTY_BOTTLE or FULL_BOTTLE'
    new_items = tuple(item for item in game_state.items if item not in ('EMPTY_BOTTLE', 'FULL_BOTTLE'))
    return game_state._replace(combat=game_state.combat._replace(avatar_log=CombatLog(action="throw bottle", result="no effect")), items=new_items)


def item_holy_water(game_state):
    'New single use item designed for the mod!'
    action, attack_damage = "throw holy water", 20
    _enemy = game_state.combat.enemy
    if _enemy.category == enemy().ENEMY_CATEGORY_DEMON:
        avatar_log = CombatLog(action=action, result=f"{attack_damage} damage")
        _enemy = _enemy._replace(hp=_enemy.hp - attack_damage)
    else:
        avatar_log = CombatLog(action=action, result="no effect")
    combat = game_state.combat._replace(enemy=_enemy, avatar_log=avatar_log)
    new_items = tuple(item for item in game_state.items if item != 'HOLY_WATER')
    return game_state._replace(combat=combat, items=new_items)


def take_scepter(game_state):
    combat = game_state.combat
    assert 'TAKE_SCEPTER' in combat.enemy.custom_actions_names
    new_custom_actions = tuple(cca for cca in combat.enemy.custom_actions if cca.name != 'TAKE_SCEPTER')
    new_custom_actions += (CustomCombatAction('SCEPTER'),)
    return game_state._replace(combat=combat._replace(avatar_log=CombatLog(action="scepter taken", result=''),
                                                      enemy=combat.enemy._replace(custom_actions=new_custom_actions)),
                               items=game_state.items + ('SCEPTER',))
