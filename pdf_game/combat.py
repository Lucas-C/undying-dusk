from .entities import GameMilestone, GameMode, RewardItem, RewardTreasure
from .explore import enter_map, pos_for_move_action
from .js import atlas
from .logs import log, log_combat
from .mazemap import mazemap_is_exit
from .power import *


def combat_logic(game_view, actions, _GameView):
    'Put next game states in actions dict, depending on player choices'
    game_state = game_view.state.clean_copy()
    _enemy = game_state.combat.enemy
    if _enemy.hp <= 0:
        next_gs = game_state.with_vanquished_enemy(game_state.coords)\
                            ._replace(mode=GameMode.EXPLORE, combat=None,
                                      bonus_atk=0, bonus_def=0)  # Temporary boosts stops after a combat
        if game_state.combat.enemy.post_victory and game_state.hp > 0:
            next_gs = game_state.combat.enemy.post_victory(next_gs) or next_gs
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
    actions['ATTACK'] = combat_round(power_hero_attack(game_state), _GameView)
    if 'BUCKLER' in game_state.items:
        next_gs, parried = power_hero_parry(game_state, 'BUCKLER')
        actions['BUCKLER'] = combat_round(next_gs, _GameView, parried=parried)
    for bribe_item in _enemy.bribes:
        if bribe_item in game_state.items:
            actions[bribe_item] = combat_bribe(game_state, bribe_item, _GameView)
        elif bribe_item.endswith('_gold'):
            gold_amount = int(bribe_item.split('_')[0])
            actions['THROW-COIN'] = combat_bribe(game_state, bribe_item, _GameView, gold_amount) if gold_amount <= game_state.gold else None
    if _is_enemy_running_away(game_state.combat):
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
        actions['HEAL'] = combat_round(power_heal(game_state), _GameView)
    if game_state.spellbook >= 2:
        actions['BURN'] = combat_round(power_burn(game_state), _GameView)
    if game_state.spellbook >= 3:
        actions['UNLOCK'] = combat_round(power_unlock(game_state), _GameView)
    if 'CRUCIFIX' in game_state.items:
        actions['CRUCIFIX'] = combat_round(item_crucifix(game_state), _GameView)
    if 'EMPTY_BOTTLE' in game_state.items:
        actions['EMPTY_BOTTLE'] = combat_round(item_empty_bottle(game_state), _GameView)
    if 'HOLY_WATER' in game_state.items:
        actions['HOLY_WATER'] = combat_round(item_holy_water(game_state), _GameView)


def _is_enemy_running_away(combat):
    enemy_rounds = combat.enemy.rounds
    _round = enemy_rounds[combat.round % len(enemy_rounds)]
    return _round.run_away


def combat_round(game_state, _GameView, parried=False):
    'Hero attack has already been resolved, now performing enemy attack'
    if not game_state:
        return None
    game_state, extra_actions = power_enemy_attack(game_state, parried=parried)
    if game_state.hp <= 0:
        game_state = game_state._replace(milestone=GameMilestone.GAME_OVER)
    elif game_state.combat.enemy.hp <= 0:
        game_state = combat_determine_reward(game_state)
    combat = game_state.combat
    next_gv = _GameView(game_state._replace(combat=combat._replace(round=combat.round + 1)))
    for action_name, next_state in extra_actions.items():
        if action_name in next_gv.actions:
            assert next_gv.actions[action_name].state == next_state
        else:
            next_gv.actions[action_name] = _GameView(next_state)
    return next_gv


def combat_bribe(game_state, bribe_item, _GameView, gold_amount=None):
    combat = game_state.combat
    log(game_state, f'bribed with {bribe_item}')
    msg = f'You offer {bribe_item.replace("_", " ").lower()}\nThe enemy runs away with it'
    combat = combat._replace(enemy=combat.enemy._replace(hp=0, gold=0, reward=None), round=combat.round + 1)
    return _GameView(game_state._replace(combat=combat, message=msg,
                                         gold=game_state.gold - gold_amount if gold_amount else game_state.gold,
                                         items=tuple(i for i in game_state.items if i != bribe_item)))


def combat_determine_reward(game_state):
    'Replicates the JS function with same name'
    _enemy = game_state.combat.enemy
    assert not _enemy.invincible, f'{_enemy.name} @ {game_state.coords} should not have been vanquished!'
    log(game_state, f'  vanquished {_enemy.name} @ {game_state.coords}: gold+{_enemy.gold} rounds:{game_state.combat.round}'
                    f' hp={game_state.hp}/{game_state.max_hp} mp={game_state.mp}/{game_state.max_mp}')
    if _enemy.hidden_trigger:
        game_state = game_state.with_hidden_trigger(_enemy.hidden_trigger)
    msg = 'Victory!'
    if _enemy.reward:
        assert not _enemy.gold, 'Not implemented yet'
        if isinstance(_enemy.reward, RewardItem):
            return game_state._replace(
                items=game_state.items + (_enemy.reward.name,),
                message=f"{msg}\nYou get a\n{_enemy.reward.name.replace('_', ' ')}",
                treasure_id=_enemy.reward.treasure_id)
        assert isinstance(_enemy.reward, RewardTreasure)
        return _enemy.reward.grant(game_state._replace(
            message=f"{msg}\n{_enemy.reward.message}",
            treasure_id=_enemy.reward.treasure_id))
    if _enemy.gold:
        msg += f"\n+{_enemy.gold} gold"
    return game_state._replace(
        message = game_state.message or msg,
        gold=game_state.gold + _enemy.gold,   # Original: round(random() * (gold_max - gold_min)) + gold_min
            combat=game_state.combat._replace(gold_treasure=_enemy.gold))
