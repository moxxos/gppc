#!/usr/bin/env python3
"""
Implements the core functionality of gppc.

Copyright (C) 2022 moxxos
"""

# Package Modules
from gppc.__version__ import __version__
from gppc.__description__ import short_description
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

"""
class ItemPageParser(HTMLParser):
    def __init__(self, *, convert_charrefs: bool = ...) -> None:
        super().__init__(convert_charrefs=convert_charrefs)
"""


class SearchPageParser(HTMLParser):
    """
    Returns an HTML parser that digests a search page and stores an array of
    6-tuples depending on number of items found:
    item_data = [(item_name, item_id, item_price, item_change), (item_url), (item_pic)]
    """

    def __init__(self, item: str, page='1') -> None:
        super().__init__()
        self.item = item
        self.page = page
        self.item_data = []
        self.data = self.item_name = self.item_id = self.item_price = self.item_change = self.item_pic = self.item_link = ''
        self.in_results_table = self.in_item_row = self.in_page_list = False
        self.td_counter = 0

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
            if (self.in_item_row
                and not self.item_id
                and 'href' and 'title' in
                (attr_keys :=
                    list(map(lambda attr_tuple: attr_tuple[0], attrs)))):
                href_pos = attr_keys.index('href')
                self.item_name = attrs[attr_keys.index('title')][1]
                # Get item_id
                self.item_link = attrs[href_pos][1]
                item_path_pos = self.item_link.find(_ITEM_PATH)
                self.item_id = self.item_link[(
                    item_path_pos + _ITEM_PATH_LEN + 1):]

        if (tag == 'table' and ('class', 'results-table') in attrs):
            self.in_results_table = True

        if (self.in_results_table and tag == 'tr'):
            self.in_item_row = True
            self.td_counter = 0
            self.item_id = ''

        if (tag == 'div'
                and ('class', 'paging') in attrs):
            self.in_page_list = True

    def handle_endtag(self, tag: str) -> None:

        if (tag == 'td'):
            if (self.td_counter == 0):
                # TODO extract and display the image sprite
                None
            if (self.td_counter == 1):
                # TODO extract and display members data
                None
            elif (self.td_counter == 2):
                self.item_price = self.data
            elif (self.td_counter == 3):
                # self.data is item_change on last td tag
                self.item_data.append((self.item_name, self.item_id,
                                       self.item_price, self.data,
                                       self.item_link, self.item_pic))
            self.td_counter += 1

        if (tag == 'table' and self.in_results_table):
            self.in_results_table = False

        # If another page exists recursively get the next page.
        if (tag == 'a' and self.in_page_list):
            # Sometimes an ellipsis appears as the next page.
            # This cannot be converted to an integer.
            try:
                if (int(self.data) == int(self.page) + 1):
                    NextPageParser = SearchPageParser(self.item, self.data)
                    next_page = _request_search_page(self.item, self.data)
                    NextPageParser.feed(next_page.text)
                    self.item_data = [*self.item_data,
                                      *NextPageParser.get_search_data()]
            except ValueError:
                # This is an ellipsis.
                None
        if (self.in_page_list and tag == 'div'):
            self.in_page_list = False

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if (tag == 'img'
            and 'src' and 'title' in
            (attr_keys :=
                list(map(lambda attr_tuple: attr_tuple[0], attrs)))
                and attrs[attr_keys.index('title')][1] == self.item_name):
            self.item_pic = attrs[attr_keys.index('src')][1]

    def handle_data(self, data: str) -> None:
        self.data = data

    def get_search_data(self) -> list[tuple[str, str, str, str, str, str]]:
        return self.item_data


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
    search_parser = SearchPageParser(item)
    search_parser.feed(search_page.text)
    return search_parser.get_search_data()


def _command_line_parser(item_argument: str) -> argparse.ArgumentParser:
    """Creates the command line parser."""
    parser = argparse.ArgumentParser(
        description=short_description)
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
