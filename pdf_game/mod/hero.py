from . import Proxy
from ..entities import CombatLog, ParryItem


_PATCHED_AVATAR = {  # Starting stats that differ from Heroine Dusk:
    'mp': 1,
    'max_mp': 1,
}


def scepter_parry_logic(gs, _round):
    avatar_log = CombatLog(action='Parry', result='Magic absorbed!')
    return gs._replace(combat=gs.combat._replace(avatar_log=avatar_log), mp=min(gs.mp + 2, gs.max_mp))


PARRY_ITEMS = {
    'BUCKLER': ParryItem(max_parries=2),
    'SCEPTER': ParryItem(max_parries=2, logic=scepter_parry_logic),
}


def patch_avatar(avatar):
    class Avatar:
        def __getattr__(self, attr):
            return _PATCHED_AVATAR[attr] if attr in _PATCHED_AVATAR else getattr(avatar, attr)
    return Avatar()


def patch_info(info):
    return Proxy(avatar_img=info.avatar_img,
                 button_img=info.button_img,
                 armors=_patch_armors(info.armors),
                 spells=info.spells,
                 weapons=info.weapons)

def _patch_armors(_):
    return [
        None,  # armor 0 is never used, heroine is in underwear on spritesheet
        Proxy(**{'name': 'No Armor', 'def': 0}),
        None,  # armor 2 is never used
        None,  # armor 3 is never used
        None,  # armor 4 is never used
        None,  # armor 5 is never used
        None,  # armor 6 is never used
        Proxy(**{'name': 'St Knight Armor', 'def': 12}),
    ]
