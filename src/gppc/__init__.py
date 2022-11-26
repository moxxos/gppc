"""
GPPC (Gold Piece Price Checker)
-------------------------------
Check OSRS Grand Exchange prices from the command line.
Includes limited module functionality.

Copyright (C) 2022 moxxos
"""

from gppc.__version__ import __version__
from gppc.__description__ import (
    __author__,
    __title__,
    __copyright__)
from gppc._gppc import _main, search
from gppc._item import Item
