"""
GPPC (Gold Piece Price Checker)
-------------------------------
Check OSRS Grand Exchange prices from the command line.
Includes limited module functionality.
"""

from gppc._version_ import __version__
from gppc.gppc import _main, _search_item_data


def search(item: str) -> list[tuple[str, str, str, str]]:
    return _search_item_data(item)


def main():
    _main()
