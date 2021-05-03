from ..bitfont import bitfont_color_red, bitfont_render
from ..entities import Book, Position, SFX
from ..logs import log

from .scenes import tuto_spells, BASE_MUSIC_URL
from .world import MAUSOLEUM_PORTAL_COORDS, VILLAGE_PORTAL_COORDS


BOOKS = {
    (0, 1, 3): Book(' '),  # for testing purpose only

    # Monastery Library:
    (3, 1, 1): Book('The Storm Dragon is a brutal\ncreature. It ravaged the\nrealm for several years.', img='assets/storm-dragon-small.png'),  # top row, left bookshelf
    (3, 2, 1): Book('\n\nAncient tales mention\npacts with dark forces,\nin order to control time\nand bring dead people\nback to life.', img='assets/blood-signed-pact.png'),  # top row, middle bookshelf
    (3, 0, 2): Book('Barely made a templar,\nthe man who would become\nthe knight of the realm\ndecided to face\nthe storm dragon...\n', img='assets/coat-of-arms.png'),  # left row, top bookshelf
    (3, 0, 3): Book('Old scriptures mention\nvery old pagan gods.\n\nThey lived underwater,\ndeep down below the ground,\nand protected ancient tribes\nin exchange for offerings.'),  # left row, bottom bookshelf
    (3, 4, 2): False,  # right row, top bookshelf
    (3, 4, 3): Book('...demons hide in hesitations,\nin fractions of seconds\nwhere our moral compass\nis adjusting,', img='assets/demons-of-time.png', next=Book('...and there is still\na potentiality that we\ncommit something horrible.\nIf time froze\nin those instants,\nour flesh would open up\nto terrible monsters...')),  # right row, bottom bookshelf

    # Templar Academy: first 2 bookshelves
    (10, 0, 1): Book('The guarding lady,\nis a famous mythical figure.\nTemplar apprentices took\ntheir vow by kneeing\nbefore her statue and\nplacing their trainee\namulet in her hand.'),
    (10, 0, 3): Book('During all their\nformation, young templars\nwear a sapphire amulet,\nsymbolizing the moral purity\nthey are trying to acquire.\n\n', treasure_id=12),
    # Templar Academy: next 4 bookshelves
    (10, 0, 5): Book('The Saint Knight was\nmurdered in his sleep\nby a cabal of druids\njealous of his influence.\n',
                    img='assets/tomb-stone.png', next=Book('Following a grand funeral,\nhis body and armor were\nburied in the Mausoleum,\nwhile his sword was hidden\nin the Templar Academy maze.')),
    (10, 0, 7): Book('The Empress is said to have\nan interest in the occult,\nand to sometimes perform\narcane dark magic rituals.\n', img='assets/small-pentacle.png'),
    (10, 0, 9): Book('Drawings were made,\non empty pages corners',
                    next=Book(' ', bird_index=0,
                        next=Book(' ', bird_index=1,
                            next=Book(' ', bird_index=2,
                                next=Book(' ', bird_index=3,
                                    next=Book(' ', bird_index=4)))))),
    (10, 0, 11): Book('A trap mechanism is detailed,\ninvolving a giant boulder.\nIt appears to protect\na secret part of the library\nand the Templars treasure.\n\n', treasure_id=9),
    # Templar Academy: final 4 bookshelves
    (10, 0, 13): Book('Mimics are\nmagical creatures\nthat take the shape\nof mundane objects,\nlike chests.\n', img='assets/mimics.png', next=Book('They are as strong\nas the furniture item\nthey imitate,\nbut they also\nshare the same\nvulnerabilities.')),
    (10, 0, 14): Book('\n' * 4 + 'Seamus Mc Lornan is\na powerful wizard,\nand a reknown advisor\nof the late Emperor.', portrait=0),
    (10, 1, 15): Book('An encyclopedia mentions\na sorcerer thief that\nmastered a spell to unlock\nall doors & chests...', img='assets/open-chest-and-treasure.png'),
    (10, 2, 15): Book('The secret of the Saint\nKnight victory over the\nStorm Dragon was\nhis armor : it was made\nof electric-proof steel.\n\n', sfx=SFX(id=5, pos=Position(64, 88))),

    # Mausoleum: 2 bookshelves next to portal
    (8, 3, 13): Book('A treatise on\nDruidic linguistics.\nThe first chapter teaches\nthe names of numbers.',
                     next=Book('1 : Klaatu  2 : Da\n3 : Fer  4 : Me\n5 : Mi  6 : Sesa\n7 : To  8 : Bara\n9 : Nik  10 : Do')),
    # Mausoleum: 2 bookshelves in east corridor
    (8, 14, 4): Book('An old parchment mentions\nhow the Mausoleum stairs\nleading to the castle above\nwere condamned long ago.', next=Book('A secret mechanism still\nallows to open the iron gate:\nthe key is a sequence of\nthree directions, hidden\nin the lyrics of a folk song.')),
    (8, 14, 10): Book('Of gods & men\nChapt. 4\nGorgons', img='assets/gorgon-head.png', next=Book('Never look a gorgon\nin the eye! Their gaze can\nturn people into stone.\n\nNote: watching their own\nreflection is fatal for them.')),
    # Mausoleum: bookshelf in north-west alcove, behind 2 mimics:
    (8, 2, 2): Book('The ballad of the first king\n\nIn the plains\nthe journey started.\nSouth he went\nto the monks temple.', music=BASE_MUSIC_URL + 'AlexandrZhelanov-JourneyToTheEastRocks.ogg', next=Book('All the books he read,\nas wisdom was his goal.\nThen north he traveled,\nto the knights college.\nTo become the bravest,\nwas is new ambition.\n', next=Book("Finally, to the west\nhe crossed a river,\nand there established\nthe realm's foundations.\n\n", treasure_id=28))),
}


def examine_bookshelf(gs, bookshelf_pos, actions, _GameView):
    key = (gs.map_id, *bookshelf_pos)
    if key == (8, 3, 11):
        # Mausoleum bookshelf that hides hint on how to activate portal:
        if 'SCROLL' not in gs.items and gs.spellbook < 3:
            actions['EXAMINE'] = _GameView(gs._replace(message='You found\nan ancient scroll\n\n',
                                                       treasure_id=23, items=gs.items + ('SCROLL',)))
        else:
            ritual_words, fixed_id = 'Mido Sesame', 51064
            if 'ABYSS_BOTTOM' in gs.secrets_found:
                ritual_words, fixed_id = 'Klaatu Barada Nikto', 18297
            actions['EXAMINE'] = _GameView(gs._replace(book=Book(f'Ancient portals\nused to be controlled\nwith a magic incantation:\n"{ritual_words}"'), extra_render=ctrl_g_hint_extra_render))
            if gs.spellbook < 3:  # creating a hidden GameView with the portal open and a fixed page ID:
                new_gv = _GameView(gs._replace(message=f'You utter out loud\nthe ritual words:\n\n"{ritual_words}"',
                                               fixed_id=fixed_id, facing='west'))
                actions[None] = new_gv
                if not new_gv.tile_override(MAUSOLEUM_PORTAL_COORDS):# avoid adding overrides if GameView already exists
                    log(new_gv.state, f'activating-portal: secrets_found={new_gv.state.secrets_found}')
                    new_gv.add_tile_override(27, coords=MAUSOLEUM_PORTAL_COORDS)
                    new_gv.add_tile_override(27, coords=VILLAGE_PORTAL_COORDS)
        return
    book = BOOKS.get(key)
    if book:
        actions['EXAMINE'] = _GameView(gs._replace(book=book))
    elif key == (3, 3, 1):  # Library top row, right bookshelf
        if gs.spellbook == 0:
            actions['EXAMINE'] = _GameView(gs._replace(book=Book('You find a spellbook\nand learn a healing spell'),
                                                       treasure_id=11, spellbook=1, shop_id=tuto_spells().id))
    elif book is None:
        raise NotImplementedError(f'No book associated yet with bookshelf @{bookshelf_pos} from coords {gs.coords}')


def ctrl_g_hint_extra_render(pdf):
    with bitfont_color_red():
        bitfont_render(pdf, 'c', 77, 62)
        bitfont_render(pdf, 'tr', 97, 62)
        bitfont_render(pdf, 'l', 121, 62)
        bitfont_render(pdf, 'g', 62, 72)
