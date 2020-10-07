'''
This package role is to tweak the original game
(enemy stats, map tiles, randomness...)
in order to make it fun to play as a PDF port.
'''

class Proxy(dict):
    __getattr__ = dict.__getitem__
