# pylint: disable=unused-import
try:
    from humanfriendly.terminal import ansi_wrap
except ImportError:
    ansi_wrap = lambda msg, color=None, bold=None: msg

try:
    from tqdm import tqdm
except ImportError:
    tqdm = lambda _, **__: _
