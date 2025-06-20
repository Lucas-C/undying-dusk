# pylint: disable=chained-comparison,inconsistent-return-statements,too-many-lines
from ..ascii import map_as_string
from ..bitfont import bitfont_color_red, bitfont_render, bitfont_set_color_red, Justify
from ..entities import Bribe, CustomCombatAction as CCA, Checkpoint, CombatRound as CR, MessagePlacement, Position, RewardItem, RewardTreasure, SFX, Trick
from ..js import REL_RELEASE_DIR
from ..logs import log, log_combat, log_path_to
from ..mapscript import *
from ..render import render_bar
from ..render_utils import add_link, portrait_render, white_arrow_render
from ..render_treasure import treasure_render_item
from ..warp_portals import warp_portal_add

from .scenes import abyss_bottom, risking_it_all, seamus_through_small_window, the_end, BASE_MUSIC_URL
from .world import is_instinct_preventing_to_enter_village, is_instinct_preventing_to_pass_mausoleum_portal, is_instinct_preventing_to_pass_village_portal, BOX_MIMIC_POS, DOOR_MIMIC_POS, MAUSOLEUM_PORTAL_COORDS, MAUSOLEUM_EXIT_COORDS, VILLAGE_INN_COORDS

EMPRESS_INTERPHASE_LINES = (
    'Nooooo!',
    'Come back to help me\nDominik!',
)

VICTORY_POS = Checkpoint((9, 11, 5), 'Victory screen after beating the Empress & final ending scene')
CHECKPOINTS = (  # intermediate positions that should be reachable through a unique path only
    # Checkpoint((1, 6, 6), 'Entering Monastery after Scriptorium'),
    Checkpoint((1, 4, 9),   'After beating the imp, still in Monastery'),
    Checkpoint((5, 3, 1),   'Entering Cedar Village'),
    Checkpoint((6, 4, 3),   'Entering Zuruth Plains, after beating zombie'),
    Checkpoint((10, 2, 1),  'Entering Templar Academy with the BURN spell',
                            condition=lambda gs: gs.mp >= 2 and gs.spellbook >= 2),
    Checkpoint((10, 2, 8),  'After beating the druid in the Academy'),
    Checkpoint((10, 1, 13), 'Before the chest behind boulder in the Academy'),
    Checkpoint((6, 11, 7),  'About to face Skeleton, rested, with Great Sword',
                            condition=lambda gs: gs.weapon >= 7 and gs.hp == gs.max_hp),
    Checkpoint((7, 2, 5),   'Canal Boneyard entrance'),
    Checkpoint((7, 9, 5),   'After beating zombie on Canal Boneyard exit'),
    # Checkpoint((8, 5, 7),   'Mausoleum, about to pass portcullis'),
    Checkpoint((8, 10, 11), 'Mausoleum, after bribing goblin'),
    Checkpoint((8, 4, 12),  'Mausoleum, after opening door with blue key'),
    Checkpoint((5, 9, 4),   'back to Cedar Village'),
    Checkpoint((8, 3, 12),  'back to Mausoleum with full HP & UNLOCK spell'),
    Checkpoint((5, 9, 4),   'back again to Cedar Village'),
    # Checkpoint((4, 10, 14), 'after beating the Shadow Soul -> secret',
                            # condition=lambda gs: 'BEEN_TO_VILLAGE' in gs.hidden_triggers),
    # Checkpoint((5, 3, 1),   'back to Cedar Village after finding dead tree secret'),
    Checkpoint((8, 14, 7),  'Mausoleum exit before dragon, with strong armor & iron gate raised',
                            condition=lambda gs: gs.armor > 1 and gs.tile_override_at(MAUSOLEUM_EXIT_COORDS)),
    Checkpoint((9, 2, 5),   'Dead Walkways entrance, after beating dragon'),
    Checkpoint((9, 5, 5),   'after passing 1st Dead Walkways arch'),
    Checkpoint((9, 8, 2),   'after passing 2nd Dead Walkways arch',
                            condition=lambda gs: 'BUCKLER' in gs.items),
    Checkpoint((9, 9, 3),   'after flying demon fight, about to face Empress'),
    Checkpoint((9, 11, 5),  'start of phase 2 of Empress boss fight', mode=GameMode.COMBAT,
                            condition=lambda gs: gs.message == EMPRESS_INTERPHASE_LINES[-1]),
    Checkpoint((9, 11, 5), 'Ending scene after beating the Empress', mode=GameMode.DIALOG),
    VICTORY_POS,
)
# VICTORY_POS = Checkpoint((0, 1, 1), ''); CHECKPOINTS = (VICTORY_POS,)  # stop after intro
# VICTORY_POS = Checkpoint((2, 3, 2), ''); CHECKPOINTS = (VICTORY_POS,)  # stop after leaving cell
# VICTORY_POS = Checkpoint((2, 1, 2), ''); CHECKPOINTS = (VICTORY_POS,)  # stop after beating Scriptorium sokoban
# VICTORY_POS = Checkpoint((3, 2, 3), ''); CHECKPOINTS = (VICTORY_POS,)  # stop after beating Shadow Tendrils

ENEMY_CATEGORY_BEAST = 4  # new category, 1s unused integer among original ENEMY_CATEGORY_* constants
PORTCULLIS_MUSIC_BTN_POS = Position(x=72, y=55)
ROTATING_LEVER_CORRECT_SEQUENCE = 402  # south-north-east


def script_it():
    # For portals test map:
    # warp_portal_add(0, (2, 1), 'north', (5, 6), 'south')
    # warp_portal_add(0, (2, 6), 'south', (5, 1), 'north')
    # warp_portal_add(0, (0, 4), 'west', (7, 4), 'west')
    def _start_game(game_view, _):
        game_view.add_tile_override(3, coords=(4, 10, 15))  # unlocking door to Cedar Village
    mapscript_add_trigger((0, 1, 2), _start_game)

    #---------------------------
    # Entering: Monastery (maps: 0, 1, 2 & 3)
    #---------------------------
    # The heroine starts with 25/25 HP, 1/1 MP and their Bare Fists, doing 2 damages.
    def _talk_to_seamus(game_view, _GameView):
        log(game_view.state, 'talking-to-Seamus')
        new_game_view = _GameView(game_view.state._replace(mode=GameMode.DIALOG,
                                                           shop_id=seamus_through_small_window().id))
        new_game_view.add_hidden_trigger('TALKED_TO_SEAMUS')
        game_view.actions['TALK'] = new_game_view
    mapscript_add_trigger((2, 3, 3), _talk_to_seamus, facing='south', permanent=True,
                                     condition=lambda gs: 'TALKED_TO_SEAMUS' not in gs.hidden_triggers)

    def _rearrange_scriptorium_boxes(game_view, _):  # Sleight of hand to reduce the branching paths:
        if 'TALKED_TO_SEAMUS' not in game_view.state.hidden_triggers:
            game_view.add_hidden_trigger('TALKED_TO_SEAMUS')
        if game_view.tile_override((2, 2, 1)) == 33:
            game_view.remove_tile_override((2, 2, 1))
            game_view.add_tile_override(5, (2, 2, 1))
            assert game_view.tile_override((2, 2, 3)) == 5
            game_view.remove_tile_override((2, 2, 3))
            game_view.add_tile_override(33, (2, 2, 3))
        assert game_view.tile_override((2, 2, 1)) == 5
        assert game_view.tile_override((2, 2, 3)) == 33
    mapscript_add_trigger((1, 6, 6), _rearrange_scriptorium_boxes)

    mapscript_remove_chest((2, 1, 1))  # Wood stick is now in the well
    def _examine_well(game_view, _GameView):
        game_view.actions['EXAMINE'] = _GameView(game_view.state._replace(message='You find a wooden stick\ndown in the well', msg_place=MessagePlacement.UP, treasure_id=10, weapon=1))
    mapscript_add_trigger((1, 2, 6), _examine_well, facing='west', condition=lambda gs: gs.weapon == 0, permanent=True)
    mapscript_add_trigger((1, 1, 5), _examine_well, facing='south', condition=lambda gs: gs.weapon == 0, permanent=True)
    mapscript_add_trigger((1, 1, 7), _examine_well, facing='north', condition=lambda gs: gs.weapon == 0, permanent=True)

    # Protects the HEAL spell; required to win: Wood Stick (4 damages)
    mapscript_add_enemy((3, 2, 3), 'shadow_tendrils',
        hp=7, gold=1, rounds=(
            CR('Tentacle hit', atk=5),
            CR('Tentacle hit', atk=7),
            CR('Tentacle hit', atk=6),
            CR('Tentacle hit', atk=8),
        ), # at the end of the combat, hero has 13 HP
        post_defeat=render_monastery_post_defeat_hint)

    # Block access to the Monastery exit; required to win: Wood Stick (4 damages) + HEAL spell
    mapscript_add_enemy((1, 4, 8), 'imp',
        hp=8, gold=2, rounds=(
            CR('Trident slash', atk=10),
            CR('Trident thrust', atk=15),  # without HEAL spell, hero must dies on 2nd round
            CR('Horn strike', atk=7),
        ), # at the end of the combat, hero has 1 HP
        post_defeat=render_monastery_post_defeat_hint)

    #---------------------------
    # Entering: Monastery Trail (map: 4 - checkpoint)
    #---------------------------
    # The heroine now has 1/25 HP, 0/1 MP & the HEAL spell and does 4 damages with their stick.
    # There are 2 enemies blocking each path to the village entrance.
    # It must be evident that the Shadow Soul is too strong to be beaten now.
    # It can however be bypassed through the forest to access the chest behind it.
    # The imp can be beaten, but only once the holy water has been crafter at the well.

    mapscript_add_message((4, 6, 2), 'The Monastery doors\nare locked', facing='north')
    # The door is closed by mod.world:patched_can_move_to
    mapscript_add_message((4, 9, 3), 'The whispering wind\ntells you of hidden\npassages in the forest', facing='east')
    mapscript_add_message((4, 3, 9), 'The whispering wind\ntells you that demons\nfear blessed liquids', facing='west')

    def whisper_about_monk(game_view, _GameView):
        gs = game_view.state
        if gs.weapon != 1: return
        if 'CRUCIFIX_STOLEN' in gs.hidden_triggers:
            game_view.state = gs._replace(message='The whispering wind\nis saddened by\nthe fate of the monk')
        else:
            game_view.state = gs._replace(message='The whispering wind\nis pleased the monk is safe\n')
    mapscript_add_trigger((4, 9, 14), whisper_about_monk, facing='west', permanent=True)

    def _examine_forest_well(game_view, _GameView):
        gs = game_view.state
        if 'CRUCIFIX' in gs.items:
            game_view.actions['CRUCIFIX'] = _GameView(gs.with_hidden_trigger('HOLY_WELL')
                                                        ._replace(message='SPLASH!',
                                                                  items=tuple(i for i in gs.items if i != 'CRUCIFIX')))
        if 'EMPTY_BOTTLE' in gs.items:
            if 'HOLY_WELL' in gs.hidden_triggers:
                new_game_state = gs._replace(message='You fill the bottle\nwith holy water.',
                                             msg_place=MessagePlacement.UP,
                                             items=tuple(i for i in gs.items if i != 'EMPTY_BOTTLE') + ('HOLY_WATER',),
                                             treasure_id=22)
            elif 'CRUCIFIX' in gs.items:
                # This prevent a case where the monk won't bless the water, because we stole the crucifix,
                # and we could not bless a bottle already full of water from the well:
                new_game_state = gs._replace(message='Better fill it\nwith holy water',
                                             msg_place=MessagePlacement.UP)
            else:
                new_game_state = gs._replace(message='You fill the bottle\nwith water.',
                                             msg_place=MessagePlacement.UP,
                                             items=tuple(i for i in gs.items if i != 'EMPTY_BOTTLE') + ('FULL_BOTTLE',),
                                             treasure_id=43)
            game_view.actions['EMPTY_BOTTLE'] = _GameView(new_game_state)
    mapscript_add_trigger((4, 3, 2), _examine_forest_well, facing='west', permanent=True)

    def _grant_empty_bottle(game_view, _):  # placed on a stump in the forest, near the Shadow Soul
        game_view.state = game_view.state._replace(message="Empty bottle found",
                                                   items=game_view.state.items + ('EMPTY_BOTTLE',))
    mapscript_add_chest((4, 11, 9), 34, _grant_empty_bottle)

    # Block access to the village entrance at first, then to a SECRET; required to win: St Knight armor (def 12), a Great Sword (13 dmg), 0 MP & 15 HP
    shadow_soul_stats = dict(
        hp=53, rounds=(
            CR('Magic drain', mp_drain=True),
            CR('Magic pump', mp_drain=True),
            CR('Magic suck', mp_drain=True),
            CR('Critical blast!', atk=20),  # => 7 dmg with St Knight armor
            CR('Critical blast!', atk=17),  # => 5 dmg with St Knight armor
        ))
    mapscript_add_enemy((4, 9, 9), 'shadow_soul', **shadow_soul_stats,
                        condition=lambda gs: 'BEEN_TO_VILLAGE' not in gs.hidden_triggers)

    # Block access to the village entrance; required to win: holy water bottle
    mapscript_add_enemy((4, 7, 10), 'imp',
        hp=13, gold=2, rounds=(
            CR('Horn strike', atk=4),
            CR('Trident slash', atk=6),
            CR('Trident feint', atk=5, dodge=True),
        ))

    #---------------------------
    # Entering: Cedar village (map: 5 - checkpoint)
    #---------------------------
    # The heroine now has 2/30 HP, 0/1 MP & the HEAL spell and does 4 damages with their stick.
    # When the hero enters the village, the Shadow Soul moves closest to the door at the end of the trail,
    # so that the player MUST face it if they want to come back:
    def _enter_cedar_village(game_view, _):
        game_view.state = clear_hidden_triggers(game_view.state)  # removes CRUCIFIX_STOLEN & HOLY_WELL
        game_view.add_hidden_trigger('BEEN_TO_VILLAGE')
        game_view.add_tile_override(29, coords=(4, 10, 11))  # dead tree
        game_view.add_tile_override(12, coords=(4, 9, 11))   # tree
        game_view.remove_tile_override((4, 10, 15))  # locking door to Cedar Village
    mapscript_add_trigger((5, 3, 1), _enter_cedar_village)
    mapscript_add_enemy((4, 10, 14), 'shadow_soul', **shadow_soul_stats, gold=3,
                        intro_msg="The shadow soul locks\nthe door behind you.",
                        condition=lambda gs: 'BEEN_TO_VILLAGE' in gs.hidden_triggers)
    # Beating this enemy can only be done at the end of the campaign, and gives access to a SECRET in front of the dead tree:
    def _facing_dead_tree(game_view, _GameView):
        if game_view.state.armor <= 1:
            log_combat(game_view)
            assert False, 'Hero should have the St Knight armor to beat the Shadow Soul'
        msg = 'The dead tree whispers:\n"May the forest spirits\nstrengthen your arm\nin the fights to come"\n(you found a SECRET)'
        music = BASE_MUSIC_URL + 'TomaszKucza-10MysteriesOfTheMechanicalPrince.mp3'
        btn_pos = Position(x=40, y=12)
        game_view.actions['LIGHT'] = _GameView(game_view.state.with_secret('DEAD_TREE')
                                                        # opening locked door to Cedar Village:
                                                        # .without_tile_override((4, 10, 15))   unlock by spell
                                                        ._replace(message=msg, hp=15, mp=1,  # restoring HP
                                                                  music=music, music_btn_pos=btn_pos))
    mapscript_add_trigger((4, 10, 12), _facing_dead_tree, facing='north', permanent=True,
                                       condition=lambda gs: 'BEEN_TO_VILLAGE' in gs.hidden_triggers and 'DEAD_TREE' not in gs.secrets_found)

    # A boulder blocks access to a chest with 10 gold.
    # It can be avoided by moving backward back to the street the player comes from.
    mapscript_add_message((5, 2, 3), 'DANGER!\nBeware rock slides', msg_place=MessagePlacement.UP)  # sign
    mapscript_add_boulder(trigger_pos=(5, 3, 10), start_at=(5, 5, 10), _dir='west')

    # Available shops:
    # - The Pilgrim Inn:        room to rest for the night = 10$
    # REPLACED ones:
    # - Cedar Arms:             Iron Knife   (5 dgt) for 50$ / Bronze Mace  (7 dgt) for 200$
    # - Simmons Fine Clothier:  Travel Cloak (def 4) for 50$ / Hide Cuirass (def 6) for 200$
    # - Sage Therel             learn Burn spell for 100$
    # NEW ones: (defined in mod.world:*Sellable* classes)
    # - Cedar Arms:             make a great sword out of a rusty sword for 50$ / rumor about a secret in Zuruth Plains for free
    # - Simmons Fine Clothier:  boots to pass over shallow waters for 15$ / St Knight armor from armor parts
    # - Sage Therel             teach BURN spell in exchange for the scroll / teach UNLOCK spell later on, again in exchange for a scroll


    # Block exit to the plains; required to win: a night of rest
    def _post_1st_zombie_fight(gs, _):
        assert gs.hp == 8 and not gs.mp, gs
        return gs.with_tile_override(1, (6,15,7))
    mapscript_add_enemy((5, 9, 10), 'zombie',
        hp=5, gold=3, rounds=(                 # best moves:
            CR('Critical thump!', atk=20),     # ATTACK -> hero HP=10 | zombie HP=1
            CR('Bite  +7hp', atk=7, hp_drain=True),  # HEAL   -> hero HP=23 | zombie HP=8
            CR('Blow', atk=6),                 # ATTACK -> hero HP=17 | zombie HP=4
            CR('Punch', atk=9),                # ATTACK -> hero HP=8  | zombie HP=0
        ), post_victory=_post_1st_zombie_fight)

    #---------------------------
    # Entering: Zuruth Plains (map: 6 - checkpoint)
    #---------------------------
    # The heroine has 8/30 HP, 0/1 MP, 5 gold, the HEAL spells and does 4 damages with their stick.

    # We limit the #states by cutting unneeded access to the village,
    # and use this opportunity to provide hints:
    def _village_door_hint(game_view, _):
        gs = game_view.state
        if not is_instinct_preventing_to_enter_village(gs): return
        if not gs.tile_override_at((6, 1, 9)):
            msg = 'The whispering wind\ntells you to look for Seamus\nbefore returning'
        elif gs.mp >= 2 and gs.spellbook < 2:
            msg = 'The whispering wind\nadvises you to look behind\nthe ivy before returning'
        elif 'SCROLL' in gs.items:
            if 'AMULET' in gs.items:
                msg = 'The whispering wind\nrecommends you to use this\namulet before returning'
            else:
                msg = 'The whispering wind\ntells you to search the canal\nfor an amulet before returning'
        else:
            msg = "The whispering wind\ntells you to follow\nSeamus's advice\nbefore returning"
        assert msg, 'A hint should be given if the path is blocked'
        game_view.state = gs._replace(message=msg)
    mapscript_add_trigger((6, 4, 3), _village_door_hint, facing='north', permanent=True)

    # Entrance to Canal Boneyard is blocked by a skeleton; required to win: full HP + 3 MP (1 BURN & 2 HEAL) + great sword (13 dmg)
    def skeleton_enemy_frame(combat):
        if combat.enemy.hp > 0:
            return combat.round + 1
        if combat.action_name == 'BURN':
            return 9
        return 8
    mapscript_add_enemy((6, 12, 7), 'skeleton',
        # STRATEGY to beat him: wait until 5th turn for an opportunity to launch BURN spell with a critical
        hp=58, gold=9, max_rounds=6, rounds=(            # best moves:
            CR('Sword thrust', atk=14),                  # ATTACK         -> hero HP=16 | skeleton HP=45
            CR('Sword slash', atk=12),                   # ATTACK         -> hero HP=4  | skeleton HP=32
            CR('Sword thrust', atk=14),                  # HEAL           -> hero HP=10 | skeleton HP=32
            CR('Sword slash', atk=12),                   # HEAL           -> hero HP=18 | skeleton HP=32
            CR('Sword thrust', atk=14, hero_crit=True),  # CRITICAL BURN! -> hero HP=4  | skeleton HP=0
        ), music=BASE_MUSIC_URL + 'MatthewPablo-DarkDescent.mp3',
        post_victory=lambda gs, _: gs._replace(mode=GameMode.DIALOG, shop_id=risking_it_all().id),
        enemy_frame=skeleton_enemy_frame)

    # An invisible chest is hidden behind a wall with ivy, behind a pillar:
    def _grant_scroll(game_view, _):
        if 'SCROLL' in game_view.state.items or game_view.state.spellbook >= 2:
            return False
        game_view.state = game_view.state._replace(message='You found\nan ancient scroll',
                                                   items=game_view.state.items + ('SCROLL',))
    mapscript_add_chest((6, 3, 15), 23, _grant_scroll)

    def _amulet_trail(game_view, _):
        game_view.state = game_view.state._replace(
                extra_render=lambda pdf: pdf.image('assets/water-trail.png', x=0, y=86))
    mapscript_add_trigger((6, 12, 4), _amulet_trail, facing='east', permanent=True,
                                      condition=lambda gs: 'AMULET' not in gs.items and gs.max_mp == 1)
    def _amulet_sight(game_view, _GameView):
        game_view.state = game_view.state._replace(
                extra_render=lambda pdf: pdf.image('assets/water-trail.png', x=97, y=86))
        game_view.actions['GLIMPSE'] = _GameView(game_view.state._replace(
                message='You found a dull amulet\ndrifting in the canal water',
                msg_place=MessagePlacement.UP,
                treasure_id=35, items=game_view.state.items + ('AMULET',)))
    mapscript_add_trigger((6, 12, 3), _amulet_sight, facing='east', permanent=True,
                                      condition=lambda gs: 'AMULET' not in gs.items and gs.max_mp == 1)

    # Getting the templar statue blessing (+2 MP) is needed in order to be able to launch the BURN spell
    # and get rid of the 2 bone piles in the Templar Academy
    def _place_amulet_on_statue(game_view, _GameView):
        game_view.actions['AMULET'] = _GameView(game_view.state
                .with_tile_override(39, coords=(6, 9, 4))
                ._replace(message='You feel an inner\nwarmth as you receive\n\n\nthe templar blessing\n(MP & max MP up!)',
                          mp=game_view.state.mp + 2, max_mp=game_view.state.max_mp + 2,
                          items=tuple(i for i in game_view.state.items if i != 'AMULET'),
                          music=BASE_MUSIC_URL + 'AlexandrZhelanov-ADarknessOpus.ogg',
                          music_btn_pos=Position(2, 30)))
    mapscript_add_trigger((6, 8, 4), _place_amulet_on_statue, facing='east', permanent=True,
                                      condition=lambda gs: 'AMULET' in gs.items)
    mapscript_add_trigger((6, 9, 5), _place_amulet_on_statue, facing='north', permanent=True,
                                      condition=lambda gs: 'AMULET' in gs.items)
    mapscript_add_trigger((6, 10, 4), _place_amulet_on_statue, facing='west', permanent=True,
                                      condition=lambda gs: 'AMULET' in gs.items)
    mapscript_add_trigger((6, 9, 3), _place_amulet_on_statue, facing='south', permanent=True,
                                      condition=lambda gs: 'AMULET' in gs.items)

    # The chest on the water provides an artifact useful later on.
    # It can be accessed from the Templar Academy or with boots over the water.
    # Placing it here before the second door is handy as the player HAS to pick it up on their way, to bypass the boulder.
    def _grant_fish(game_view, _):
        game_view.state = game_view.state._replace(message="A smelly fish", items=game_view.state.items + ('FISH',))
    mapscript_add_chest((6, 14, 14), 26, _grant_fish)

    #---------------------------
    # Entering: Templar Academy (map: 10 - checkpoint)
    #---------------------------
    # The heroine has 8/30 HP, 2/3 MP, 8 gold, the HEAL & BURN spells and does 4 damages with their stick.
    # The path further is blocked by a bone pile, requiring the BURN spell & 1 MP.

    # Delivers a nice amount of gold; required to win: rusty sword
    mapscript_add_enemy((10, 2, 8), 'druid',
        hp=16, gold=12, rounds=(
            CR('Magic drain', mp_drain=True),
            CR('Dagger slash', atk=7),
            CR('Life drain  +14hp', atk=14, hp_drain=True),
        ))

    # Maze warp tiles setup:
    warp_portal_add(10, (14, 1), 'north', (9, 10), 'south')
    warp_portal_add(10, (11, 6), 'west', (12, 8), 'east')
    # Removing all existing chests, that were behind locked doors:
    mapscript_remove_chest((10, 11, 2))  # used to be: Magic Emerald (+5 HP)
    mapscript_remove_chest((10, 13, 2))  # used to be: 100 gold
    # The treasure at the end of the maze:
    def _grant_rusty_sword(game_view, _):
        game_view.state = game_view.state._replace(message="You found the Saint Knight's\nsword! It has gotten rusty...", weapon=4,
                                                   music=BASE_MUSIC_URL + 'AlexandrZhelanov-FullOfMemories.ogg',
                                                   music_btn_pos=Position(x=20, y=20))
    mapscript_add_chest((10, 9, 3), 18, _grant_rusty_sword)

    # The hero now does 8 damage with their sword, and can beat the druid
    # (but NOT the skeleton yet, even with a night of rest).
    # With the combat reward, the hero has 20 gold, and can now buy the boots...
    # CHECKPOINT
    # A boulder blocks access to a chest with a big gold treasure.
    # Escaping the boulder can only be done by moving backward straight to the exit,
    # blocking the entrance, and requiring to find another way in (using the boots).
    mapscript_add_boulder(trigger_pos=(10, 2, 12), start_at=(10, 2, 13), _dir='north',
                          message="You hear a loud thud.\nSomething is approaching\n")
    mapscript_add_boulder(trigger_pos=(10, 2, 2), start_at=(10, 4, 2), _dir='west',
                          condition=lambda gs: gs.rolling_boulders!=(),
                          message="You hear a thud beside you!\n Another boulder approaches")
    mapscript_add_message((10,7,4), 'The door locks behind you', condition=lambda gs: 'FISH' in gs.items)
    mapscript_add_chest((10, 1, 13), 'gold_60')  # The treasure behind the boulder
    # CHECKPOINT: finding 60$ in the chest is just enough to upgrade the sword and get a night of rest, before facing the skeleton

    #---------------------------
    # Entering: Canal Boneyard (map: 7 - checkpoint)
    #---------------------------
    # The heroine has 4/30 HP, 0/3 MP, 9 gold, boots, the HEAL & BURN spells and does 13 damages with their great sword.
    def _signal_portcullis(game_view, _):
        # Override default message indicating entered map name:
        music = BASE_MUSIC_URL + 'JanneHanhisuanto-OldCrypt.ogg'
        game_view.state = game_view.state._replace(message='You hear the portcullis\ngoing down behind you\n\n\n\nCanal Boneyard', music=music, music_btn_pos=PORTCULLIS_MUSIC_BTN_POS)
    mapscript_add_trigger((7, 2, 5), _signal_portcullis)  # one-time event/message

    # Entrance to Mausoleum is blocked by a zombie; required to win: full HP & full fire boost buff (+9 dmg)
    def _post_canal_zombie_fight(gs, _):
        assert gs.hp == 4 and not gs.mp, gs
    mapscript_add_enemy((7, 9, 5), 'zombie',
        hp=27, gold=5, rounds=(                # best moves:
            CR('Punch', atk=6, dodge=True),    # player ATTACK -> hero HP=24 | zombie HP=24
            CR('Bite  +8hp', atk=8, hp_drain=True),  # player ATTACK -> hero HP=16 | zombie HP=10
            CR('Critical thump', atk=12),      # player ATTACK -> hero HP=4  | zombie VANQUISHED!
            CR('Bite  +10hp', atk=10, dodge=True, hp_drain=True),
        ), post_victory=_post_canal_zombie_fight)
    def render_grave_icon(pdf):
        treasure_render_item(pdf, 42, Position(64,22))
    mapscript_add_message((7, 2, 2), 'You might want to pray\non the grave of\nthe Saint Knight.\nMay he rest in peace.',
                          extra_render=render_grave_icon)  # hint on grave appearance


    def _examine_glimpse(game_view, _GameView):
        game_view.actions['GLIMPSE'] = _GameView(game_view.state._replace(message='A voice comes\nfrom the water:\n\n"There is a shortcut\nto the Mausoleum entrance\nabove the fire."'))
    def _no_text_present(game_state):
        return game_state.message == ''
    mapscript_add_trigger((7, 4, 9), _examine_glimpse, facing='west', permanent=True, condition=_no_text_present)

    cauldron_pos = (7, 13, 5)
    def _shortcut_above_fire_and_cauldron(game_view, _GameView):
        # Creating a shortcut to the Mausoleum entrance, starting the fight against the zombie with the current Atk Buff:
        if not game_view.tile_override(cauldron_pos):
            log(game_view.state, 'drinking-cauldron')
            game_view.add_tile_override(40, coords=cauldron_pos)
            msg = 'You drink the cauldron soup\nand feel stronger!\n\n'
            game_view.state = game_view.state._replace(message=msg, bonus_atk=10, sfx=SFX(id=4, pos=Position(64, 88)))
        if game_view.state.facing == 'west' and not game_view.state.extra_render:
            game_view.actions['BEHIND_IVY'] = _GameView(game_view.state._replace(
                extra_render=lambda pdf: pdf.image('assets/page-up-hint.png', x=61, y=22)))
        # This trick is rendered 60 times,
        # due to the varying possible values for .hp / .bonus_atk / .facing / .extra_render
        trick = Trick('You climb on the roof\nand run to the\nMausoleum entrance!',
                      music=BASE_MUSIC_URL + 'JohanJansen-OrchestralLoomingBattle.ogg')
        game_view.actions[None] = _GameView(game_view.state._replace(x=9, y=5, facing='east', trick=trick,
                                                                     treasure_id=0, extra_render=None))
        game_view.prev_page_trick_game_view = game_view.actions[None]
    mapscript_remove_chest(cauldron_pos)  # used to be: Magic Diamond (Def Up)
    mapscript_add_trigger(cauldron_pos, _shortcut_above_fire_and_cauldron, permanent=True)

    def _tomb_healing(game_view, _GameView):
        gs = game_view.state
        log(gs, 'healed-by-tomb')
        message = 'A voice comes from the sky:\n"I give you my blessing,\nGo save this land!"'
        music = BASE_MUSIC_URL + 'MatthewPablo-Spiritwatcher.mp3'
        btn_pos = Position(x=71, y=36)
        render_knight_portrait = lambda pdf: portrait_render(pdf, 2, x=64, y=2)
        game_view.actions['PRAY'] = _GameView(gs.with_hidden_trigger('TOMB_HEALED')
                                                ._replace(hp=gs.max_hp, message=message, treasure_id=25,
                                                          extra_render=render_knight_portrait,
                                                          music=music, music_btn_pos=btn_pos))
    mapscript_add_trigger((7, 7, 7), _tomb_healing, facing='east', permanent=True,
                                     condition=lambda gs: 'TOMB_HEALED' not in gs.hidden_triggers)

    #---------------------------
    # Entering: Mausoleum (map: 8 - checkpoint)
    #---------------------------
    # The heroine has 4/30 HP, 0/3 MP, 14 gold, boots, the HEAL & BURN spells and does 13 damages with their great sword
    def _edge_of_the_abyss(game_view, _GameView):
        assert game_view.state.hp == 4, game_view
        gs = game_view.state._replace(message='The path ends abruptly.\nA bottomless abyss\nopens at your feet')
        game_view.state = gs
        if 'ABYSS_BOTTOM' in gs.secrets_found:
            trick = Trick('The abyss swallows\nall sound.  Only\nsilence remains.',
                          filler_renderer=render_abyss_filler_page,
                          link=False, filler_pages=3, background='depths')
            secret_view = _GameView(gs._replace(message='', trick=trick))
                                                #mode=GameMode.DIALOG, shop_id=abyss_bottom().id))
            game_view.actions[None] = secret_view
            game_view.next_page_trick_game_view = secret_view
        else:
            # Adding hint as a trick at the bottom of the abyss.
            # The secret comes in the form of a shop, whose page ID is the reflection of the hint page one:
            # Because of this reverse_id enigma, this secret MUST be the first than can be found,
            # otherwise the current reverse ID attribution algorithm will burn
            trick = Trick('You hear a faint echo:\n"a secret lies\nin the reflection\nof this place"',
                          filler_renderer=render_abyss_filler_page,
                          link=False, filler_pages=3, background='depths')
            secret_view = _GameView(gs.with_secret('ABYSS_BOTTOM')
                                      ._replace(message='', trick=trick, reverse_id=True,
                                                mode=GameMode.DIALOG, shop_id=abyss_bottom().id))
            game_view.actions[None] = secret_view
            game_view.next_page_trick_game_view = secret_view
    mapscript_add_trigger((8, 3, 5), _edge_of_the_abyss, facing='north', permanent=True)

    def _lower_portcullis(game_view, _):  # block the way back, to avoid exploding #states
        log(game_view.state, 'lowering-portcullis')
        game_view.state = clear_hidden_triggers(game_view.state) # removes TOMB_HEALED
        game_view.add_tile_override(26, coords=(8, 5, 7))
        game_view.add_tile_override(26, coords=(8, 7, 4))
        game_view.add_tile_override(26, coords=(8, 10, 10))
        game_view.state = game_view.state._replace(message='You hear portcullises\nclosing all around you',
                                                   music=BASE_MUSIC_URL + 'AlexandrZhelanov-DarkHall.mp3',
                                                   music_btn_pos=PORTCULLIS_MUSIC_BTN_POS)
    mapscript_add_trigger((8, 6, 7), _lower_portcullis)  # one-time event/message

    warp_portal_add(8, (7, 10), 'south', (10, 4), 'north')  # so that player get lost a bit
    mapscript_remove_chest((8, 3, 2))   # used to be: Magic Ruby (Atk Up) - replaced by mimic
    mapscript_remove_chest((8, 6, 9))   # used to be: 25 gold - moved up & replaced by mimic:
    mapscript_remove_chest((8, 3, 12))  # used to be: Magic Sapphire (MP Up)

    # 3 mimics possess the St Knight armor parts; required to win: UNLOCK spell + 1 MP each + enough HP (= 1 night of rest @ Inn)
    def _on_mimic_vanquished(gs, _):
        assert gs.spellbook >= 3, f'Mimic @{gs.coords} beaten without UNLOCK spell!'
        if gs.coords == BOX_MIMIC_POS:  # box mimic beaten => inscription on wall can be seen
            gs = gs.with_hidden_trigger('FOUNTAIN_HINT')
        if gs.coords != DOOR_MIMIC_POS:  # door mimic tile override is performed BEFORE the battle:
            return gs.with_tile_override(5, coords=gs.coords)  # remove camouflage
    _mimic_stats = lambda first_atk_name: dict(
        category=enemy().ENEMY_CATEGORY_AUTOMATON, show_on_map=False,  # rendered by the chest tile
        hp=30, rounds=(
            CR(first_atk_name, atk=5),    # Hero must be able to stand this x3
            CR('Critical bite', atk=30),  # The hero must not be able to beat a mimic without the UNLOCK spell.
                                          # Knowing he can HEAL on 1st round, a quick way to ensure this is to one-shot him on 2nd round.
        ), post_victory=_on_mimic_vanquished)
    mapscript_add_enemy((8, 7, 3), 'chest_mimic', **_mimic_stats('Lid clasp'), reward=RewardItem('ARMOR_PART', 38))
    def _chest_mimic_tongue(game_view, _):
        game_view.state = game_view.state._replace(
            extra_render=lambda pdf: pdf.image('assets/tongue.png', x=84, y=77))
    mapscript_add_trigger((8, 7, 4), _chest_mimic_tongue, facing='north', permanent=True,
                                      condition=lambda gs: (8, 7, 3) not in gs.vanquished_enemies)
    mapscript_add_trigger((8, 7, 2), _chest_mimic_tongue, facing='south', permanent=True,
                                      condition=lambda gs: (8, 7, 3) not in gs.vanquished_enemies)

    def _hidden_in_hay_pile(game_view, _):
        is_door_open = bool(game_view.tile_override((8, 4, 12)))
        if is_door_open: return False
        if 'BLUE_KEY' not in game_view.state.items:
            game_view.state = game_view.state._replace(message='You find\na blue key',
                                                       msg_place=MessagePlacement.UP,
                                                       items=game_view.state.items + ('BLUE_KEY',),
                                                       treasure_id=27)
            log(game_view.state, '+BLUE_KEY')
        else:
            return False
    mapscript_add_trigger((8, 8, 11), _hidden_in_hay_pile, permanent=True)

    def _lever(game_view, _GameView):
        lever_tile_id = game_view.tile_override((8, 12, 7)) or 48
        if lever_tile_id == 48:  # slot waiting for stick or puzzle over
            if not game_view.tile_override((8, 7, 4)): return
            log(game_view.state, 'put-stick-in-lever')
            game_view.actions['PUT_STICK_IN_LEVER'] = _GameView(game_view.state
                    .with_tile_override(49, coords=(8, 12, 7))
                    ._replace(message='You place your stick\nin the mechanism slot'))
        elif lever_tile_id == 49:  # lever waiting to be raised
            log(game_view.state, 'raise-lever')
            assert 'RAISE_LEVER' not in game_view.actions
            game_view.actions['RAISE_LEVER'] = _GameView(game_view.state
                    .with_tile_override(50, coords=(8, 12, 7), exist_ok=True)
                    .without_tile_override(coords=(8, 7, 4))
                    .without_tile_override(coords=(8, 10, 10))
                    # (cheap) Moving player 1 step back so that it does not immediately sees the FISH action
                    ._replace(message='You raise the lever\nand hear a metallic noise', x=10))
        elif lever_tile_id == 50:  # lever waiting for fish
            log(game_view.state, 'put-fish-on-lever-stick')
            game_view.actions['FISH'] = _GameView(game_view.state
                    .with_tile_override(51, coords=(8, 12, 7), exist_ok=True)
                    ._replace(message='You place the fish\non the stick',
                              items=tuple(i for i in game_view.state.items if i != 'FISH')))
        elif lever_tile_id == 51:  # fish-on-a-stick ready to be picked up!
            log(game_view.state, 'pick-up-fish-on-a-stick')
            game_view.actions['PICK_FISH_ON_A_STICK'] = _GameView(game_view.state
                    .without_tile_override((8, 12, 7))
                    ._replace(message='You pick up the\nfish-on-a-stick',
                              treasure_id=31, msg_place=MessagePlacement.UP,
                              items=game_view.state.items + ('FISH_ON_A_STICK',)))
    mapscript_add_trigger((8, 11, 7), _lever, facing='east', permanent=True)

    def _smoke_fish_on_a_stick(game_view, _GameView):
        log(game_view.state, 'smoking fish-on-a-stick on torch flame')
        items = tuple(i for i in game_view.state.items if i != 'FISH_ON_A_STICK') + ('SMOKED_FISH_ON_A_STICK',)
        message = 'You bring your fish on a stick\nnear the flame for a moment'
        game_view.actions['FISH_ON_A_STICK'] = _GameView(game_view.state._replace(
                items=items,
                treasure_id=32,
                message=message,
                msg_place=MessagePlacement.UP))
    mapscript_add_trigger((8, 11, 6), _smoke_fish_on_a_stick, facing='east', permanent=True,
                                      condition=lambda gs: 'FISH_ON_A_STICK' in gs.items)
    mapscript_add_trigger((8, 11, 8), _smoke_fish_on_a_stick, facing='east', permanent=True,
                                      condition=lambda gs: 'FISH_ON_A_STICK' in gs.items)

    goblin_bribes = (
        Bribe(item='FISH', successful=False, result_msg='"Yummy fish! But... yuck!\nToo slimy to eat by hand!"'),
        Bribe(item='FISH_ON_A_STICK', successful=False, result_msg='"Yummy fish! But... yuck!\nIt is raw! Disgusting!"'),
        Bribe(item='SMOKED_FISH_ON_A_STICK', result_msg='"Yummy fish!"\nHe takes it and leaves'),
    )
    mapscript_add_enemy((8, 10, 11), 'goblin',  # MUST be bribed
        category=ENEMY_CATEGORY_BEAST, bribes=goblin_bribes,
        hp=15, rounds=(CR('Dagger cut', atk=4),))

    def _open_locked_door_with_key(game_view, _GameView):
        if not game_view.tile_override((8, 4, 12)):  # avoid re-adding override if GameView already exists
            gs = game_view.state
            log(gs, 'opening-door-to-portal')
            new_gs = gs.with_tile_override(3, coords=(8, 4, 12))\
                       ._replace(items=tuple(i for i in gs.items if i != 'BLUE_KEY'))
            game_view.actions['BLUE_KEY'] = _GameView(new_gs)
    mapscript_add_trigger((8, 5, 12), _open_locked_door_with_key, facing='west', permanent=True,
                                      condition=lambda gs: 'BLUE_KEY' in gs.items)

    # CHECKPOINT: about to find scroll & pass through portal back to Cedar Village
    # Sage Therel will trade the scroll for the UNLOCK spell

    gorgon_pos = (5, 9, 9)
    def _unbelievable(*_):
        assert False, 'Gorgon vanquished in a fair battle!'
    mapscript_add_enemy(gorgon_pos, 'gorgon',
        condition=lambda gs: gs.tile_override_at(MAUSOLEUM_PORTAL_COORDS),
        category=enemy().ENEMY_CATEGORY_DEMON,
        hp=100, rounds=(CR('Petrifying stare', atk=42),),
        post_victory=_unbelievable)

    def _reflect_gorgon_or_loot_her_staff_or_shopkeeper_message(game_view, _GameView):
        gs = game_view.state
        has_staff_been_picked_up = gs.tile_override_at(gorgon_pos) == 54 # petrified_gorgon (without staff)
        if gs.facing == 'west' and 'HAND_MIRROR' in gs.items:
            game_view.state = game_view.state._replace(message='The shopkeeper shouts\n"I can\'t risk letting\nthat gorgon in here!"')
        elif gs.facing == 'north' and 'HAND_MIRROR' in gs.items:
            if not gs.extra_render:
                game_view.actions['HAND_MIRROR'] = _GameView(gs._replace(
                        extra_render=lambda pdf: pdf.image('assets/gorgon-in-mirror.png', x=0, y=0)))
            else:
                log(gs, 'reflecting-gorgon')
                game_view.actions['REFLECT_GORGON'] = _GameView(gs
                    .with_vanquished_enemy(gorgon_pos)
                    .with_tile_override(53, gorgon_pos).without_tile_override(VILLAGE_INN_COORDS)
                    ._replace(
                        message='The gorgon\npetrified\nherself!', msg_place=MessagePlacement.UP,
                        extra_render=lambda pdf: pdf.image('assets/gorgon-petrified-in-mirror.png', x=0, y=0),
                        music=BASE_MUSIC_URL + 'MarcusRasseli-WalkingWithPoseidon.mp3',
                        music_btn_pos=Position(74, 58),
                        items=tuple(i for i in gs.items if i != 'HAND_MIRROR')))
        elif gs.facing == 'south' and gorgon_pos in gs.vanquished_enemies and not has_staff_been_picked_up:
            log(gs, '+gorgon-staff')
            game_view.actions['PICK_STAFF'] = _GameView(gs
                .with_tile_override(54, gorgon_pos, exist_ok=True)
                ._replace(items=gs.items + ('STAFF',), treasure_id=30,
                          message="You take\nthe gorgon's staff", msg_place=MessagePlacement.UP))
    mapscript_add_trigger((5, 9, 8), _reflect_gorgon_or_loot_her_staff_or_shopkeeper_message, permanent=True)

    def _take_mirror(game_view, _GameView):
        gs = game_view.state
        if gs.facing == 'north' and not gs.tile_override_at((8, 8, 11)): #mirror not taken yet
            log(gs, '+HAND_MIRROR')
            game_view.actions['TAKE_MIRROR'] = _GameView(gs
                .with_tile_override(37, (8,8,11))
                ._replace(items=gs.items + ('HAND_MIRROR',), treasure_id=41,
                          message="You remove the mirror\n\nA secret passage opens!",
                          msg_place=MessagePlacement.UP))
    mapscript_add_trigger((8, 8, 12), _take_mirror, permanent=True)

    def _mausoleum_portal_hint(game_view, _):
        gs = game_view.state
        if not is_instinct_preventing_to_pass_mausoleum_portal(gs): return
        msg = None
        if gs.items.count('ARMOR_PART') < 4:
            # msg = 'No need to go back until\nyou have all the armor parts'
            msg = 'The whispering wind\nsuggests there are more\narmor parts to find'
        elif not gs.tile_override_at(MAUSOLEUM_EXIT_COORDS):
            msg = 'The whispering wind\ntells you the key to this\ncrypt exit is in the books'
        assert msg, 'A hint should be given if the path is blocked'
        game_view.state = gs._replace(message=msg)
    mapscript_add_trigger((8, 3, 12), _mausoleum_portal_hint, facing='west', permanent=True)
    def _village_portal_hint(game_view, _):
        gs = game_view.state
        if not is_instinct_preventing_to_pass_village_portal(gs): return
        msg = None
        if gs.spellbook < 3:
            msg = 'The whispering wind\nadvises you to bring\nthe scroll to the sage\nbefore returning'
        elif gs.gold >= 10:
            msg = 'The whispering wind\nadvises you to rest before\nreturning to that dungeon'
        elif gorgon_pos not in gs.vanquished_enemies:
            msg = 'The whispering wind\nimplores you not to abandon\nthe villagers to the gorgon'
        elif 'STAFF' not in gs.items:
            msg = 'The whispering wind\nadvises you to inspect the\ngorgon before returning'
        assert msg, 'A hint should be given if the path is blocked'
        game_view.state = gs._replace(message=msg)
    mapscript_add_trigger((5, 9, 4), _village_portal_hint, facing='north', permanent=True)

    def _facing_door_mimic(game_view, _GameView):
        if 'MOVE-FORWARD' in game_view.actions:
            assert game_view.actions['MOVE-FORWARD'].state.mode == GameMode.COMBAT
            return
        mimic_stats = _mimic_stats('Flying handle')
        _enemy = Enemy(name='door_mimic', **mimic_stats, max_hp=mimic_stats['hp'], reward=RewardItem('ARMOR_PART', 39))
        game_view.actions['MOVE-FORWARD'] = _GameView(game_view.state
            .with_tile_override(5, coords=(8, 4, 2))
            ._replace(mode=GameMode.COMBAT, combat=CombatState(enemy=_enemy)))
    mapscript_add_trigger(DOOR_MIMIC_POS, _facing_door_mimic, facing='west', permanent=True,
                                          condition=lambda gs: DOOR_MIMIC_POS not in gs.vanquished_enemies)
    mapscript_add_enemy(BOX_MIMIC_POS, 'box_mimic', **_mimic_stats('Wood slivers'), reward=RewardItem('ARMOR_PART', 40))

    def _second_lever(game_view, _GameView):
        gs = game_view.state
        if gs.tile_override_at(MAUSOLEUM_EXIT_COORDS):
            game_view.state = game_view.state._replace(extra_render=RENDER_STAFF_PUZZLE[2])
        elif gs.puzzle_step is not None:
            lever_angle_index = gs.puzzle_step % 10
            if not gs.extra_render:  # happens when moving to this tile from another one
                assert False # game no longer preserves staff in slot, so this should never happen
                assert gs.puzzle_step == 0, gs.puzzle_step
                angle=0
                if gs.tile_override_at(MAUSOLEUM_EXIT_COORDS):
                    angle=2
                game_view.state = game_view.state._replace(extra_render=RENDER_STAFF_PUZZLE[angle])
            if gs.puzzle_step == ROTATING_LEVER_CORRECT_SEQUENCE:
                game_view.state = game_view.state.with_tile_override(5, MAUSOLEUM_EXIT_COORDS)._replace(
                        items=tuple(i for i in gs.items if i != 'STAFF'),
                        message='You hear the iron gate\nrise behind you',
                        puzzle_step=None, extra_render=RENDER_STAFF_PUZZLE[2])
            gs = game_view.state
            log(game_view.state, f'lever-sequence-{gs.puzzle_step}')
            # If the sequence of lever positions is correct so far, we propagate it:
            new_puzzle_step = 0
            is_correct = str(ROTATING_LEVER_CORRECT_SEQUENCE).startswith(str(gs.puzzle_step))
            if is_correct and 'FOUNTAIN_HINT' in gs.hidden_triggers:
                # This hidden trigger indicates that access was given to the last bookshelf:
                # in order to reduce #states, we only allow to solve this puzzle when the ballad has been read.
                new_puzzle_step = gs.puzzle_step * 10
            for i in range(8):
                if i != lever_angle_index:
                    game_view.actions[f'TURN_LEVER_{i}'] = _GameView(gs._replace(message='',
                        puzzle_step=new_puzzle_step + i,
                        extra_render=RENDER_STAFF_PUZZLE[i]))
        elif 'STAFF' in gs.items:
            log(gs, 'placing-staff-in-slot')
            game_view.actions['STAFF'] = _GameView(gs._replace(
                    message="You place the gorgon's staff\nin the mechanism slot\nand runes appear on the wall",
                    puzzle_step=0, extra_render=RENDER_STAFF_PUZZLE[0]))
    mapscript_add_trigger((8, 13, 7), _second_lever, facing='west', permanent=True)

    # CHECKPOINT: about to enter the Dead Walkways and fight the storm dragon, with the St Knight armor

    #---------------------------
    # Entering: Dead Walkways (map: 9 - checkpoint)
    #---------------------------
    # The heroine has 15/30 HP, 0/3 MP, 3/4 gold, boots, the HEAL, BURN & UNLOCK spells, St Knight armor (def 12) and does 13 dmg with their sword.
    def dragon_withstand_logic(game_state, attack_damage):
        attack_damage = attack_damage-7
        combat = game_state.combat
        members_count = sum(1 for action_name in combat.enemy.custom_actions_names if action_name.startswith('ATTACK'))
        if combat.action_name == 'ATTACK_HEAD' and members_count > 1:
            # Head cannot be injured until all other members are severed:
            return game_state, 'Parried!'
        log_result = f'{attack_damage} damage'
        if combat.action_name == 'ATTACK_WINGS' and combat.enemy.hp >= 6 * attack_damage:
            # The wings are not severed on the first hits, only after the 3rd cut:
            new_custom_actions = combat.enemy.custom_actions
        else:  # Member is severed and cannot be clicked:
            new_custom_actions = tuple(cca for cca in combat.enemy.custom_actions if cca.name != combat.action_name)
            attack_damage = attack_damage * 3
            log_result = f'{attack_damage} damage'
            if combat.action_name == 'ATTACK_TAIL':
                log_result = 'Tail cut! ' + log_result #+ '!'
            elif combat.action_name == 'ATTACK_WINGS':
                log_result = 'Wing cut! ' + log_result #+ '!'
            else:
                log_result = 'Head cut! ' + log_result #+ '!'
        new_hp = combat.enemy.hp - attack_damage
        combat = combat._replace(enemy=combat.enemy._replace(hp=new_hp, custom_actions=new_custom_actions))
        return game_state._replace(combat=combat), log_result
    def dragon_attack_logic(combat):
        if 'ATTACK_TAIL' in combat.enemy.custom_actions_names:  # = tail not cut yet
            # Tail is the most lethal attack, it kills the hero in 2 hits, and hence must be cut 1st:
            return CR('Tail slap', atk=16)
        if 'ATTACK_WINGS' in combat.enemy.custom_actions_names:  # = wing not cut yet
            return CR('Wing thump', atk=14)
        if 'ATTACK_HEAD' in combat.enemy.custom_actions_names:  # = head not cut yet
            return CR('Bite', atk=15)
        return CR()  # dies without attacking
    def dragon_enemy_frame(combat):
        if 'ATTACK_TAIL' in combat.enemy.custom_actions_names:  # = tail not cut yet
            return 0
        if 'ATTACK_WINGS' in combat.enemy.custom_actions_names:  # = wing not cut yet
            return 1
        if 'ATTACK_HEAD' in combat.enemy.custom_actions_names:  # = head not cut yet
            return 2
        return 3  # head severed
    def _ensure_beaten_with_st_knight_armor(gs, src_view):
        if gs.armor <= 1 or gs.hp != 2:
            log_combat(src_view)
            assert gs.armor > 1, 'Storm Dragon beaten without St Knight armor!'
            assert gs.hp == 2, f'Hero should have 2 HP after beating the Storm Dragon, in order to face the druid later on, but has: {gs.hp} HP'
            # 2 final HP = 15 initial HP - 4 dmg (tail slap round 1) - 3*2 dmg (wing thumps round 2, 3 & 4) - 3 dmg (final bite round 5)
    mapscript_add_enemy((9, 2, 5), 'storm_dragon',  # required to win: St Knight armor, great sword & > 11 HP
        category=ENEMY_CATEGORY_BEAST,
        hp=65, max_rounds=6, custom_actions=(
            CCA('ATTACK_HEAD', Position(x=98, y=20)),
            CCA('ATTACK_TAIL', Position(x=30, y=44)),
            CCA('ATTACK_WINGS', Position(x=98, y=81)),
            CCA('HEAL'), CCA('BURN'), CCA('UNLOCK'),
        ), withstand_logic=dragon_withstand_logic, attack_logic=dragon_attack_logic, enemy_frame=dragon_enemy_frame,
        post_defeat_condition=lambda gs: gs.armor <= 1,   # only display hint if not wearing strong armor
        post_defeat=render_storm_dragon_post_defeat_hint,
        post_victory=_ensure_beaten_with_st_knight_armor,
        gold=7)

    goblin_bribe = Bribe(gold=3, result_msg='He runs away with your gold')
    mapscript_add_enemy((9, 3, 3), 'goblin',  # deal is a red-herring, run away if fought
        intro_msg="I'll give you the door key\nfor 3 gold, milady.",
        category=ENEMY_CATEGORY_BEAST, bribes=(goblin_bribe,), hp=10, rounds=(CR('', run_away=True),))

    mapscript_add_enemy((9, 3, 7), 'druid',   # ask for mercy if fought -> restore hero HP/MP
        hp=40, gold=5, rounds=(
            CR('Dagger slash', atk=7),  # fully withstanded by armor, but still gives 1 damage
            CR('Life drain', miss=True),
            CR('', ask_for_mercy=('Mercy! Spare me!',
                                  # The gold reset to zero helps limiting the #states
                                  lambda gs: gs._replace(gold=0, hp=gs.max_hp, mp=gs.max_mp, treasure_id=25,
                                                         message='"Thank you noble lady!\nLet me heal you in return."\n(you give him your last coins)'))),
            CR('', miss=True),
        ))

    def _pass_arch1(game_view, _):
        gs = game_view.state
        assert gs.hp == gs.max_hp, f'Hero should have full HP on 1st arch passing, but has: {gs.hp} HP'
        assert gs.mp == 2, f'Hero should have 2 MP on 1st arch passing, but has: {gs.mp} MP'
        msg = 'The Empress\'s voice echoes:\n'
        msg += '\n"Go away, impostor!\nYou have nothing of a knight!"\n'
        # Doing a bit of unnecessary state cleanup:
        game_view.state = gs._replace(tile_overrides=(((9, 4, 5), 26),),  # portcullis block the way back
                                      triggers_activated=(gs.coords,), vanquished_enemies=((9, 2, 5), (9, 3, 3)),
                                      message=msg)
    mapscript_add_trigger((9, 5, 5), _pass_arch1)

    def _grant_buckler(game_view, _GameView):
        if 'BUCKLER' in game_view.state.items:
            log_path_to(game_view, map_as_string=map_as_string, stop_at_cond=lambda gv: 'BUCKLER' not in gv.state.items)
            assert False
        game_view.state = game_view.state._replace(message="A buckler", items=game_view.state.items + ('BUCKLER',))
    mapscript_add_chest((9, 6, 9), 33, _grant_buckler)

    def _pass_arch2(game_view, _):
        msg = '\n\n\n\nThe Empress\'s voice echoes:\n'
        msg += '\n"My love, the saint knight,\ndied a hero to save this\ndamn realm. You\'re a joke\ncompared to him!"'
        # Doing some tile_overrides cleanup to avoid #states branching due to boxes:
        game_view.state = game_view.state._replace(tile_overrides=(((9, 7, 2), 26),((9, 5, 7), 1),((9, 5, 8), 1),((9, 6, 7), 1),((9, 6, 8), 1),),  # portcullis block the way back, sokoban
                                                   message=msg)
    mapscript_add_trigger((9, 8, 2), _pass_arch2)

    # Block access to the Empress boss; required to win: full HP & St Knight armor & a bucklet
    def _ensure_beaten_with_buckler(gs, src_view):
        buckler_used, gv = False, src_view.src_view
        assert 'BUCKLER' not in gv.state.items
        while gv.state.combat:
            buckler_used = 'BUCKLER' in gv.state.items
            gv = gv.src_view
        if not buckler_used or gs.hp != 16:
            log_combat(src_view)
            assert buckler_used, 'Demon Seamus beaten without buckler!'
            assert gs.hp == 16, f'Hero should have 16 HP after beating Demon Seamus, but has: {gs.hp} HP'
    mapscript_add_enemy((9, 9, 3), 'demon_seamus',
        condition=lambda gs: 'SEAMUS_TRANSFORMED' in gs.hidden_triggers,
        category=enemy().ENEMY_CATEGORY_DEMON, hp=13*5-2, max_rounds=7, rounds=(
            # STRATEGY to beat him: parry all spits, attack on all other rounds
            CR('Soul sucking', mp_drain=True, sfx=SFX(id=1, pos=Position(64, 42))),
            CR('Spit frost', atk=42),
            CR('Hypnotic stare', atk=19, sfx=SFX(id=0, pos=Position(64, 40))),
        ),
        loop_frames=True,
        music=BASE_MUSIC_URL + 'MatthewPablo-DefyingCommodus.mp3',
        reward=RewardTreasure('Magic Diamond found\n(MP & buckler restored)', 15,
                              lambda gs: gs._replace(mp=gs.max_mp, items=gs.items + ('BUCKLER',))),
        post_victory=_ensure_beaten_with_buckler
    )

    def _last_empress_words(game_view, _):
        msg = '\nThe Empress\'s voice echoes:\n\n"You\'re an insult\nto his memory,\nprepare to die!"\n'
        game_view.state = game_view.state._replace(message=msg)
    mapscript_add_trigger((9, 9, 5), _last_empress_words)  # one-time message

    def post_empress_phase1_victory(next_gs, src_view):
        assert src_view.state.message in EMPRESS_INTERPHASE_LINES
        # We extend the combat a little:
        next_gs = next_gs._replace(mode=GameMode.COMBAT, vanquished_enemies=())  # Empress is not really vanquished yet!
        if src_view.state.message == EMPRESS_INTERPHASE_LINES[-1]:
            # Last Empress dialog line -> triggering phase 2 of the boss fight:
            # The heroine has 3/30HP, 0/3 MP, the HEAL, BURN & UNLOCK spells, no BUCKLER,
            # the St Knight armor (def 12) and does 13 dmg with their sword.
            combat = src_view.state.combat
            assert combat.round == 6, combat.round
            assert next_gs.hp == 3, next_gs.hp
            assert combat.enemy.hp == 0, combat.enemy.hp
            phase2_enemy = Enemy(name='empress_+_dominik', category=enemy().ENEMY_CATEGORY_DEMON,
                hp=1, max_hp=26,
                max_rounds=19, custom_actions=(
                    CCA('ATTACK_EMPRESS', Position(x=107, y=34)),
                    CCA('ATTACK_DOMINIK', Position(x=62, y=86)),
                    CCA('HEAL',           Position(x=140, y=34)),
                    CCA('BURN_EMPRESS',   Position(x=107, y=51)),
                    CCA('BURN_DOMINIK',   Position(x=44, y=86)),
                    CCA('UNLOCK_EMPRESS', Position(x=107, y=68)),
                    CCA('UNLOCK_DOMINIK', Position(x=80, y=86)),
                    CCA('TAKE_SCEPTER',   renderer=render_scepter),
                ), withstand_logic=phase2_withstand_logic, attack_logic=phase2_attack_logic, enemy_frame=phase2_enemy_frame,
                post_victory=lambda gs, _: gs._replace(mode=GameMode.DIALOG, shop_id=the_end().id))
            return next_gs._replace(combat=CombatState(enemy=phase2_enemy))
        # Displaying next inter-phases Empress dialog line:
        line_index = EMPRESS_INTERPHASE_LINES.index(src_view.state.message)
        combat = src_view.state.combat._replace(avatar_log=None, enemy_log=None)
        return next_gs._replace(combat=combat, message=EMPRESS_INTERPHASE_LINES[line_index + 1])

    # The heroine has 16/30HP, 3/3 MP, the HEAL, BURN & UNLOCK spells, a BUCKLER,
    # the St Knight armor (def 12) and does 13 dmg with their sword.
    mapscript_add_enemy((9, 11, 5), 'death_speaker',  # Empress
        show_on_map=False,  # rendered by the tile
        music=BASE_MUSIC_URL + 'MatthewPablo-HeroicDemise.mp3',
        # STRATEGY to beat her: parry lightning attacks, use 2 BURN to put shield down, 1 HEAL, else attack
        # Note that the Empress is of DEMON type, so BURN does her only 4 dmg (it ignores the shield)
        hp=34, max_rounds=10, rounds=(                       # best moves:
            CR('Bone shield!', boneshield_up=True, atk=15),  # player ATTACK -> hero HP=13 | empress HP=21
            CR('Death voice!', atk=24,                       # player BURN -> hero HP=1    | empress HP=17
               sfx=SFX(id=8, pos=Position(64, 6))),
            CR('Dark lightning!', atk=38,                    # player PARRY -> hero HP=1   | empress HP=17
               sfx=SFX(id=2, pos=Position(64, 42))),
            # Bone shield                                    # player HEAL -> hero HP=18   | empress HP=17
            # Death voice                                    # player BURN -> hero HP=6    | empress HP=13
            # Dark lightning                                 # player PARRY -> hero HP=6   | empress HP=13
            # Bone shield                                    # player ATTACK -> hero HP=3  | empress HP=0
        ), victory_msg=EMPRESS_INTERPHASE_LINES[0], post_victory=post_empress_phase1_victory)

    def phase2_withstand_logic(game_state, attack_damage):
        combat = game_state.combat
        if combat.action_name in ('ATTACK_DOMINIK', 'BURN_DOMINIK'):
            # Dominik only reflects all attacks against him & heal the impress:
            log_result = f'reflected {attack_damage} damage'
            game_state = game_state._replace(hp=game_state.hp - attack_damage)
        elif combat.action_name == 'UNLOCK_DOMINIK':
            log_result = 'Dominik is dazed'
            # Making this action unavailable, in order to avoid repeating it, and to signal a framme change:
            new_custom_actions = tuple(cca for cca in combat.enemy.custom_actions if cca.name != combat.action_name)
            combat = combat._replace(enemy=combat.enemy._replace(custom_actions=new_custom_actions))
            game_state = game_state._replace(combat=combat)
        else:
            assert combat.action_name in ('ATTACK_EMPRESS', 'BURN_EMPRESS', 'UNLOCK_EMPRESS')
            log_result = f'{attack_damage} damage'
            new_hp = combat.enemy.hp - attack_damage
            game_state = game_state._replace(combat=combat._replace(enemy=combat.enemy._replace(hp=new_hp)))
        return game_state, log_result
    def phase2_attack_logic(combat):
        dominik_dazed = 'UNLOCK_DOMINIK' not in combat.enemy.custom_actions_names
        if combat.enemy.hp < 14 and not dominik_dazed:
            return CR('\"Dominik, heal me!\"', heal=combat.enemy.max_hp, sfx=SFX(id=9, pos=Position(75, 14)))
        return CR('Death voice!', atk=22, sfx=SFX(id=8, pos=Position(98, 6)))
    def phase2_enemy_frame(combat):
        return 0 if 'UNLOCK_DOMINIK' in combat.enemy.custom_actions_names else 1


def render_abyss_filler_page(pdf, i):
    pdf.add_page()
    pdf.image(REL_RELEASE_DIR + 'images/backgrounds/black.png', x=0, y=0)
    if i == 1: pdf.image('assets/blobfish.png', x=53, y=30)


def render_monastery_post_defeat_hint(pdf):
    bitfont_set_color_red(False)
    pdf.add_page()
    pdf.image(REL_RELEASE_DIR + 'images/backgrounds/black.png', x=0, y=0)
    bitfont_render(pdf, 'Tip', 80, 5, Justify.CENTER)
    render_bar(pdf, 10, 20)
    white_arrow_render(pdf, 'BACK', 16, 16)
    bitfont_render(pdf, 'If you cannot bring an enemy\nlifebar to zero before\nlosing your last HP,\nmaybe an item somewhere\ncan help you.', 80, 40, Justify.CENTER, page_id=1)
    with bitfont_color_red():
        bitfont_render(pdf, 'Start over', 80, 100, Justify.CENTER, page_id=1)


def render_staff_puzzle(lever_angle_index):
    def extra_render(pdf):
        pdf.image('assets/runes.png', x=0, y=0)
        x, y, _ = LEVER_STAFF_POS[lever_angle_index]
        pdf.image(f'assets/lever-staff-{lever_angle_index}.png', x=x, y=y)
    return extra_render
RENDER_STAFF_PUZZLE = tuple(render_staff_puzzle(i) for i in range(8))

LEVER_STAFF_POS = (  # order matches assets/lever-staff-$i.png files
    Position(x=76, y=41),
    Position(x=77, y=47),
    Position(x=80, y=69),
    Position(x=77, y=69),
    Position(x=76, y=71),
    Position(x=54, y=69),
    Position(x=48, y=69),
    Position(x=55, y=47),
)


def render_storm_dragon_post_defeat_hint(pdf):
    bitfont_set_color_red(False)
    pdf.add_page()
    pdf.image(REL_RELEASE_DIR + 'images/backgrounds/black.png', x=0, y=0)
    bitfont_render(pdf, 'Tip', 80, 5, Justify.CENTER)
    bitfont_render(pdf, 'You need better armor\nto withstand \nthe dragon\'s attacks', 80, 40, Justify.CENTER, page_id=1)
    with bitfont_color_red():
        bitfont_render(pdf, 'Start over', 80, 100, Justify.CENTER, page_id=1)


def render_scepter(pdf, page_id):
    x, y = 103, 95
    pdf.image('assets/empress-scepter.png', x=x, y=y)
    add_link(pdf, x, y, width=54, height=16, page_id=page_id, link_alt='Take the empress\'s scepter laying on the ground')


def clear_hidden_triggers(gs):
    return gs._replace(hidden_triggers=tuple(ht for ht in gs.hidden_triggers
    # Those are the only ones that need to be preserved until 2nd visit to village:
                                             if ht in ('BEEN_TO_VILLAGE', 'FIRST_NIGHT_OF_REST')))
