'''
A "dead-end" state is a GameState that cannot lead to either a GAMEOVER or a VICTORY.
'''
import os
from queue import LifoQueue

from .optional_deps import tqdm


def detect_deadends(game_views):
    print('Starting dead-end detecter')
    print('- listing all end-game leaf states')
    endgame_gvs = set(gv for gv in game_views if gv.state and gv.state.milestone >= 2)
    print('#end-game GVs:', len(endgame_gvs))
    print('- marking all states leading to an end-game leaf')
    non_deadend_gs_hashes = set()
    for gv in tqdm(endgame_gvs, disable='NO_TQDM' in os.environ):
        while gv:
            if gv.state:
                gs_hash = hash(gv.state)
                if gs_hash in non_deadend_gs_hashes:
                    break
                non_deadend_gs_hashes.add(gs_hash)
            gv = gv.src_view
    print('Initial #non-deadend GVs:', len(non_deadend_gs_hashes))
    print('- deducing all dead-end states')
    loops = []
    for gv in tqdm(game_views):
        if not gv.state or gv.state.map_id < 0 or hash(gv.state) in non_deadend_gs_hashes:
            continue
        children = {gv.state}  # GameStates reachable by following actions from "gv"
        queue = LifoQueue() # GameViews to be processed, a subset of all children of "gv"
        queue.put(gv)
        abort = False
        dest_loops = []
        while not (abort or queue.empty()):
            qgv = queue.get()
            for next_gv in qgv.actions.values():
                if not next_gv:
                    continue
                if hash(next_gv.state) in non_deadend_gs_hashes:
                    non_deadend_gs_hashes |= set(hash(gs) for gs in children)
                    abort = True
                    break
                for loop in loops:
                    if next_gv.state in loop:
                        if loop not in dest_loops:
                            dest_loops.append(loop)
                        break
                else:
                    if next_gv.state not in children:
                        queue.put(next_gv)
                        children.add(next_gv.state)
        if not abort:
            # Note: the regrouping logic is flawed I think, but I get the information I needed so YAGNI
            if dest_loops:
                if len(dest_loops) == 1:
                    # print(f'  * growing existing loop by {len(children)} elements')
                    dest_loops[0] |= children
                else:
                    # print(f'  * merging {len(dest_loops)} existing loops into one')
                    loops = [loop for loop in loops if loop not in dest_loops]
                    for dest_loop in dest_loops:
                        children |= dest_loop
                    loops.append(children)
            else:
                # print(f'  * new loop of size: {len(children)}')
                loops.append(children)
    print('#dead-ends:', sum(len(loop) for loop in loops))
    print('#dead-ends loops:', len(loops))
    map_ids = set()
    for loop in loops:
        for gs in loop:
            map_ids.add(gs.map_id)
    if map_ids:
        print('Maps with dead-ends:', map_ids)
    for loop in sorted(loops, key=len):
        print(f'\nDead-ends loop of size {len(loop)} includes:')
        print(list(loop)[0])
