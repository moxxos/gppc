#!/usr/bin/env python3
"""
Implements the core functionality of gppc.

Copyright (C) 2022 moxxos
"""

# Package Modules
from gppc.__version__ import __version__
from gppc.__description__ import __short_description__
from gppc._display import _print_item_data

# External Packages
import requests

# Standard Library
import argparse
from html.parser import HTMLParser

# Constants
_MAIN_URL = 'https://secure.runescape.com/m=itemdb_oldschool'
_ITEM_PATH = '/viewitem?obj'
_SEARCH_PATH = '/results#main-search'
_GET_PARAMETER = 'obj'
_POST_PARAMETER = 'query'
_HEADER_PARAMETER_USER_AGENT = 'user-agent'
_USER_AGENT = 'Mozilla/5.0'


# Calculated constants
_MAIN_URL_LEN = len(_MAIN_URL)
_ITEM_PATH_LEN = len(_ITEM_PATH)


class _SearchPageParser(HTMLParser):
    """
    Returns an HTML parser that digests a search page and stores an array of
    6-tuples depending on number of items found:
    item_data = [(item_name, item_id, item_price, item_change), (item_url), (item_pic)]
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

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
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
        # We only need to consume one start <a> tag
        if (tag == 'a'):
            if (self.__item_row
                and not self.__item_id
                and 'href' and 'title' in
                (attr_keys :=
                    list(map(lambda attr_tuple: attr_tuple[0], attrs)))):
                href_pos = attr_keys.index('href')
                self.__item_name = attrs[attr_keys.index('title')][1]
                # Get item_id
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

        if (tag == 'td'):
            if (self.__td_counter == 0):
                # TODO extract and display the image sprite
                None
            if (self.__td_counter == 1):
                # TODO extract and display members data
                None
            elif (self.__td_counter == 2):
                self.__item_price = self.__data
            elif (self.__td_counter == 3):
                # self.__data is item_change on last td tag
                self.__item_data.append((self.__item_name, self.__item_id,
                                         self.__item_price, self.__data,
                                         self.__item_link, self.__item_pic))
            self.__td_counter += 1

        if (tag == 'table' and self.__in_results_table):
            self.__in_results_table = False

        # If another page exists recursively get the next page.
        if (tag == 'a' and self.__in_page_list):
            # Sometimes an ellipsis appears as the next page.
            # This cannot be converted to an integer.
            try:
                if (int(self.__data) == int(self.__page) + 1):
                    NextPageParser = _SearchPageParser(self.__item,
                                                       self.__data)
                    next_page = _request_search_page(self.__item, self.__data)
                    NextPageParser.feed(next_page.text)
                    self.__item_data = [*self.__item_data,
                                        *NextPageParser.get_search_data()]
            except ValueError:
                # This is an ellipsis.
                None
        if (self.__in_page_list and tag == 'div'):
            self.__in_page_list = False

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if (tag == 'img'
            and 'src' and 'title' in
            (attr_keys :=
                list(map(lambda attr_tuple: attr_tuple[0], attrs)))
                and attrs[attr_keys.index('title')][1] == self.__item_name):
            self.__item_pic = attrs[attr_keys.index('src')][1]

    def handle_data(self, data: str) -> None:
        self.__data = data

    def get_search_data(self) -> list[tuple[str, str, str, str, str, str]]:
        return self.__item_data


def _request_search_page(item: str, page='') -> requests.Response:
    """
    Queries the main OSRS Grand Exchange URL with item.
    Returns a request.Reponse object.

    :param item: 
    """
    headers = {
        _HEADER_PARAMETER_USER_AGENT: _USER_AGENT
    }
    params = {
        _POST_PARAMETER: item,
        'page': page
    }
    return requests.get(
        _MAIN_URL + _SEARCH_PATH,
        headers=headers,
        params=params)


def _search_item_data(item: str) -> list[tuple[str, str, str, str, str, str]]:
    """
    Search for an item. 
    Returns list of items found in a 6-tuple:
    (item_name, item_id, item_price, item_change, item_url, item_link)

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
    return parser


def _main() -> None:
    """Main command line function."""
    item_argument = 'item(s)'
    parser = _command_line_parser(item_argument)
    args = vars(parser.parse_args())

    total_item_data = []
    for item in args[item_argument]:
        item = item.replace('_', ' ')
        for item_data in _search_item_data(item):
            total_item_data.append(item_data)
    _print_item_data(total_item_data)


if (__name__ == "__main__"):
    _main()


def search(item) -> None:
    _print_item_data(_search_item_data(item))
