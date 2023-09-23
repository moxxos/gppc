#!/usr/bin/env python3
"""
Implements the core functionality of gppc.

Copyright (C) 2022 moxxos
"""

# Standard Library
import argparse
from html.parser import HTMLParser

# External Packages
import requests

# Package Modules
from gppc.__version__ import __version__
from gppc.__description__ import __short_description__
from gppc._display import _print_item_simple, _print_item_full, _get_item_pic
from gppc._db import DbManager
from gppc._constant import (_MAIN_URL,
                            _ITEM_PATH,
                            _SEARCH_PATH,
                            _POST_PARAMETER,
                            _REQUEST_HEADER,
                            _SM_IMG_SIZE,
                            _LG_IMG_SIZE)
from gppc._item import Item

# Calculated constants
_MAIN_URL_LEN = len(_MAIN_URL)
_ITEM_PATH_LEN = len(_ITEM_PATH)


class _SearchPageParser(HTMLParser):
    """
    Returns an HTML parser that digests a search page and stores an array of
    6-tuples depending on number of items found:
    item_data = [(item_name, item_id, item_price,
                 item_change, item_url, item_pic)]
    """

    def __init__(self, item: str, page='1') -> None:
        super().__init__()
        self.__item = item
        self.__page = page
        self.__item_data = []
        self.__data = ''
        self.__item_name = ''
        self.__item_id = ''
        self.__item_price = ''
        self.__item_pic = ''
        self.__item_link = ''
        self.__in_results_table = False
        self.__item_row = False
        self.__in_page_list = False
        self.__td_counter = 0

    def handle_starttag(self, tag: str,
                        attrs: list[tuple[str, str | None]]) -> None:
        """
        attrs example: [('class', 'table-item-link'), ('href', 'https://...')]

        A single item row should look like the following:
        <tr>
            <td><a href=item_link/ title=item_name><img/></td>
            <td class='memberItem'></td> or <td class=''></td> for non-member
            <td>item_price</td>
            <td>item_change</td>
        </tr>
        """
        if tag == 'a':
            if (self.__item_row
                and not self.__item_id
                and 'href' in
                (attr_keys := list(
                    map(lambda attr_tuple: attr_tuple[0], attrs)))
                    and 'title' in attr_keys):
                href_pos = attr_keys.index('href')
                self.__item_name = attrs[attr_keys.index('title')][1]
                self.__item_link = attrs[href_pos][1]
                item_path_pos = self.__item_link.find(_ITEM_PATH)
                self.__item_id = self.__item_link[(
                    item_path_pos + _ITEM_PATH_LEN + 1):]

        if (tag == 'table' and ('class', 'results-table') in attrs):
            self.__in_results_table = True

        if (self.__in_results_table and tag == 'tr'):
            self.__item_row = True
            self.__td_counter = 0
            self.__item_id = ''

        if (tag == 'div'
                and ('class', 'paging') in attrs):
            self.__in_page_list = True

    def handle_endtag(self, tag: str) -> None:

        if tag == 'td':
            if self.__td_counter == 1:
                # TODO extract and display members data
                None
            elif self.__td_counter == 2:
                self.__item_price = self.__data
            elif self.__td_counter == 3:
                # self.__data is item_change on last td tag
                self.__item_data.append((self.__item_name, self.__item_id,
                                        self.__item_price, self.__data,
                                        self.__item_link, self.__item_pic))
            self.__td_counter += 1

        if (tag == 'table' and self.__in_results_table):
            self.__in_results_table = False

        if (tag == 'a' and self.__in_page_list):
            try:
                if int(self.__data) == int(self.__page) + 1:
                    next_page_parser = _SearchPageParser(self.__item,
                                                         self.__data)
                    next_page = _request_search_page(self.__item, self.__data)
                    next_page_parser.feed(next_page.text)
                    self.__item_data = [*self.__item_data,
                                        *next_page_parser.get_search_data()]
            except ValueError:
                return
        if (self.__in_page_list and tag == 'div'):
            self.__in_page_list = False

    def handle_startendtag(self, tag: str,
                           attrs: list[tuple[str, str | None]]) -> None:
        if (tag == 'img' and 'src' and 'title'
            in (attr_keys := list(map(lambda attr_tuple: attr_tuple[0], attrs)))
                and attrs[attr_keys.index('title')][1] == self.__item_name):
            self.__item_pic = attrs[attr_keys.index('src')][1]

    def handle_data(self, data: str) -> None:
        self.__data = data

    def get_search_data(self) -> list[tuple[str, str, str, str, str, str]]:
        """Return search data."""
        return self.__item_data


def _request_search_page(item: str, page='') -> requests.Response:
    """
    Queries the main OSRS Grand Exchange URL with item.
    Returns a request.Reponse object.

    :param item:
    """
    params = {
        _POST_PARAMETER: item,
        'page': page
    }
    return requests.get(
        _MAIN_URL + _SEARCH_PATH,
        headers=_REQUEST_HEADER,
        params=params, timeout=100)


def _search_item_data(item: str) -> list[tuple[str, str, str, str, str, str]]:
    """
    Search for an item.
    Returns list of items found in a 6-tuple:
    (item_name, item_id, item_price, item_change, item_url, item_pic_link)

    :param item: required searchable item
    :type item: str
    :return: the list of found items
    :rtype: list[tuple[str, str, str, str, str, str]]
    """
    search_page = _request_search_page(item)
    search_parser = _SearchPageParser(item)
    search_parser.feed(search_page.text)
    return search_parser.get_search_data()


def _command_line_parser(item_argument: str) -> argparse.ArgumentParser:
    """Creates the command line parser."""
    parser = argparse.ArgumentParser(
        description=__short_description__)
    parser.add_argument(
        '--version', '-v',
        action='version',
        version=__version__,
        help='display current version'
    )
    parser.add_argument(
        item_argument,
        metavar='I',
        type=str,
        nargs='+',
        help='snake case or quoted item(s) (ex: gold_bar or \'gold bar\')'
    )
    parser.add_argument(
        '--full', '-f',
        action='store_true',
        help='display full price and item information'
    )
    return parser


def _main() -> None:
    """Main command line function."""
    item_argument = 'item(s)'
    parser = _command_line_parser(item_argument)
    args = vars(parser.parse_args())
    for item in args[item_argument]:
        item = item.replace('_', ' ')
        _search_print(item, args['full'])


if __name__ == "__main__":
    _main()


def _search_print(item, full=False) -> None:
    """Preform search"""
    DbMan = DbManager()
    for item_data in _search_item_data(item):
        try:
            if DbMan.retrieve_item_info(item_data[1]) is None:
                item_img = _get_item_pic(item_data[5], (_SM_IMG_SIZE if not full else _LG_IMG_SIZE))
                item = Item(item_data[0])
                DbMan.store_item_info(item._Item__info, item_img)
            else:
                item_img = DbMan.retrieve_item_info(int(item_data[1]))[9]

            if full:
                _print_item_full(item_data[0], item_data[2],
                                 item_data[3], item_data[4], item_img)
            else:
                _print_item_simple(item_data[0], item_data[2],
                                   item_data[3], item_data[4], item_img)
        except ValueError:
            print(item_data[0] + ' not found in mapping.')
    DbMan.close_db()
