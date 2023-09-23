"""
GPPC (Gold Piece Price Checker)
-------------------------------
Check OSRS Grand Exchange prices from the command line.
Includes module functionality to check full item price history.

Copyright (C) 2022 moxxos
"""

from gppc.__version__ import __version__
from gppc.__description__ import (
    __author__,
    __title__,
    __copyright__)
from gppc._gppc import _main, _search_print as search
from gppc._item import Item, Catalog
