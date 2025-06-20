from .entities import GameMilestone, GameMode, RewardItem, RewardTreasure
from .explore import enter_map, pos_for_move_action
from .js import atlas
from .logs import log, log_combat
from .mazemap import mazemap_is_exit
from .power import *

from .mod.hero import PARRY_ITEMS


def combat_logic(game_view, actions, _GameView):
    'Put next game states in actions dict, depending on player choices'
    game_state = game_view.state.clean_copy()
    game_state = game_state._replace(combat=game_state.combat.incr_round())
    _enemy = game_state.combat.enemy
    if _enemy.hp <= 0:
        next_gs = game_state.with_vanquished_enemy(game_state.coords)\
                            ._replace(mode=GameMode.EXPLORE, combat=None,
                                      bonus_atk=0, bonus_def=0)  # Temporary boosts stops after a combat
        if _enemy.post_victory and game_state.hp > 0:
            next_gs = _enemy.post_victory(next_gs, game_view) or next_gs
        actions['END-COMBAT-AFTER-VICTORY'] = _GameView(next_gs)
        return
    if game_state.combat.round > _enemy.max_rounds:
        log_combat(game_view)
        assert False, f'NO FUN ALERT: Combat against {_enemy.name} @ {game_state.coords} can last more than {_enemy.max_rounds} rounds: eHP={_enemy.hp} aHP={game_state.hp} MP={game_state.mp}'
    if game_state.combat.round == 0 and _enemy.allows_running_away:
        # We only allow ro run away on the very first round.
        # Reasons: Allowing to run away WHEN the combat starts generates NO extra states,
        #          and gives the player a "last chance" to change their mind,
        #          plus we can trick them later on with enemies that do not allow to run away!
        #          Allowing to run away AFTER the combat has started generates MANY extra states,
        #          and provides zero tectical benefit to the player.
        _map = atlas().maps[game_state.map_id]
        x, y = pos_for_move_action(game_state, 'MOVE-BACKWARD')
        next_state = game_state._replace(mode=GameMode.EXPLORE, combat=None, x=x, y=y, message='Backing off!')
        map_exit = mazemap_is_exit(_map, x, y)
        if map_exit:
            next_state = enter_map(next_state, map_exit)
        # Unlike the original game, running away "pushes back" the avatar 1 tile away.
        actions['RUN'] = _GameView(next_state)
    def get_action_names(action_name):  # return None if action is not available, else the final action name, that can be custom
        if not _enemy.custom_actions:
            return [action_name]
        return [cca.name for cca in _enemy.custom_actions if cca.name.startswith(action_name)]
    for action_name in get_action_names('ATTACK'):
        actions[action_name] = combat_round(power_hero_attack(game_state.with_combat_action(action_name)), _GameView)
    for parry_item_name in ('BUCKLER', 'SCEPTER'):
        if parry_item_name in game_state.items:
            for action_name in get_action_names(parry_item_name):
                actions[action_name] = combat_round(game_state.with_combat_action(action_name), _GameView, PARRY_ITEMS[parry_item_name])
    for bribe in _enemy.bribes:
        if bribe.item and bribe.item in game_state.items:
            assert bribe.item not in actions, f'Several bribes can be offered to {_enemy.name}@{game_state.coords} with the same item: {bribe.item}'
            for action_name in get_action_names(bribe.item):
                actions[action_name] = combat_bribe(game_state.with_combat_action(action_name), bribe, _GameView)
        elif bribe.gold and bribe.gold <= game_state.gold:
            assert 'THROW-COIN' not in actions, f'Several gold bribes can be offered {_enemy.name}@{game_state.coords} at the same time'
            for action_name in get_action_names('THROW-COIN'):
                actions[action_name] = combat_bribe(game_state.with_combat_action(action_name), bribe, _GameView)
    if game_state.combat.combat_round.run_away:
        # This is a hack, but we don't want to allow the player to stupidly loose a MP
        # if the enemy is running away anyway.
        # (this can happen when fighting goblin after druid in Death Walkaways)
        # We still display available spells though:
        if game_state.spellbook >= 1:
            actions['HEAL'] = None
        if game_state.spellbook >= 2:
            actions['BURN'] = None
        if game_state.spellbook >= 3:
            actions['UNLOCK'] = None
        return
    # Spells are only available if MP>=0 (and HP<max for HEAL).
    # Else they are displayed but do not generate a new state (= no link),
    # so insert them in "actions" with a None value.
    if game_state.spellbook >= 1:
        for action_name in get_action_names('HEAL'):
            actions[action_name] = combat_round(power_heal(game_state.with_combat_action(action_name)), _GameView)
    if game_state.spellbook >= 2:
        for action_name in get_action_names('BURN'):
            actions[action_name] = combat_round(power_burn(game_state.with_combat_action(action_name)), _GameView)
    if game_state.spellbook >= 3:
        for action_name in get_action_names('UNLOCK'):
            actions[action_name] = combat_round(power_unlock(game_state.with_combat_action(action_name)), _GameView)
    if 'CRUCIFIX' in game_state.items:
        for action_name in get_action_names('CRUCIFIX'):
            actions[action_name] = combat_round(item_crucifix(game_state.with_combat_action(action_name)), _GameView)
    if 'EMPTY_BOTTLE' in game_state.items:
        for action_name in get_action_names('EMPTY_BOTTLE'):
            actions[action_name] = combat_round(item_bottle(game_state.with_combat_action(action_name)), _GameView)
    if 'FULL_BOTTLE' in game_state.items:
        for action_name in get_action_names('FULL_BOTTLE'):
            actions[action_name] = combat_round(item_bottle(game_state.with_combat_action(action_name)), _GameView)
    if 'HOLY_WATER' in game_state.items:
        for action_name in get_action_names('HOLY_WATER'):
            actions[action_name] = combat_round(item_holy_water(game_state.with_combat_action(action_name)), _GameView)
    if 'SCEPTER' not in game_state.items and any(cca.name == 'TAKE_SCEPTER' for cca in _enemy.custom_actions):
        for action_name in get_action_names('TAKE_SCEPTER'):
            actions[action_name] = combat_round(take_scepter(game_state.with_combat_action(action_name)), _GameView)


def combat_round(game_state, _GameView, parry_item=None):
    'Hero attack has already been resolved, now performing enemy attack'
    if not game_state:
        return None
    game_state, extra_actions = power_enemy_attack(game_state, parry_item)
    if game_state.hp <= 0:
        game_state = game_state._replace(milestone=GameMilestone.GAME_OVER)
    elif game_state.combat.enemy.hp <= 0:
        game_state = combat_determine_reward(game_state)
    next_gv = _GameView(game_state)
    for action_name, next_state in extra_actions.items():
        if action_name in next_gv.actions:
            assert next_gv.actions[action_name].state == next_state
        else:
            next_gv.actions[action_name] = _GameView(next_state)
    return next_gv


def combat_bribe(game_state, bribe, _GameView):
    combat = game_state.combat
    bribe_name = ('a ' + bribe.item.replace('_', ' ').lower()) if bribe.item else f'{bribe.gold} gold'
    log(game_state, f'bribe attempt with {bribe_name}')
    if bribe.successful:
        combat = combat._replace(enemy=combat.enemy._replace(hp=0, gold=0, reward=None))
    # Note: using a central message instead of the left-side avatar_log to focus on this special situation:
    message = 'You offer'
    message += '\n' if len(bribe_name) >= 19 else ' '
    message += f'{bribe_name}.\n{bribe.result_msg}'
    game_state = game_state._replace(combat=combat,
                                     message=message,
                                     gold=game_state.gold - bribe.gold,
                                     items=tuple(i for i in game_state.items if i != bribe.item))
    if bribe.handshake:
        game_state = bribe.handshake(game_state)
    return _GameView(game_state)


def combat_determine_reward(game_state):
    'Replicates the JS function with same name'
    _enemy = game_state.combat.enemy
    assert not _enemy.invincible, f'{_enemy.name} @ {game_state.coords} should not have been vanquished!'
    log(game_state, f'  vanquished {_enemy.name} @ {game_state.coords}: gold+{_enemy.gold} rounds:{game_state.combat.round}'
                    f' hp={game_state.hp}/{game_state.max_hp} mp={game_state.mp}/{game_state.max_mp}')
    if _enemy.hidden_trigger:
        game_state = game_state.with_hidden_trigger(_enemy.hidden_trigger)
    msg = _enemy.victory_msg or 'Victory!'
    if _enemy.reward:
        assert not _enemy.gold, 'Not implemented yet'
        if isinstance(_enemy.reward, RewardItem):
            assert _enemy.reward.name == 'ARMOR_PART'  # if other values are possible, message must be made dynamic
            indent="                "
            return game_state._replace(
                items=game_state.items + (_enemy.reward.name,),
                message=(
                    f"{indent}{msg}\n"
                    f"{indent}You get a\n"
                    f"{indent}piece of\n"
                    f"{indent}armor"
                ),
                treasure_id=_enemy.reward.treasure_id)
        assert isinstance(_enemy.reward, RewardTreasure)
        return _enemy.reward.grant(game_state._replace(
            message=f"{msg}\n{_enemy.reward.message}",
            treasure_id=_enemy.reward.treasure_id))
    if _enemy.gold:
        msg += f"\n+{_enemy.gold} gold"
    return game_state._replace(
        message = game_state.message or msg,
        gold=game_state.gold + _enemy.gold)   # Original: round(random() * (gold_max - gold_min)) + gold_min
