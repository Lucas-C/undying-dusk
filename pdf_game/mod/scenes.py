# pylint: disable=import-outside-toplevel
from functools import lru_cache as cached

from . import Proxy

from ..entities import CutScene, DialogButtonType, DialogOption, GameMode, Position, SFX


BASE_MUSIC_URL = 'https://chezsoi.org/lucas/undying-dusk/music/'


def patch_shop(shop, shop_id):
    if not shop:
        return CutScene.from_id(shop_id)
    if shop.name == 'A Nightmare':  # shop 8 == intro
        # return reader_history_depth_test(shop_id)
        return intro(shop_id)
    if shop.name == 'Woodsman':  # shop 4 on Monastery Trail
        return chapel_in_the_woods(shop_id)
    if shop.name == 'Cedar Arms':  # shop 0 at Cedar Village
        return Proxy(background=shop.background, name=shop.name, item=[
            CedarArmsSellableSwordUpgrade,
        ])
    if shop.name == 'Simmons Fine Clothier':  # shop 1 at Cedar Village
        return Proxy(background=shop.background, name=shop.name, item=[
            SimmonsSellableBoots,
            SimmonsSellableArmor,
        ])
    if shop.name == 'Sage Therel':  # shop 3 at Cedar Village
        return Proxy(background=shop.background, name=shop.name, item=[
            SageTherelAdvice,
            SageTherelSellableSpell,
        ])
    if shop.name == 'The Pilgrim Inn':  # shop 2 at Cedar Village
        return Proxy(background=shop.background, name=shop.name, item=[
            PilgrimInnAdvice,
            RoomForTheNight,
        ])
    raise NotImplementedError(f'Shop not handled: {shop.name}')


@cached()
def reader_history_depth_test(_, depth=60):
    scene = CutScene.new(text='0')
    for i in range(1, depth + 1):
        scene = CutScene.new(text=str(i), next_scene_id=scene.id)
    return scene

@cached()
def intro(scene_id):
    # Original intro: "Darkness has overtaken\nthe human realm.\n\nThe monastery is no\nlonger safe."
    # This cannot be placed at the top of the module to avoid a circular import:
    # pylint: disable=import-outside-toplevel
    from ..bitfont import bitfont_render, Justify
    intro_8 = CutScene.new(
        text='In fact,\napart from\nthat peculiar detail,\nyou have lost\nall memory.',
        justify=Justify.CENTER,
        exit_msg='Wake up',
    )
    def dream_extra_render(pdf):
        pdf.image('assets/dominik-small.png', x=63, y=0)
        bitfont_render(pdf, 'You dream a long dream.\n\nAs it ends\nthe only thing you remember\nis the face of a man.', 80, 55, Justify.CENTER)
    intro_7 = CutScene.new(
        extra_render=dream_extra_render,
        next_scene_id=intro_8.id,
    )
    intro_6 = CutScene.new(
        text='\n\nYou drink the thick,\nharsh liquid.\n\nA sudden torpor\nseizes you.\n\nYou fall asleep.',
        justify=Justify.CENTER,
        next_scene_id=intro_7.id,
    )
    intro_6b = CutScene.new(# Duplicate, so that it isn't immediately obvious that both links point to the same page
        text='\n\nYou drink the thick,\nharsh liquid.\n\nA sudden torpor\nseizes you.\n\nYou fall asleep.',
        justify=Justify.CENTER,
        next_scene_id=intro_7.id,
    )
    intro_5 = CutScene.new(
        dialog_options=(
            DialogOption.only_link(DialogButtonType.DRINK_RED,   intro_6.id),
            DialogOption.only_link(DialogButtonType.DRINK_GREEN, intro_6b.id),
        ),
        no_exit=True,
        extra_render=seamus_speaks('Which one do you choose ?'),
    )
    intro_4 = CutScene.new(
        extra_render=seamus_speaks('The green phial\non the other hand\nmay allow you to fix it all,\nat the price of your life.\nAnd maybe more.'),
        next_scene_id=intro_5.id,
    )
    intro_3 = CutScene.new(
        extra_render=seamus_speaks('Drink the red phial\nand this tragedy\nwill be no more.\nYou will be free at last\nof this burden.'),
        next_scene_id=intro_4.id,
    )
    intro_2 = CutScene.new(
        extra_render=seamus_speaks('I found what you asked for.\n\nThe time has come\nto make a decision.'),
        next_scene_id=intro_3.id,
    )
    return CutScene.new(id=scene_id,
        music=BASE_MUSIC_URL + 'AlexandrZhelanov-Audience.ogg',
        extra_render=seamus_speaks('My respects, my lady'),
        next_scene_id=intro_2.id,
    )

@cached()
def seamus_through_small_window():
    dialog_5 = CutScene.new(
        extra_render=seamus_speaks('In case of trouble\nuse your arcane talent:\nALT KEY + LEFT ARROW KEY \nwill rewind time', behind_bars=True),
        # treasure_id=32,
    )
    dialog_4 = CutScene.new(
        extra_render=seamus_speaks('You must get out\nand meet me at the door.\n\nFirst off, find a way\nbehind those boxes.', behind_bars=True),
        next_scene_id=dialog_5.id,
    )
    dialog_3 = CutScene.new(
        extra_render=seamus_speaks("For your safety I brought\nyou inside this Monastery.\nBut I can't come back inside,\nas the monks have turned\ninto demons!", behind_bars=True),
        next_scene_id=dialog_4.id,
    )
    dialog_2 = CutScene.new(
        extra_render=seamus_speaks('Something terrible\nis happening...\nTime has stopped,\nand people are transforming\ninto monsters!', behind_bars=True),
        next_scene_id=dialog_3.id,
    )
    return CutScene.new(
        extra_render=seamus_speaks("Pssst, here!\n\nIt's me, Seamus.", behind_bars=True),
        next_scene_id=dialog_2.id,
    )


@cached()
def entering_monastery_courtyard():
    minimap_tip = CutScene.new(
        name='Tip',
        text='\n' * 7 + 'Use the minimap\non the INFO page\nto help orient\nyourself',
        extra_render=lambda pdf: pdf.image('minimaps/map_1___.png', x=67, y=15),
        exit_msg='Enter courtyard',
    )
    return CutScene.new(
        background=1,
        text='\n' * 15 + 'As you step outside,\nyou notice\na strange phenomenon\non the horizon:\nthe sun is stuck\nin a never-ending dusk.',
        music=BASE_MUSIC_URL + 'Yubatake-M31.ogg',
        next_scene_id=minimap_tip.id,
    )


@cached()
def tuto_spells():
    return CutScene.new(
        text = '\n' * 10 + 'Spell casting costs 1 MP.\n\nThe "HEAL" spell\ncan only be used\nduring battles.\n\nAn icon will show up\nwhen you can use\nother spells elsewhere.',
        sfx=SFX(id=9, pos=Position(120, 34))
    )


@cached()
def looking_for_hope():
    dialog_4 = CutScene.new(
        background='valley_village_with_seamus',
        extra_render=seamus_speaks2("Now you should try to reach\nthe village back there.\nI will meet you later,\nin Zuruth plains.\nBeware, the woods\nare dangerous now.\n\nGood luck."),
        exit_msg='Take the road',
    )
    dialog_3 = CutScene.new(
        background='valley_village_with_seamus',
        dialog_options=(
            DialogOption.only_msg('You feel your body\ngetting stronger.\n(HP & max HP up!)' + '\n' * 3),
            # Using a custom DialogOption to be able to alter GameState:
            DialogOption(btn_type=DialogButtonType.NEXT, msg='', can_buy=True,
                         buy=lambda gs: gs.without_hidden_trigger('TALKED_TO_SEAMUS, ')
                                          ._replace(max_hp=gs.max_hp + 5, hp=gs.hp + 5, shop_id=dialog_4.id))),
        sfx=SFX(id=3, pos=Position(64, 88)),
        no_exit=True,
    )
    dialog_2 = CutScene.new(
        background='valley_village_with_seamus',
        extra_render=seamus_speaks2("Despite your shattered\nmemory, you even managed\nto learn a spell!\n\n\nI do not have\nmuch more magic myself,\nbut let me try something..."),
        next_scene_id=dialog_3.id,
    )
    return CutScene.new(
        background='valley_village_with_seamus',
        name='Looking for hope',
        music=BASE_MUSIC_URL + 'AlexandrZhelanov-MysteryForest.mp3',
        extra_render=seamus_speaks2('\nWell done!\n\nThese demons got\nwhat they deserved!\nYou had no choice;\nno one touched by\nthe Empress\'s curse\ncan be saved...'),
        next_scene_id=dialog_2.id,
    )


@cached()
def chapel_in_the_woods(scene_id):
    # Original: "I'm staying right here" "until the sun comes back."
    chapel_closed = CutScene.new(
        name='Chapel In The Woods',
        text='\n' * 13 + 'Get out!\nMy hunger is growing...',
        extra_render=lambda pdf: pdf.image('assets/monk-portrait.png', x=48, y=12),
        exit_msg='Leave',
    )
    crucifix_taken = CutScene.new(
        name='Chapel In The Woods',
        background='chapel_with_monk',
        text='\n' * 7 + 'What have you done?\n\n\nNow the Empress\'s curse\nwill befall us!\n\nFool!',
        treasure_id=36,
        exit_msg='Leave',
    )
    def take_crucifix(gs):
        is_imp_beaten = (4, 7, 10) in gs.vanquished_enemies
        if is_imp_beaten or 'HOLY_WATER' in gs.items or 'FULL_BOTTLE' in gs.items:
            # The monk already blessed your water, or we prevent a case where where the monk won't bless the water,
            # because we stole the crucifix,  and we could not bless a bottle already full of water from the well:
            return gs._replace(message='Please leave that be.\nIt wards this chapel.')
        assert 'CRUCIFIX_STOLEN' not in gs.hidden_triggers
        return gs.with_hidden_trigger('CRUCIFIX_STOLEN')._replace(items=gs.items + ('CRUCIFIX',),
                                                                  shop_id=crucifix_taken.id)
    def talk_with_monk(gs):
        is_imp_beaten = (4, 7, 10) in gs.vanquished_enemies
        if is_imp_beaten or 'HOLY_WATER' in gs.items: # the monk already blessed your water
            return gs._replace(message='I wish you luck\nin your quest.')
        if 'FULL_BOTTLE' in gs.items:
            def render_holy_water(pdf):
                from ..render_treasure import treasure_render_item
                treasure_render_item(pdf, 22, pos=Position(64,70))
            return gs._replace(items=tuple(i for i in gs.items if i != 'FULL_BOTTLE') + ('HOLY_WATER',),
                               message='I bless this water.\nMay it serve you well.', extra_render=render_holy_water)
        return gs._replace(message='If you bring me water,\nI can bless it for you.')
    return CutScene.new(
        id=scene_id,
        name='Chapel In The Woods',
        background='chapel_empty',
        dialog_options=(DialogOption(btn_type=DialogButtonType.TAKE_CRUCIFIX, msg='',
                                     can_buy=True, buy=take_crucifix),
                        DialogOption(btn_type=DialogButtonType.TALK_WITH_MONK,
                                     msg='A monk prays silently\non the left side.',
                                     can_buy=True, buy=talk_with_monk),),
        music= BASE_MUSIC_URL + 'AlexandrZhelanov-CavesOfSorrow.ogg',
        redirect=lambda gs: chapel_closed if 'CRUCIFIX_STOLEN' in gs.hidden_triggers else None,
    )


@cached()
def a_safe_haven():
    return CutScene.new(
        name='A safe haven',
        background='cloudy_town',
        text='\n' * 5 + 'A village seems to\nhave been spared.\n\nPeople welcome you\nand ask for your help\nagainst the monsters.',
        music=BASE_MUSIC_URL + 'AngusMacnaughton-FantasyMusic-NightTown.mp3',
        exit_msg='Enter town',
    )


@cached()
def the_inn_evening_tale():
    tale_6 = CutScene.new(
        name='The inn evening tale',
        background='st_knight_tale_5',
        dialog_options=(DialogOption.only_msg('\nFor many years,\nall was great again.\n\nUntil the day\nhe passed away...'),
                        # Using a custom DialogOption to be able to alter GameState:
                        DialogOption.exit('Go to sleep', lambda gs: gs._replace(message='You have rested'))),
    )
    tale_5 = CutScene.new(
        name='The inn evening tale',
        background='st_knight_tale_1',
        text='The young man became\nthe realm protector,\n\nthe Saint Knight',
        next_scene_id=tale_6.id,
    )
    tale_4 = CutScene.new(
        name='The inn evening tale',
        background='st_knight_tale_4',
        text='\n' * 12 + "To everyone's surprise,\nthe storm dragon was\nindeed finally beaten.",
        next_scene_id=tale_5.id,
    )
    tale_3 = CutScene.new(
        name='The inn evening tale',
        background='st_knight_tale_3',
        text='\nA young templar came,\npretending he would\nslay the beast.\nPeople laughed at him.' + '\n' * 2,
        next_scene_id=tale_4.id,
    )
    tale_2 = CutScene.new(
        name='The inn evening tale',
        background='st_knight_tale_2',
        text='\n' * 18 + 'The storm dragon.\nViolence. Death. Terror.\nA relentless scourge\nupon us.',
        next_scene_id=tale_3.id,
    )
    return CutScene.new(
        name='The inn evening tale',
        background='st_knight_tale_1',
        text='Our realm was at peace,\nuntil IT came.',
        music=BASE_MUSIC_URL + 'MatthewPablo-TheFallOfArcana.mp3',
        next_scene_id=tale_2.id,
    )


@cached()
def seamus_in_zuruth_plains():
    dialog_3 = CutScene.new(
        background='forest_trees_with_seamus',
        extra_render=seamus_speaks2('And secrets may be hiding\nin its pillars shadow...\n\nThe Empress\'s castle stands\nfurther behind the canal.\n\nGo look if you can see it\ndespite the darkness.'),
        # Using a custom DialogOption to be able to alter GameState:
        dialog_options=(DialogOption.exit('Leave', lambda gs: gs.with_tile_override(6, (6, 1, 9))),),
    )
    dialog_2 = CutScene.new(
        background='forest_trees_with_seamus',
        extra_render=seamus_speaks2('You may want to explore the\nTemplar Academy nearby...\n\nIt is abandoned,\nbut old relics\nlay there,\nforgotten.'),
        next_scene_id=dialog_3.id,
    )
    return CutScene.new(
        background='forest_trees_with_seamus',
        extra_render=seamus_speaks2('\nCongratulations\non making it\nthis far!'),
        next_scene_id=dialog_2.id,
    )


@cached()
def risking_it_all():
    scene_6 = CutScene.new(
        background='distant_castle',
        name='Risking it all',
        dialog_options=(DialogOption.only_msg('May the guardian lady\nwatch over you!'),
                        # Using a custom DialogOption to be able to alter GameState:
                        DialogOption.exit('Walk towards the castle',
                                          lambda gs: gs._replace(items=gs.items + ('ARMOR_PART',),
                                                                 # Entering Canal Boneyard:
                                                                 map_id=7, x=2, y=5))),
    )
    scene_5 = CutScene.new(
        background='distant_castle',
        name='Risking it all',
        text='Then I offer you\nthis first fragment:',
        treasure_id=37,
        next_scene_id=scene_6.id,
    )
    scene_4 = CutScene.new(
        background='distant_castle',
        name='Risking it all',
        text='\n' * 4 + 'Will you walk in the\nSaint Knight\'s\nfootsteps?\n\nMaybe even restore\nhis shattered armor?',
        next_scene_id=scene_5.id,
    )
    scene_3 = CutScene.new(
        background='distant_castle',
        name='Risking it all',
        text='\n' * 4 + 'A foolish hope\ncomes to my mind:\n\nCould you defy\nthe Empress herself?',
        next_scene_id=scene_4.id,
    )
    scene_2 = CutScene.new(
        background='hangman',
        extra_render=seamus_speaks('You rid the plains\nof all the monsters.\nYour bravery will be praised!\nYou really deserve\nthis legendary blade.'),
        next_scene_id=scene_3.id,
    )
    scene_1 = CutScene.new(
        background='hangman',
        extra_render=seamus_speaks('Impressive my lady!\nYou are a sly arcanist,\nand a fine sword.'),
        next_scene_id=scene_2.id,
    )
    scene_0 = CutScene.new(
        background='hangman',
        extra_render=skeleton_speaks(with_explosion=True),
        next_scene_id=scene_1.id,
    )
    return CutScene.new(
        background='hangman',
        extra_render=skeleton_speaks('Noooooo!'),
        next_scene_id=scene_0.id,
    )


@cached()
def abyss_bottom():  # Did the Empress made a pact with the Deep Ones?
    return CutScene.new(
        name='Abyss bottom',
        text='The soul of the empress\nrests in the dark\n(you found a SECRET)',
        sfx=SFX(id=6, pos=Position(64, 78)),
        exit_msg='Climb back up',
        music=BASE_MUSIC_URL + 'AlexandrZhelanov-MysticalTheme.mp3',
    )


@cached()
def the_final_leap():
    scene_2 = CutScene.new(
        background=1,
        name='The final leap',
        text='\n' * 8 + "You reach the Empress's\nquarters: there is only\ndarkness and ruins.\n\nAs you climb your way\namong floating debris,\na huge creature falls\nfrom the sky onto you!",
        exit_msg="Engage the fight",
    )
    return CutScene.new(
        background='palace_hall',
        name='The final leap',
        text='\n' * 3 + 'You leave the mausoleum\nand warily enter\nthe castle above.\n\nThe palace is empty.\nThere is no living soul.',
        music=BASE_MUSIC_URL + 'JohanJansen-DarkWinds.ogg',
        next_scene_id=scene_2.id,
    )


@cached()
def seamus_transformation():
    poor_seamus = CutScene.new(
        dialog_options=(DialogOption.only_msg("The Empress...\nYou...\nOh no.\nThe curse... I can't...\n...my...\nlaaaaadyyy..."),
                        DialogOption.exit('Step back',
                                          lambda gs: gs.with_hidden_trigger('SEAMUS_TRANSFORMED')
                                                       .with_tile_override(1, (9, 9, 3)))),
    )
    return CutScene.new(
        extra_render=seamus_speaks('You made it.\n\nDid you expect to...\nWait.\nWhat is happening to me...'),
        next_scene_id=poor_seamus.id,
    )


@cached()
def the_end():
    scene_9 = CutScene.new(
        background='bloodsplat',
        text='At least, one last time,\nyou met your only love.',
        exit_msg='Dominik.',
    )
    scene_8 = CutScene.new(
        background='bloodsplat',
        text='As your eyes\nslowly close,\na faint smile raises\non your lips.',
        next_scene_id=scene_9.id,
    )
    scene_7 = CutScene.new(
        background='bloodsplat',
        text='\n\n\nWith your talent\nto alter time,\ncould you have caused\nall this?\n\nDid Seamus know?',
        next_scene_id=scene_8.id,
    )
    scene_6 = CutScene.new(
        background='bloodsplat',
        text='Is the curse lifted?\nWill time flow again?',
        next_scene_id=scene_7.id,
    )
    scene_5 = CutScene.new(
        background='bloodsplat',
        text='\nAs you lay on the floor,\nbleeding,\nfatally wounded,\nyou wonder...',
        next_scene_id=scene_6.id,
    )
    scene_4 = CutScene.new(
        background='the_end_2',
        text='You are not\nthe Empress!' + '\n' * 5,
        next_scene_id=scene_5.id,
    )
    scene_3 = CutScene.new(
        background='the_end_2',
        text='\n\n\nNo.\n\nImpossible.',
        next_scene_id=scene_4.id,
    )
    scene_2 = CutScene.new(
        background='the_end_1',
        text='\nYou look\ncloser.',
        next_scene_id=scene_3.id,
    )
    scene_1 = CutScene.new(
        background='the_end_1',
        text="Something's\nodd..." + '\n' * 5,
        next_scene_id=scene_2.id,
    )
    return CutScene.new(
        text='\n\nThe Empress finally\ndefeated,\nyou look over her.\n\nA cheval mirror\nis standing behind her.',
        music=BASE_MUSIC_URL + 'MatthewPablo-Soliloquy.mp3',
        next_scene_id=scene_1.id,
    )


def seamus_speaks(text, behind_bars=False):  # Seamus portrait speaking
    # This cannot be placed at the top of the module to avoid a circular import:
    # pylint: disable=import-outside-toplevel
    from ..bitfont import bitfont_render, Justify
    from ..render_utils import portrait_render
    def extra_render(pdf):
        portrait_render(pdf, 0, x=66, y=16)
        if behind_bars:
            pdf.image('assets/window-bars.png', x=62, y=13)
        bitfont_render(pdf, text, 80, 58, Justify.CENTER)
    return extra_render

def skeleton_speaks(text='', with_explosion=False):  # Skeleton portrait speaking
    # This cannot be placed at the top of the module to avoid a circular import:
    # pylint: disable=import-outside-toplevel
    from ..bitfont import bitfont_render, Justify
    from ..render_utils import portrait_render
    def extra_render(pdf):
        portrait_render(pdf, 1, x=66, y=22)
        if text:
            bitfont_render(pdf, text, 80, 58, Justify.CENTER)
        if with_explosion:
            pdf.image('assets/explosion.png', x=54, y=0)
    return extra_render

def seamus_speaks2(text):  # Seamus character, standing up on the left, speaking
    # This cannot be placed at the top of the module to avoid a circular import:
    # pylint: disable=import-outside-toplevel
    from ..bitfont import bitfont_render, Justify
    return lambda pdf: bitfont_render(pdf, text, 158, 18, Justify.RIGHT)


class CedarArmsSellableSwordUpgrade:
    @staticmethod
    def dialog_option(game_state):
        if game_state.weapon == 7:
            if game_state.tile_override_at((5, 9, 3)):  # VILLAGE_PORTAL_COORDS
                return DialogOption.only_msg('Take down the empress,\nfor all of our safety.')
            return DialogOption.only_msg('No creature of darkness\ncan match this weapon!')
        return DialogOption(btn_type=DialogButtonType.BUY, can_buy=game_state.weapon == 4 and game_state.gold >= 50,
                            msg="Polish a rusty sword\nfor 50 gold",
                            buy=lambda gs: gs._replace(gold=gs.gold - 50,
                                                       treasure_id=21, weapon=7,
                                                       message="Acquired Great Sword"))


class SimmonsSellableBoots:
    @staticmethod
    def dialog_option(game_state):
        if 1 <= game_state.items.count('ARMOR_PART'):
            return DialogOption.only_msg('I recognize that armor!\nIs it The Saint knight\'s?')
        if 'BOOTS' in game_state.items:
            return DialogOption.only_msg('')
        can_buy = game_state.gold >= 20
        assert not can_buy or game_state.weapon >= 4, f'Boots should not be buyable before beating the druid: gold={game_state.gold} weapon={game_state.weapon}'
        return DialogOption(btn_type=DialogButtonType.BUY, can_buy=can_buy, msg="Boots to pass shallow\nwater for 20 gold",
                            buy=lambda gs: gs._replace(gold=gs.gold - 20,
                                                       treasure_id=24, items=gs.items + ('BOOTS',),
                                                       message="Bought waterproof Boots"))

def render_armor(pdf):
    from ..render_treasure import treasure_render_item
    treasure_render_item(pdf, 29, pos=Position(64,46))

class SimmonsSellableArmor:
    @staticmethod
    def dialog_option(game_state):
        if game_state.armor > 1:
            return DialogOption.only_msg('Always happy to work\nsuch marvelous metal.')
        if 1 <= game_state.items.count('ARMOR_PART') < 4:
            return DialogOption.only_msg('I can repair it, but\nI\'ll need more pieces')
        if game_state.items.count('ARMOR_PART') == 0:
            return DialogOption(btn_type=DialogButtonType.BUY, can_buy=game_state.items.count('ARMOR_PART') == 4,
                            msg="I can repair armor\nfrom broken parts",
                            buy=lambda gs: gs._replace(armor=7,
                                                       items=tuple(i for i in gs.items if i != 'ARMOR_PART'),
                                                       message="Acquired\nthe Saint Knight's armor",
                                                       extra_render=render_armor))
        return DialogOption(btn_type=DialogButtonType.BUY, can_buy=game_state.items.count('ARMOR_PART') == 4,
                            msg="Please let me restore\nit to its former glory.",
                            buy=lambda gs: gs._replace(armor=7,
                                                       items=tuple(i for i in gs.items if i != 'ARMOR_PART'),
                                                       message="Acquired\nthe Saint Knight's armor",
                                                       extra_render=render_armor))


class SageTherelAdvice:
    @staticmethod
    def dialog_option(game_state):
        if not game_state.tile_override_at((5, 9, 3)):  # VILLAGE_PORTAL_COORDS
            return DialogOption.only_msg('Fire magic is effective\nagainst undead and bone.')
        return DialogOption.only_msg("You opened a magic\nportal, I'm impressed!")


class SageTherelSellableSpell:
    @staticmethod
    def dialog_option(game_state):
        if 'SCROLL' in game_state.items:
            if game_state.spellbook < 2:
                return DialogOption(btn_type=DialogButtonType.BUY, can_buy=True, msg="I will teach it to you\nif you give me the scroll.",
                                    # no more Seamus in Zuruth plains (branching paths optimization)
                                    buy=lambda gs: gs.with_tile_override(6, (6, 1, 9), exist_ok=True)
                                                     .with_trigger_activated((6, 1, 9))
                                                     ._replace(items=tuple(i for i in gs.items if i != 'SCROLL'),
                                                               spellbook=2, message='New spell learned: BURN'))
            if game_state.spellbook < 3:
                return DialogOption(btn_type=DialogButtonType.BUY, can_buy=True, msg="For another scroll, I can\nteach you a thief spell.",
                                    buy=lambda gs: gs._replace(items=tuple(i for i in gs.items if i != 'SCROLL'),
                                                               spellbook=3, message='New spell learned: UNLOCK'))
            assert False, 'Sage There has no more spell to teach'
        if game_state.spellbook < 2:
            return DialogOption(btn_type=DialogButtonType.BUY, can_buy=False, msg="I can teach it to you\nif you bring me a scroll.")
        return DialogOption.only_msg('Use your new power\nwisely, young apprentice')

class PilgrimInnAdvice:
    @staticmethod
    def dialog_option(game_state):
        if not game_state.tile_override_at((5, 9, 3)):  # VILLAGE_PORTAL_COORDS
            return DialogOption.only_msg('We saw dead walking\nfrom the Canal Boneyard.')
        return DialogOption.only_msg("Thank you for taking\ncare of that Gorgon!")

class RoomForTheNight:
    @staticmethod
    def dialog_option(game_state):
        # Replicates shop_set_room / shop_buy_room:
        disable_reason, room_cost = '', 10
        if game_state.hp == game_state.max_hp and game_state.mp == game_state.max_mp:
            disable_reason = "(You are well rested)"
        msg = "Buy a room for the night"
        # show the gold cost or the reason you can't
        msg += f'\n{disable_reason}' if disable_reason else f'\nfor {room_cost} gold'
        # display the dialog button if the item can be purchased
        can_buy = game_state.gold >= room_cost and not disable_reason
        def buy(gs):
            gs = gs._replace(message="You have rested", gold=gs.gold - room_cost,
                             hp=gs.max_hp, mp=gs.max_mp)
            if 'FIRST_NIGHT_OF_REST' not in gs.hidden_triggers:
                gs = gs.with_hidden_trigger('FIRST_NIGHT_OF_REST')\
                       ._replace(mode=GameMode.DIALOG, shop_id=the_inn_evening_tale().id, message='')
            return gs
        return DialogOption(btn_type=DialogButtonType.BUY, msg=msg, can_buy=can_buy, buy=buy)


def patch_map_shops(_map):
    if _map.name == "Monk Quarters":  # new map: Scriptorium
        return [Proxy(exit_x=0, exit_y=2, shop_id=entering_monastery_courtyard().id, ephemeral=True)]
    if _map.name == "Gar'ashi Monastery":
        return [Proxy(exit_x=4, exit_y=10, shop_id=looking_for_hope().id)]  # cut-scene when leaving the Monastery
    if _map.name == "Monastery Trail":
        return [
            Proxy(exit_x=5,  exit_y=13, shop_id=4, dest_x=5, dest_y=12, facing='south'),
            Proxy(exit_x=10, exit_y=15, shop_id=a_safe_haven().id, ephemeral=True),  # entering the village the 1st time
        ]
    if _map.name == "Cedar Village":
        return [
            Proxy(exit_x=6, exit_y=4, shop_id=0, dest_x=6, dest_y=5, facing='north'),
            Proxy(exit_x=6, exit_y=8, shop_id=1, dest_x=6, dest_y=7, facing='south'),
            Proxy(exit_x=8, exit_y=8, shop_id=2, dest_x=9, dest_y=8, facing='west'),
            Proxy(exit_x=1, exit_y=8, shop_id=3, dest_x=2, dest_y=8, facing='west'),
        ]
    if _map.name == "Zuruth Plains":
        return [
            Proxy(exit_x=1, exit_y=9, shop_id=seamus_in_zuruth_plains().id, dest_x=2, dest_y=9, facing='west', ephemeral=True),
        ]
    if _map.name == "Mausoleum":
        return [Proxy(exit_x=15, exit_y=7, shop_id=the_final_leap().id)]  # entering the final level, before the dragon
    if _map.name == "Trade Tunnel":
        return []  # Removing all existing shops
    if _map.name == "Dead Walkways":
        return [Proxy(exit_x=9, exit_y=3, shop_id=seamus_transformation().id, dest_x=9, dest_y=2, facing='south', ephemeral=True)]
    return _map.shops
