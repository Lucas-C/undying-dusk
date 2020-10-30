from ..ascii import map_as_string
from ..bitfont import bitfont_render, bitfont_set_color_red, Justify
from ..entities import Bribe, Checkpoint, CombatRound as CR, MessagePlacement, Position, RewardItem, RewardTreasure, SFX, Trick
from ..js import REL_RELEASE_DIR
from ..logs import log, log_combat, log_path_to
from ..mapscript import *
from ..render import render_bar
from ..render_utils import portrait_render, white_arrow_render

from .scenes import abyss_bottom, seamus_through_small_window, the_end, BASE_MUSIC_URL
from .world import is_instinct_preventing_to_enter_village, is_instinct_preventing_to_enter_templar_academy, is_instinct_preventing_to_pass_mausoleum_portal, is_instinct_preventing_to_pass_village_portal


VICTORY_POS = Checkpoint((9, 11, 5), 'ending after beating the Empress')
CHECKPOINTS = (  # intermediate positions that should be reachable through a unique path only
    # Checkpoint((1, 6, 6), 'Entering Monastery after Scriptorium'),
    Checkpoint((1, 4, 9),   'After beating the imp, still in Monastery'),
    Checkpoint((5, 3, 1),   'Entering Cedar Village'),
    Checkpoint((6, 4, 3),   'Entering Zuruth Plains, after beating zombie'),
    Checkpoint((10, 2, 1),  'Entering Templar Academy with the BURN spell',
                            condition=lambda gs: gs.mp >= 2 and gs.spellbook >= 2),
    Checkpoint((10, 2, 8),  'After beating the druid in the Academy'),
    Checkpoint((10, 2, 14), 'Before the chest behind boulder in the Academy'),
    Checkpoint((7, 2, 5),   'Canal Boneyard entrance'),
    Checkpoint((7, 9, 5),   'After beating zombie on Canal Boneyard exit'),
    # Checkpoint((8, 5, 7),   'Mausoleum, about to pass portcullis'),
    Checkpoint((8, 4, 12),  'Mausoleum, after opening door with blue key'),
    Checkpoint((5, 9, 4),   'back to Cedar Village'),
    Checkpoint((8, 3, 12),  'back to Mausoleum with full HP & UNLOCK spell'),
    Checkpoint((5, 9, 4),   'back again to Cedar Village'),
    # Checkpoint((4, 10, 14), 'after beating the Shadow Soul -> secret',
                            # condition=lambda gs: 'BEEN_TO_VILLAGE' in gs.hidden_triggers),
    # Checkpoint((5, 3, 1),   'back to Cedar Village after finding dead tree secret'),
    Checkpoint((8, 14, 7),  'Mausoleum exit before dragon, with strong armor',
                            condition=lambda gs: gs.armor > 1),
    Checkpoint((9, 2, 5),   'Dead Walkways entrance, after beating dragon'),
    Checkpoint((9, 5, 5),   'after passing 1st Dead Walkways arch'),
    Checkpoint((9, 8, 2),   'after passing 2nd Dead Walkways arch',
                            condition=lambda gs: 'BUCKLER' in gs.items),
    Checkpoint((9, 9, 3),   'after flying demon fight, about to face Empress'),
    VICTORY_POS,
)
# VICTORY_POS = Checkpoint((0, 1, 1)); CHECKPOINTS = (VICTORY_POS,)  # stop after intro
# VICTORY_POS = Checkpoint((2, 3, 2)); CHECKPOINTS = (VICTORY_POS,)  # stop after leaving cell
# VICTORY_POS = Checkpoint((2, 1, 2)); CHECKPOINTS = (VICTORY_POS,)  # stop after beating Scriptorium sokoban
# VICTORY_POS = Checkpoint((3, 2, 3)); CHECKPOINTS = (VICTORY_POS,)  # stop after beating Shadow Tendrils

ENEMY_CATEGORY_BEAST = 4  # new category, 1s unused integer among original ENEMY_CATEGORY_* constants
PORTCULLIS_BTN_POS = Position(x=72, y=55)


def script_it():
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
        game_view.actions['EXAMINE'] = _GameView(game_view.state._replace(message='You find a wood stick\ndown in the well', msg_place=MessagePlacement.UP, treasure_id=10, weapon=1))
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
        post_defeat=render_post_defeat_hint)

    # Block access to the Monastery exit; required to win: Wood Stick (4 damages) + HEAL spell
    mapscript_add_enemy((1, 4, 8), 'imp',
        hp=8, gold=2, rounds=(
            CR('Trident slash', atk=10),
            CR('Trident thrust', atk=15),  # without HEAL spell, hero must dies on 2nd round
            CR('Horn strike', atk=7),
        ), # at the end of the combat, hero has 1 HP
        post_defeat=render_post_defeat_hint)

    #---------------------------
    # Entering: Monastery Trail (map: 4 - checkpoint)
    #---------------------------
    # The heroine now has 1/25 HP, 0/1 MP & the HEAL spell and does 4 damages with their stick.
    # There are 2 enemies blocking each path to the village entrance.
    # It must be evident that the Shadow Soul is too strong to be beaten now.
    # It can however be bypassed through the forest to access the chest behind it.
    # The imp can be beaten, but only once the holy water has been crafter at the well.

    mapscript_add_message((4, 6, 2), 'The Monastery doors\nare closed', facing='north')
    # The door is closed by mod.world:patched_can_move_to
    mapscript_add_message((4, 9, 3), 'The whispering wind\ntells you of hidden\npassages in the forest', facing='east')
    mapscript_add_message((4, 3, 9), 'The whispering wind\ntells you that demons\nfear blessed liquids', facing='west')

    def _examine_forest_well(game_view, _GameView):
        gs = game_view.state
        if 'CRUCIFIX' in gs.items:
            game_view.actions['CRUCIFIX'] = _GameView(gs.with_hidden_trigger('HOLY_WELL')
                                                        ._replace(message='SPLASH !',
                                                                  items=tuple(i for i in gs.items if i != 'CRUCIFIX')))
        if 'EMPTY_BOTTLE' in gs.items:
            if 'HOLY_WELL' in gs.hidden_triggers:
                new_game_state = gs._replace(message='You fill the bottle\nwith holy water.',
                                             msg_place=MessagePlacement.UP,
                                             items=tuple(i for i in gs.items if i != 'EMPTY_BOTTLE') + ('HOLY_WATER',),
                                             treasure_id=22)
            else:
                new_game_state = gs._replace(message='You fill the bottle\nwith water.',
                                             msg_place=MessagePlacement.UP)
            game_view.actions['EMPTY_BOTTLE'] = _GameView(new_game_state)
    mapscript_add_trigger((4, 3, 2), _examine_forest_well, facing='west', permanent=True)

    def _grant_empty_bottle(game_view, _):  # placed on a stump in the forest, near the Shadow Soul
        game_view.state = game_view.state._replace(message="Empty bottle found",
                                                   items=game_view.state.items + ('EMPTY_BOTTLE',))
    mapscript_add_chest((4, 11, 9), 34, _grant_empty_bottle)

    # Block access to the village entrance at first, then to a SECRET; required to win: St Knight armor (def 12), a Great Sword (13 dmg), 0 MP & 12 HP
    shadow_soul_stats = dict(
        hp=53, rounds=(
            CR('Magic drain', mp_drain=True),
            CR('Magic pump', mp_drain=True),
            CR('Magic suck', mp_drain=True),
            CR('Critical blast!', atk=20),
            CR('Critical blast!', atk=15),
        ))
    mapscript_add_enemy((4, 9, 9), 'shadow_soul', **shadow_soul_stats)

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
        game_view.add_tile_override(18, coords=(4, 10, 15))  # locking door to Cedar Village
    mapscript_add_trigger((5, 3, 1), _enter_cedar_village)
    mapscript_add_enemy((4, 10, 14), 'shadow_soul', **shadow_soul_stats,
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
                                                        ._replace(message=msg, hp=12,  # restoring HP
                                                                  music=music, music_btn_pos=btn_pos))
        game_view.actions['LIGHT'].remove_tile_override(coords=(4, 10, 15))  # opening locked door to Cedar Village
    mapscript_add_trigger((4, 10, 12), _facing_dead_tree, facing='north', permanent=True,
                                       condition=lambda gs: 'BEEN_TO_VILLAGE' in gs.hidden_triggers and 'DEAD_TREE' not in gs.secrets_found)

    # A boulder blocks access to a chest with 10 gold.
    # It can be avoided by moving backward back to the street the player comes from.
    mapscript_add_message((5, 2, 3), 'DANGER!\nBeware rock slides', msg_place=MessagePlacement.UP)  # sign
    mapscript_add_boulder(trigger_pos=(5, 3, 10), start_at=(5, 6, 10), _dir='west')

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
    def _post_zombie_fight(gs):
        assert gs.hp == 8 and not gs.mp, f'HP={gs.hp} MP={gs.mp}'
    mapscript_add_enemy((5, 9, 10), 'zombie',
        hp=5, gold=3, rounds=(                 # best moves:
            CR('Critical thump!', atk=20),     # ATTACK -> hero HP=10 | zombie HP=1
            CR('Bite', atk=7, hp_drain=True),  # HEAL   -> hero HP=23 | zombie HP=8
            CR('Blow', atk=6),                 # ATTACK -> hero HP=17 | zombie HP=4
            CR('Punch', atk=9),                # ATTACK -> hero HP=8  | zombie HP=0
        ), post_victory=_post_zombie_fight)

    #---------------------------
    # Entering: Zuruth Plains (map: 6 - checkpoint)
    #---------------------------
    # The heroine has 8/30 HP, 0/1 MP, 5 gold, the HEAL spells and does 4 damages with their stick.

    # We limit the #states by cutting unneeded access to the village:
    mapscript_add_message((6, 4, 3), 'Trust your instinct:\nno need to go back for now', facing='north',
                                      condition=is_instinct_preventing_to_enter_village)
    mapscript_add_message((6, 8, 14), 'Trust your instinct:\nno need to go back no more', facing='south',
                                      condition=is_instinct_preventing_to_enter_templar_academy )

    # Entrance to Canal Boneyard is blocked by a skeleton; required to win: full HP + 3 MP (1 BURN & 2 HEAL) + great sword (13 dmg)
    mapscript_add_enemy((6, 12, 7), 'skeleton',
        # STRATEGY to beat him: wait until 5th turn for an opportunity to launch BURN spell with a critical
        hp=58, gold=9, max_rounds=6, rounds=(            # best moves:
            CR('Sword thrust', atk=14),                  # ATTACK         -> hero HP=16 | skeleton HP=45
            CR('Sword slash', atk=12),                   # ATTACK         -> hero HP=4  | skeleton HP=32
            CR('Sword thrust', atk=14),                  # HEAL           -> hero HP=10 | skeleton HP=32
            CR('Sword slash', atk=12),                   # HEAL           -> hero HP=18 | skeleton HP=32
            CR('Sword thrust', atk=14, hero_crit=True),  # CRITICAL BURN! -> hero HP=4  | skeleton HP=0
        ), music=BASE_MUSIC_URL + 'MatthewPablo-DarkDescent.mp3',
        post_victory=clear_hidden_triggers)  # removes RUMOR_HEARD

    # An invisible chest is hidden behind a wall, behind a pillar:
    def _grant_scroll(game_view, _):
        game_view.state = game_view.state._replace(message='You found\nan ancient scroll',
                                                   items=game_view.state.items + ('SCROLL',))
    mapscript_add_chest((6, 3, 15), 23, _grant_scroll)

    def _amulet_sight(game_view, _GameView):
        game_view.actions['GLIMPSE'] = _GameView(game_view.state._replace(
                message='You found a bright amulet\ndrifting in the canal water',
                msg_place=MessagePlacement.UP,
                treasure_id=35, items=game_view.state.items + ('AMULET',)))
    mapscript_add_trigger((6, 12, 3), _amulet_sight, facing='east', permanent=True,
                                      condition=lambda gs: 'AMULET' not in gs.items and gs.max_mp == 1)

    # Getting the templar statue blessing (+2 MP) is needed in order to be able to launch the BURN spell
    # and get rid of the 2 bone piles in the Templar Academy
    def _place_amulet_on_statue(game_view, _GameView):
        game_view.actions['AMULET'] = _GameView(game_view.state
                .with_tile_override(39, coords=(6, 9, 4))
                ._replace(message='You feel an inner warmth\nas you receive\nthe templars blessing\n(MP & max MP up!)',
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
        game_view.add_tile_override(3, coords=(10, 8, 4))  # as a side effect, unlock the door in the Academy to access this chest
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
            CR('Life drain', atk=14, hp_drain=True),
        ))

    # Maze warp tiles setup:
    mapscript_add_warp((10, 14, 1), (10, 9, 10))
    mapscript_add_warp((10, 11, 6), (10, 12, 8))
    # Removing all existing chests, that were behind locked doors:
    mapscript_remove_chest((10, 11, 2))  # used to be: Magic Emerald (+5 HP)
    mapscript_remove_chest((10, 13, 2))  # used to be: 100 gold
    # The treasure at the end of the maze:
    def _grant_rusty_sword(game_view, _):
        game_view.state = game_view.state._replace(message="You found\nthe Saint Knight\nrusty sword!", weapon=4,
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
    mapscript_add_boulder(trigger_pos=(10, 2, 12), start_at=(10, 2, 13), _dir='north')
    mapscript_add_chest((10, 2, 14), 'gold_60')  # The treasure behind the boulder
    # CHECKPOINT: finding 60$ in the chest is just enough to upgrade the sword and get a night of rest, before facing the skeleton

    #---------------------------
    # Entering: Canal Boneyard (map: 7 - checkpoint)
    #---------------------------
    # The heroine has 4/30 HP, 0/3 MP, 9 gold, boots, the HEAL & BURN spells and does 13 damages with their great sword.
    def _signal_portcullis(game_view, _):
        # Override default message indicating entered map name:
        music = BASE_MUSIC_URL + 'JanneHanhisuanto-OldCrypt.ogg'
        game_view.state = game_view.state._replace(message='You hear the portcullis\ngoing down behind you\n\n\n\nCanal Boneyard', music=music, music_btn_pos=PORTCULLIS_BTN_POS)
    mapscript_add_trigger((7, 2, 5), _signal_portcullis)  # one-time event/message

    # Entrance to Mausoleum is blocked by a zombie; required to win: full HP & full fire boost buff (+9 dmg)
    mapscript_add_enemy((7, 9, 5), 'zombie',
        hp=27, gold=5, rounds=(                # best moves:
            CR('Punch', atk=6, dodge=True),    # player ATTACK -> hero HP=24 | zombie HP=24
            CR('Bite', atk=8, hp_drain=True),  # player ATTACK -> hero HP=16 | zombie HP=10
            CR('Critical thump', atk=12),      # player ATTACK -> hero HP=4  | zombie VANQUISHED!
            CR('Bite', atk=10, dodge=True, hp_drain=True),
        ))

    mapscript_add_message((7, 2, 2), 'You might want to pray\non the grave\nof the Saint Knight.\nMay he rest in peace.')  # hint on sign in the water

    def _examine_glimpse(game_view, _GameView):
        game_view.actions['GLIMPSE'] = _GameView(game_view.state.with_hidden_trigger('SHORTCUT_HINT')._replace(message='A voice comes from the water:\n\n"There is a shortcut\nto the Mausoleum entrance\nabove the fire."'))
    mapscript_add_trigger((7, 4, 9), _examine_glimpse, facing='west', permanent=True,
                                     condition=lambda gs: 'SHORTCUT_HINT' not in gs.hidden_triggers)

    def _shortcut_above_fire_and_cauldron(game_view, _GameView):
        # Creating a shortcut to the Mausoleum entrance, starting the fight against the zombie with the current Atk Buff:
        if not game_view.tile_override((7, 13, 5)):
            log(game_view.state, 'drinking-cauldron')
            game_view.add_tile_override(40, coords=(7, 13, 5))
            msg = 'You drink the cauldron soup\nand feel stronger!\n\n'
            game_view.state = game_view.state._replace(message=msg, bonus_atk=10, sfx=SFX(id=4, pos=Position(64, 88)))
        trick = Trick('You climb on the roof\nand run to the\nMausoleum entrance!',
                      music=BASE_MUSIC_URL + 'JohanJansen-OrchestralLoomingBattle.ogg')
        game_view.actions[None] = _GameView(game_view.state._replace(x=9, y=5, facing='east', trick=trick, treasure_id=0))
        game_view.prev_page_trick_game_view = game_view.actions[None]
    mapscript_remove_chest((7, 13, 5))  # used to be: Magic Diamond (Def Up)
    mapscript_add_trigger((7, 13, 5), _shortcut_above_fire_and_cauldron, permanent=True)

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
        gs = game_view.state._replace(message='The path ends abrutly.\nA bottomless abyss\nopens at your feet')
        game_view.state = gs
        if 'ABYSS_BOTTOM' in gs.secrets_found:
            return
        # Adding hint as a trick at the bottom of the abyss.
        # The secret comes in the form of a shop, whose page ID is the reflection of the hint page one:
        # Because of this reverse_id enigma, this secret MUST be the first than can be found,
        # otherwise the current reverse ID attribution algorithm will burn
        trick = Trick('You hear a faint echo:\n"a secret lays,\nin the reflection\nof this place"',
                      filler_renderer=render_abyss_filler_page,
                      link=False, filler_pages=3, background='depths')
        secret_view = _GameView(gs.without_hidden_trigger('SHORTCUT_HINT')  # deduping as it is optionnal
                                  .with_secret('ABYSS_BOTTOM')
                                  ._replace(message='', trick=trick, reverse_id=True,
                                            mode=GameMode.DIALOG, shop_id=abyss_bottom().id))
        game_view.actions[None] = secret_view
        game_view.next_page_trick_game_view = secret_view
    mapscript_add_trigger((8, 3, 5), _edge_of_the_abyss, facing='north', permanent=True)

    def _lower_portcullis(game_view, _):  # block the way back, to avoid exploding #states
        log(game_view.state, 'lowering-portcullis')
        game_view.state = clear_hidden_triggers(game_view.state) # removes SHORTCUT_HINT & TOMB_HEALED
        game_view.add_tile_override(26, coords=(8, 5, 7))
        game_view.state = game_view.state._replace(message='You hear the portcullis\ngoing down behind you',
                                                   music=BASE_MUSIC_URL + 'AlexandrZhelanov-DarkHall.mp3',
                                                   music_btn_pos=PORTCULLIS_BTN_POS)
    mapscript_add_trigger((8, 6, 7), _lower_portcullis)  # one-time event/message

    mapscript_add_warp((8, 7, 10), (8, 10, 4))  # so that player get lost a bit
    mapscript_remove_chest((8, 3, 2))   # used to be: Magic Ruby (Atk Up) - replaced by mimic
    mapscript_remove_chest((8, 6, 9))   # used to be: 25 gold - moved up & replaced by mimic:
    mapscript_remove_chest((8, 3, 12))  # used to be: Magic Sapphire (MP Up)

    # 3 mimics possess the St Knight armor parts; required to win: UNLOCK spell + 1 MP each + enough HP (= 1 night of rest @ Inn)
    def _remove_chest(gs):
        assert gs.spellbook >= 3, f'Mimic @{gs.coords} beaten without UNLOCK spell!'
        return gs.with_tile_override(5, coords=gs.coords)
    mimic_stats = dict(
        hp=30, rounds=(
            CR('Lid clasp', atk=6),       # Hero must be able to stand this x3
            CR('Critical bite', atk=30),  # The hero must not be able to beat a mimic without the UNLOCK spell.
                                          # Knowing he can HEAL on 1st round, a quick way to ensure this is to one-shot him on 2nd round.
        ), post_victory=_remove_chest
    )
    mapscript_add_enemy((8, 7, 4), 'mimic', **mimic_stats, reward=RewardItem('ARMOR_PART', 38))

    def _grant_blue_key(game_view, _):
        game_view.state = game_view.state._replace(message="A blue key", items=game_view.state.items + ('BLUE_KEY',))
    mapscript_add_chest((8, 11, 9), 27, _grant_blue_key)    # hidden in hay pile

    def _smoke_fish_on_a_stick(game_view, _GameView):
        log(game_view.state, 'smoking fish-on-a-stick on torch flame')
        items = tuple(i for i in game_view.state.items if i != 'FISH_ON_A_STICK') + ('SMOKED_FISH_ON_A_STICK',)
        message = 'You bring your fish on a stick\nnear the flame for a moment'
        game_view.actions['FISH_ON_A_STICK'] = _GameView(game_view.state._replace(
                items=items,
                treasure_id=32,
                message=message,
                msg_place=MessagePlacement.UP))
    mapscript_add_trigger((8, 11, 7), _smoke_fish_on_a_stick, facing='east', permanent=True,
                                      condition=lambda gs: 'FISH_ON_A_STICK' in gs.items)

    goblin_bribes = (
        Bribe(item='FISH', successful=False, result_msg='"Yummy fish! But... yuck!\nToo slimy to eat by hand!"'),
        Bribe(item='FISH_ON_A_STICK', successful=False, result_msg='"Yummy fish! But... yuck!\nIt is raw! Disgusting!"'),
        Bribe(item='SMOKED_FISH_ON_A_STICK', result_msg='He takes it and leaves'),
    )
    mapscript_add_enemy((8, 10, 11), 'goblin',  # MUST be bribed
        category=ENEMY_CATEGORY_BEAST, bribes=goblin_bribes,
        hp=10, rounds=(CR('Dagger cut', atk=4),))

    def _open_locked_door_with_key(game_view, _GameView):
        gs = game_view.state
        new_game_view = _GameView(gs._replace(items=tuple(i for i in gs.items if i != 'BLUE_KEY')))
        game_view.actions['BLUE_KEY'] = new_game_view
        if not new_game_view.tile_override((8, 4, 12)):  # avoid re-adding override if GameView already exists
            log(gs, 'opening-door-to-portal')
            new_game_view.add_tile_override(5, coords=(8, 4, 12))
    mapscript_add_trigger((8, 5, 12), _open_locked_door_with_key, facing='west', permanent=True,
                                      condition=lambda gs: 'BLUE_KEY' in gs.items)

    # CHECKPOINT: about to find scroll & pass through portal back to Cedar Village
    # Sage Therel will trade the scroll for the UNLOCK spell
    mapscript_add_message((8, 3, 12), 'Trust your instinct:\nno need to go back for now', facing='west',
                                      condition=is_instinct_preventing_to_pass_mausoleum_portal)
    mapscript_add_message((5, 9, 4), 'Trust your instinct:\nno need to go back for now', facing='north',
                                      condition=is_instinct_preventing_to_pass_village_portal)

    mapscript_add_enemy((8, 3, 2), 'mimic', **mimic_stats, reward=RewardItem('ARMOR_PART', 39),
                                            hidden_trigger='FOUNTAIN_HINT')
    mapscript_add_enemy((8, 9, 3), 'mimic', **mimic_stats, reward=RewardItem('ARMOR_PART', 40))

    # CHECKPOINT: about to enter the Dead Walkways and fight the storm dragon, with the St Knight armor

    #---------------------------
    # Entering: Dead Walkways (map: 9 - checkpoint)
    #---------------------------
    # The heroine has 0/3 MP, 3/4 gold, boots, the HEAL, BURN & UNLOCK spells, St Knight armor (def 12) and does 13 dmg with their sword.
    # Pre-dragon-fight avatar has 12 HP.
    def _ensure_beaten_with_st_knight_armor(gs):
        assert gs.armor > 1, 'Hero should have the St Knight armor to beat the Storm Dragon'
    mapscript_add_enemy((9, 2, 5), 'storm_dragon',  # required to win: St Knight armor, great sword & > 11 HP
        category=ENEMY_CATEGORY_BEAST,
        hp=38, max_rounds=6, rounds=(             # best moves:
            CR('Tail slap', atk=13),              # player ATTACK -> hero HP=11 | dragon HP=25
            CR('Wing thump', atk=12, dodge=True), # player ATTACK -> hero HP=10 | dragon HP=25
            CR('Critical bite', atk=17),          # player ATTACK -> hero HP=5  | dragon HP=12
            CR('Bite', atk=14),                   # player ATTACK -> hero HP=3  | dragon HP=-1
        ), post_victory=_ensure_beaten_with_st_knight_armor)
    # Post-dragon-fight avatar has 3 HP.

    goblin_bribe = Bribe(gold=3, result_msg='He runs away with your gold')
    mapscript_add_enemy((9, 3, 3), 'goblin',  # deal is a red-herring, run away if fought
        intro_msg="I'll give you the door key\nfor 3 gold, mylady.",
        category=ENEMY_CATEGORY_BEAST, bribes=(goblin_bribe,), hp=10, rounds=(CR('', run_away=True),))

    mapscript_add_enemy((9, 3, 7), 'druid',   # ask for mercy if fought -> restore hero HP/MP
        hp=40, rounds=(
            CR('Dagger slash', atk=7),
            CR('Life drain', atk=12, hp_drain=True),
            CR('', ask_for_mercy=('Mercy! Spare me!',
                                  # The gold reset to zero helps limiting the #states
                                  lambda gs: gs._replace(gold=0, hp=gs.max_hp, mp=gs.max_mp, treasure_id=25,
                                                         message='"Thank you noble lady!\nLet me heal you in return."\n(you give him your last coins)'))),
            CR('', miss=True),
        ))

    def _pass_arch1(game_view, _):
        msg = 'The Empress voice echoes:\n'
        msg += '\n"Go away, impostor!\nYou have nothing of a knight!"\n'
        # Doing a bit of unnecessary state cleanup:
        game_view.state = game_view.state._replace(tile_overrides=(((9, 4, 5), 26),),  # portcullis block the way back
                                                   triggers_activated=(game_view.state.coords,),
                                                   vanquished_enemies=(),
                                                   message=msg)
    mapscript_add_trigger((9, 5, 5), _pass_arch1)

    def _grant_buckler(game_view, _GameView):
        if 'BUCKLER' in game_view.state.items:
            log_path_to(game_view, map_as_string=map_as_string, stop_at_cond=lambda gv: 'BUCKLER' not in gv.state.items)
            assert False
        game_view.state = game_view.state._replace(message="A buckler", items=game_view.state.items + ('BUCKLER',))
    mapscript_add_chest((9, 6, 9), 33, _grant_buckler)

    def _pass_arch2(game_view, _):
        msg = '\n\n\n\nThe Empress voice echoes:\n'
        msg += '\n"My love, the champion knight,\ndied a hero to save this\ndamn realm. You\'re a joke\ncompared to him!"'
        # Doing some tile_overrides cleanup to avoid #states branching due to boxes:
        game_view.state = game_view.state._replace(tile_overrides=(((9, 7, 2), 26),),  # portcullis block the way back
                                                   message=msg)
    mapscript_add_trigger((9, 8, 2), _pass_arch2)

    # Block access to the Empress boss; required to win: full HP & St Knight armor & a bucklet
    def _ensure_beaten_with_buckler(gs):
        assert 'BUCKLER' in gs.items, 'Demon Seamus beaten without buckler!'
        assert gs.hp == 16
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
        reward=RewardTreasure('Magic Diamond found\n(MP restored)', 15, lambda gs: gs._replace(mp=gs.max_mp)),
        post_victory=_ensure_beaten_with_buckler
    )

    def _last_empress_words(game_view, _):
        msg = '\nThe Empress voice echoes:\n\n"You\'re an insult\nto his memory,\nprepare to die!"\n'
        game_view.state = game_view.state._replace(message=msg)
    mapscript_add_trigger((9, 9, 5), _last_empress_words)  # one-time message

    # The heroine has 16/30HP, 3/3 MP, the HEAL, BURN & UNLOCK spells, a BUCKLER, St Knight armor (def 12) and does 13 dmg with their sword.
    mapscript_add_enemy((9, 11, 5), 'death_speaker',  # Empress
        music=BASE_MUSIC_URL + 'MatthewPablo-HeroicDemise.mp3',
        # STRATEGY to beat her: parry lightning attacks, use 2 BURN to put shield down, 1 HEAL, else attack
        # Note that the Empress is of DEMON type, so BURN does her only 4 dmg (it ignores the shield)
        hp=34, max_rounds=11, rounds=(                       # best moves:
            CR('Bone shield!', boneshield_up=True, atk=15),  # player ATTACK -> hero HP=13 | empress HP=21
            CR('Death voice!', atk=24,                       # player BURN -> hero HP=1    | empress HP=17
               sfx=SFX(id=8, pos=Position(64, 6))),
            CR('Dark lightning!', atk=38,                    # player PARRY -> hero HP=1   | empress HP=17
               sfx=SFX(id=2, pos=Position(64, 42))),
            # Bone shield                                    # player HEAL -> hero HP=17   | empress HP=17
            # Death voice                                    # player BURN -> hero HP=5    | empress HP=13
            # Dark lightning                                 # player PARRY -> hero HP=5   | empress HP=13
            # Bone shield                                    # player ATTACK -> hero HP=2  | empress HP=0
        ), post_victory=lambda gs: gs._replace(mode=GameMode.DIALOG, shop_id=the_end().id))


def render_abyss_filler_page(pdf, i):
    pdf.add_page()
    pdf.image(REL_RELEASE_DIR + 'images/backgrounds/black.png', x=0, y=0)
    if i == 1: pdf.image('assets/blobfish.png', x=53, y=30)


def render_post_defeat_hint(pdf):
    bitfont_set_color_red(False)
    pdf.add_page()
    pdf.image(REL_RELEASE_DIR + 'images/backgrounds/black.png', x=0, y=0)
    bitfont_render(pdf, 'Tip', 80, 5, Justify.CENTER)
    render_bar(pdf, 10, 20)
    white_arrow_render(pdf, 'BACK', 16, 16)
    bitfont_render(pdf, 'If you cannot bring an enemy\nlifebar to zero before\nloosing your last HP,\nmaybe an item somewhere\ncan help you.', 80, 40, Justify.CENTER, page_id=1)
    bitfont_render(pdf, 'Start over', 80, 100, Justify.CENTER, page_id=1)


def clear_hidden_triggers(gs):
    return gs._replace(hidden_triggers=tuple(ht for ht in gs.hidden_triggers if ht in ('BEEN_TO_VILLAGE', 'FIRST_NIGHT_OF_REST')))  # Those are the only ones that need to be preserved until 2nd visit to village
