from enum import IntEnum
from typing import Callable, NamedTuple, Optional, Tuple, Union


class Position(NamedTuple):
    x: int
    y: int
    angle: int = 0


class MessagePlacement(IntEnum):
    DOWN = 0
    UP = 1


# Replicates bitfont().JUSTIFY_* constants:
class Justify(IntEnum):
    LEFT = 0
    RIGHT = 1
    CENTER = 2


class GameMode(IntEnum):
    # Replicate gamestate.js
    EXPLORE = 0
    COMBAT = 1
    INFO = 2
    DIALOG = 3


class GameMilestone(IntEnum):
    NONE = 0
    CHECKPOINT = 1
    GAME_OVER = 2
    VICTORY = 3


class TileEdge(NamedTuple):
    'A non-oriented, unique representation of an edge between 2 adjacent tiles'
    pos1: Tuple[int]  # (x, y)
    pos2: Tuple[int]  # (x, y)
    facing: str
    @classmethod
    def new(cls, pos, facing):
        # pylint: disable=import-outside-toplevel
        from .mazemap import mazemap_mirror_facing, mazemap_next_pos_facing
        next_pos = mazemap_next_pos_facing(*pos, facing)
        if pos > next_pos:
            pos, next_pos = next_pos, pos
            facing = mazemap_mirror_facing(facing)
        assert facing in ('east', 'south')
        return cls(pos, next_pos, facing)
    @classmethod
    def from_positions(cls, pos1, pos2):
        if pos1 > pos2:
            pos1, pos2 = pos2, pos1
        # pylint: disable=import-outside-toplevel
        from .mazemap import mazemap_facing_from_positions
        facing = mazemap_facing_from_positions(pos1, pos2)
        assert facing in ('east', 'south')
        return cls(pos1, pos2, facing)


class WarpPortal(NamedTuple):
    edge1: TileEdge
    edge2: TileEdge
    @classmethod
    def new(cls, edge1, edge2):
        if edge1 > edge2:
            edge1, edge2 = edge2, edge1
        return cls(edge1, edge2)
    def has_edge(self, edge):
        return edge in (self.edge1, self.edge2)
    def translate(self, edge, x, y):
        assert self.has_edge(edge)
        src_edge, dst_edge = (self.edge1, self.edge2) if edge == self.edge1 else (self.edge2, self.edge1)
        dx = dst_edge.pos1[0] - src_edge.pos1[0]
        dy = dst_edge.pos1[1] - src_edge.pos1[1]
        return x + dx, y + dy


class SFX(NamedTuple):  # Special Effects !
    id : int
    pos : Position


class CombatRound(NamedTuple):
    attack_name : str = ''
    atk : int = 0  # value already includes Critical bonus
    miss : bool = False
    dodge : bool = False
    hero_crit : bool = False
    hp_drain : bool = False
    mp_drain : bool = False
    heal : int = 0
    run_away : bool = False
    ask_for_mercy : tuple = ()  # (offer_msg, func[GameState->GameState])
    boneshield_up : bool = False
    treasure_id : int = 0
    sfx : SFX = None


class RewardItem(NamedTuple):
    name : str
    treasure_id : int


class RewardTreasure(NamedTuple):
    message : str
    treasure_id : int
    grant : Callable[['GameState'], 'GameState']  # GameState -> GameState


class Bribe(NamedTuple):
    result_msg: str
    item: str = ''
    gold: int = 0
    successful: bool = True
    handshake : Optional[Callable[['GameState'], 'GameState']] = None


class CustomCombatAction(NamedTuple):
    """
    Usually an action with a custom action button position,
    associated with a custom attack/withstand logic for the enemy.
    """
    name: str  # must start with a known action: ATTACK_, HEAL_, etc.
    btn_pos: Optional[Position] = None  # lookup ACTION_BUTTON_POS if not set
    renderer : Optional[Callable[['FPDF', int], None]] = None  # renderer function, receives (pdf, page_id)
    @property
    def btn_type(self):
        return self.name.split('_', 1)[0]


class Enemy(NamedTuple):
    name : str
    category : int
    hp : int
    max_hp : int
    rounds : Tuple[CombatRound] = ()  # if empty, attack_logic must be defined
    type : Optional[int] = None
    show_on_map : bool = True
    intro_msg : str = ''
    bribes : Tuple[Bribe] = ()
    allows_running_away : bool = False
    max_rounds : int = 4
    gold : int = 0
    reward : Union[RewardItem, RewardTreasure, None] = None
    hidden_trigger : Optional[str] = None
    invincible : bool = False  # useful while level designing
    music : str = ''
    loop_frames : bool = False
    custom_actions : Tuple[CustomCombatAction] = ()
    withstand_logic : Optional[Callable[['GameState', int], tuple]] = None  # (GameState, attack_damage) -> (GameState, log_result)
    attack_logic : Optional[Callable[['CombatState'], CombatRound]] = None  # CombatState -> CombatRound
    enemy_frame : Optional[Callable[['GameState'], int]] = None
    post_defeat_condition : Optional[Callable[['GameState'], bool]] = None  # GameState -> bool
    post_defeat : Optional[Callable[['FPDF'], None]] = None  # renderer function, will receive a .game_view attribute
    victory_msg : str = ''
    post_victory : Optional[Callable[['GameState'], Optional['GameState']]] = None  # GameState -> GameState
    @property
    def custom_actions_names(self):
        return tuple(cca.name for cca in self.custom_actions)
    def custom_action_for(self, action_name):
        return next((cca for cca in self.custom_actions if cca.name == action_name), None)


class CombatLog(NamedTuple):
    action : str
    result : str


class CombatState(NamedTuple):
    enemy: Enemy
    combat_round: CombatRound = None
    round: int = -1
    parries: int = 0  # ignores times when Enemy did not attack
    avatar_log: Optional[CombatLog] = None
    enemy_log: Optional[CombatLog] = None
    boneshield_up: bool = False
    action_name: Optional[str] = None  # if round > 0, name of the action clicked by the player on the previous round
    def incr_round(self):
        # pylint: disable=no-member,protected-access
        combat_state = self._replace(round=self.round + 1)
        return combat_state._replace(combat_round=combat_state._combat_round())
    def _combat_round(self):
        assert self.round >= 0
        if self.enemy.rounds:
            assert not self.enemy.attack_logic, f'Enemy must either have a non-empty .rounds attribute, or an .attack_logic: {self.enemy}'
            return self.enemy.rounds[self.round % len(self.enemy.rounds)]
        assert self.enemy.attack_logic, f'Enemy must either have a non-empty .rounds attribute, or an .attack_logic: {self.enemy}'
        return self.enemy.attack_logic(self)


class ParryItem(NamedTuple):
    max_parries: int   # after more hits withstanded, destroyed
    logic: Optional[Callable[['GameState', CombatRound], Optional['GameState']]] = None


class RollingBoulder(NamedTuple):
    coords: Tuple[int]  # (map_id, x, y)
    dir: int
    shadowed_tile_override: Optional[int] = None


class Trick(NamedTuple):
    message: str
    link: bool = True
    filler_pages: int = 0
    background: str = ''
    music: str = ''
    filler_renderer: Optional[Callable[['FPDF', int], None]] = None


class Book(NamedTuple):
    text: str
    img: str = ''
    treasure_id: int = 0
    bird_index: Optional[int] = None
    next: Optional['Book'] = None  # using a Forward Reference type hint
    portrait : Optional[int] = None
    music : Optional[str] = None
    hidden_trigger : Optional[str] = None
    sfx : Optional[SFX] = None
    extra_render: Optional[Callable[['FPDF'], None]] = None


class GameState(NamedTuple):
    'Minimal, immutable set of properties that define a unique instant in the game'
    # Avatar info:
    map_id: int = -1
    x: int = -1
    y: int = -1
    facing: str = ''
    hp: int = 1
    max_hp: int = 1
    mp: int = 0
    max_mp: int = 0
    weapon: int = 0
    armor: int = 0
    spellbook: int = 0
    gold: int = 0
    bonus_atk: int = 0
    bonus_def: int = 0
    items: Tuple[str] = ()
    hidden_triggers: Tuple[str] = ()
    puzzle_step: Optional[int] = None
    rolling_boulders: Tuple[RollingBoulder] = ()
    triggers_activated: Tuple[Tuple[int]] = ()  # sequence of coords
    # Tile-transient state:
    mode: GameMode = GameMode.EXPLORE
    combat: Optional[CombatState] = None
    vanquished_enemies: Tuple[Tuple[int]] = ()  # sequence of coords - includes enemy bribed & that ran away
    shop_id: int = -1  # meaningful only if >= 0
    message: str = ''
    msg_place: MessagePlacement = MessagePlacement.DOWN
    book: Optional[Book] = None
    treasure_id: int = 0
    sfx : SFX = None
    music: str = ''
    music_btn_pos: Optional[Position] = None
    extra_render: Optional[Callable[['FPDF'], None]] = None
    trick: Optional[Trick] = None
    fixed_id: int = 0  # sets a fixed page ID for this GameView
    reverse_id: bool = False  # indicates this GameView ID must be the symmetrical of its src_view
    milestone: GameMilestone = GameMilestone.NONE
    last_checkpoint: int = 0
    tile_overrides: Tuple[tuple] = ()  # pairs: ((map_id, x, y), tile_id)
    secrets_found: Tuple[str] = ()
    # pylint: disable=no-member
    def clean_copy(self):
        return self._replace(message='', msg_place=MessagePlacement.DOWN,
                             milestone=GameMilestone.NONE,
                             book=None, treasure_id=0, extra_render=None, sfx=None,
                             music='', music_btn_pos=None,
                             trick=None, puzzle_step=None,
                             reverse_id=False, fixed_id=0,
                             combat=self.combat and self.combat._replace(
                                avatar_log=None, enemy_log=None, action_name=None))
    def tile_override_at(self, coords):
        return next((tile_id for (pos, tile_id) in self.tile_overrides if pos == coords), None)
    def with_hidden_trigger(self, hidden_trigger):
        assert hidden_trigger not in self.hidden_triggers
        return self._replace(hidden_triggers=tuple(sorted(self.hidden_triggers + (hidden_trigger,))))
    def without_hidden_trigger(self, hidden_trigger):
        return self._replace(hidden_triggers=tuple(ht for ht in self.hidden_triggers if ht != hidden_trigger))
    def with_secret(self, secret):
        assert secret not in self.secrets_found
        return self._replace(secrets_found=tuple(sorted(self.secrets_found + (secret,))))
    def with_tile_override(self, tile_id, coords, exist_ok=False):
        existing_override = self.tile_override_at(coords)
        if existing_override and exist_ok:
            return self if existing_override == tile_id else self.without_tile_override(coords).with_tile_override(tile_id, coords)
        assert not existing_override, f'Existing tile override @{coords}: {existing_override}'
        return self._replace(tile_overrides=tuple(sorted(self.tile_overrides + ((coords, tile_id),))))
    def without_tile_override(self, coords):
        assert self.tile_override_at(coords) is not None
        return self._replace(tile_overrides=tuple((pos, tile_id) for (pos, tile_id) in self.tile_overrides if pos != coords))
    def with_trigger_activated(self, trigger_coords):
        if trigger_coords in self.triggers_activated:
            return self
        return self._replace(triggers_activated=tuple(sorted(self.triggers_activated + (trigger_coords,))))
    def with_vanquished_enemy(self, enemy_coords):
        assert enemy_coords not in self.vanquished_enemies
        return self._replace(vanquished_enemies=tuple(sorted(self.vanquished_enemies + (enemy_coords,))))
    def with_combat_action(self, action_name):
        return self._replace(combat=self.combat._replace(action_name=action_name))
    @property
    def coords(self):
        'Hero avatar coordinates'
        return self.map_id, self.x, self.y
    def differing(self, other):
        out = ''
        for field in self._fields:
            self_val, other_val = getattr(self, field), getattr(other, field)
            if self_val != other_val:
                out += f'{field}: '
                if not self_val or not other_val or not isinstance(self_val, tuple) or not isinstance(other_val, tuple):
                    out += f'{self_val} != {other_val}\n'
                else:
                    self_val_set, other_val_set = set(self_val or ()), set(other_val or ())
                    left_diff, right_diff = self_val_set - other_val_set, other_val_set - self_val_set
                    left_diff = ('+' + ','.join(map(str, left_diff))) if left_diff else ''
                    right_diff = ('+' + ','.join(map(str, right_diff))) if right_diff else ''
                    out += f'{left_diff} | {right_diff}\n'
        return out


class DialogButtonType(IntEnum):
    NONE = 0
    BUY = 1
    EXIT = 2
    NEXT = 3
    DRINK_RED = 4
    DRINK_GREEN = 5
    TAKE_CRUCIFIX = 6
    TALK_WITH_MONK = 7
    def action_name(self, index):
        if self in (self.BUY, self.NONE):
            return f'{self.name}_{index}'
        # Other types of actions are always unique, no need to include option index:
        return self.name


class DialogOption(NamedTuple):
    btn_type: DialogButtonType
    msg: str
    can_buy: bool
    buy: Optional[Callable[[GameState], GameState]] = None  # GameState -> GameState
    @classmethod
    def only_link(cls, btn_type, next_scene_id):
        return cls(btn_type=btn_type, msg='', can_buy=True, buy=lambda gs: gs._replace(shop_id=next_scene_id))
    @classmethod
    def only_msg(cls, msg):
        return cls(btn_type=DialogButtonType.NONE, msg=msg, can_buy=False, buy=None)
    @classmethod
    def exit(cls, msg, buy):
        return cls(btn_type=DialogButtonType.EXIT, msg=msg, can_buy=True, buy=buy)


class ShopMessageItem(NamedTuple):
    msg: str
    def dialog_option(self, _):
        return DialogOption.only_msg(self.msg)


# Using globals due to typing.NamedTuple, but those two really are class attributes:
CUT_SCENE_PER_ID = {}
LAST_CUT_SCENE_ID = 8  # last used integer among original shop_id constants
class CutScene(NamedTuple):
    '''
    Can be a cut-scene, a shop or just a tutorial page
    TODO: rename into Dialog
    '''
    id: int
    text: str = ''
    justify: Justify = Justify.LEFT
    name: str = ''
    background: Union[int, str] = 0  # integer => original ones, cf. render_utils.BACKGROUNDS for their IDs
    treasure_id: int = 0
    sfx : SFX = None
    exit_msg: str = ''
    music: str = ''
    dialog_options: Tuple[DialogOption] = ()
    no_exit: bool = False
    next_scene_id: Optional[int] = None
    extra_render: Optional[Callable[['FPDF'], None]] = None
    redirect: Optional[Callable[[GameState], Optional['CutScene']]] = None  # may point to another CutScene
    @classmethod
    def new(cls, **kwargs):
        scene_id = kwargs.pop('id', None)
        if not scene_id:
            global LAST_CUT_SCENE_ID
            LAST_CUT_SCENE_ID += 1
            scene_id = LAST_CUT_SCENE_ID
        scene = cls(id=scene_id, **kwargs)
        CUT_SCENE_PER_ID[scene_id] = scene
        return scene
    @classmethod
    def from_id(cls, scene_id):
        return CUT_SCENE_PER_ID[scene_id]


class SingleAffectationDict(dict):
    def __setitem__(self, name, value):
        if name in self:
            raise RuntimeError(f'{name} already set!')
        super().__setitem__(name, value)


class GameView:
    '''
    Game state enriched with page numbers, links to reachable game states & helper methods.
    Mutable so that references to it can be made before page IDs are set.
    There should always be a unique mapping 1 GameView <-> 1 GameState.

    Exceptionnally, a GameView can also be a "filler" or "trick" page.
    Then, it has no GameState associated, only a "renderer" function.
    '''
    def __init__(self, game_state=None, src_view=None, renderer=None):
        assert game_state or renderer
        self._state = game_state
        self.src_view = src_view  # useful for debugging
        self.renderer = renderer
        self.freeze_state = False
        # initialized later:
        self.actions = SingleAffectationDict()  # action_name -> GameView
        self._page_id = None
        self._page_id_from = None
        self.prev_page_trick_game_view = None
        self.next_page_trick_game_view = None
    def __hash__(self):
        return hash(self.state)
    def __repr__(self):
        return f'GameView({self.state}, freeze_state={self.freeze_state}, renderer={bool(self.renderer)}, page_id={self.page_id}, _page_id_from={bool(self._page_id_from)}, actions={self.actions.keys()})'
    @property
    def state(self):
        return self._state
    @state.setter
    def state(self, new_state):
        assert not self.freeze_state, 'Unexpected state edit after GameView has been frozen'
        self._state = new_state
    def page_id_from(self, game_view):
        self._page_id = None
        assert game_view is not None
        self._page_id_from = game_view
    @property
    def page_id(self):
        if self._page_id_from:
            return self._page_id_from.page_id
        return self._page_id
    def set_page_id(self, page_id):
        if page_id is None:
            self._page_id = None
        else:
            if self._page_id_from:
                return False
            self._page_id = page_id
        return True
    def add_tile_override(self, tile_id, coords=None):
        if not coords:
            coords = self.state.coords
        existing_override = self.tile_override(coords)
        assert not existing_override, f'A tile override is already set @ {coords}: {existing_override}'
        self.state = self.state.with_tile_override(tile_id, coords)
    def remove_tile_override(self, coords):
        tile_id = self.tile_override(coords)
        assert tile_id is not None
        self.state = self.state.without_tile_override(coords)
        return tile_id
    def tile_override(self, coords):
        return self.state.tile_override_at(coords)
    @property
    def enemy_vanquished_here(self):
        return self.enemy_vanquished(self.state.coords)
    def enemy_vanquished(self, coords):
        return coords in self.state.vanquished_enemies
    def add_hidden_trigger(self, hidden_trigger):
        self.state = self.state.with_hidden_trigger(hidden_trigger)
    def as_dict(self):  # JSON-export-friendly
        if not self.state: return self.state
        view_dict = self.state._asdict()
        # removing non-serializable fields:
        view_dict['extra_render'] = bool(view_dict['extra_render'])
        trick = self.state.trick
        if trick:
            view_dict['trick'] = trick._replace(filler_renderer=None)
        combat = self.state.combat
        if combat:
            view_dict['combat'] = combat._replace(enemy=combat.enemy._replace(
                    post_defeat_condition=None, post_defeat=None, post_victory=None))
        view_dict['actions'] = {action: next_gv.page_id if next_gv else None
                                for action, next_gv in self.actions.items()}
        return view_dict


class Checkpoint(NamedTuple):
    coords: Tuple[int]
    description: str
    mode: GameMode = GameMode.EXPLORE
    condition: Optional[Callable[[GameState], bool]] = None  # GameState -> bool
    def matches(self, game_state):
        # pylint: disable=not-callable
        if self.condition and not self.condition(game_state):
            return False
        return game_state.coords == self.coords
