
def minimap_is_unknown(map_id, x, y):
    if map_id == 10:  # In Trade Tunnel (aka Lost Temple), hide the maze
        return (9 <= x <= 14) and (1 <= y <= 10)
    if map_id == 7:  # In Canal Boneyard, hide island-hints
        return (x, y) in ((2, 2), (2, 9))
    return False
