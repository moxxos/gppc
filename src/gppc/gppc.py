#!/usr/bin/env python3
"""Implements the core functionality of gppc."""

# Package Modules
from gppc._description_ import short_description
from gppc import _display

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


def _search_page_parser(item: str, item_page='1'):
    """
    Returns an HTML parser that digests a search page and stores an array of
    4-tuples depending on number of items found:
    item_data = [(item_name, item_id, item_price, item_change), ...]
    """
    class SearchPageParser(HTMLParser):

        # Array of item results from single search page
        item_data = []
        data = item_name = item_id = item_price = item_change = item_pic = item_link = ''
        in_results_table = in_item_row = in_page_list = False
        td_counter = 0

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
                    if (int(self.data) == int(item_page) + 1):
                        NextPageParser = _search_page_parser(item, self.data)
                        next_page = _request_search_page(item, self.data)
                        NextPageParser.feed(next_page.text)
                        self.item_data += NextPageParser.get_search_data()
                except ValueError:
                    "This is an ellipsis."

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

    return SearchPageParser()


def _request_search_page(item: str, page='') -> requests.Response:
    """
    Queries the main OSRS Grand Exchange URL with item.
    Returns a request.Reponse object.
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
    Search an for an item
    Returns list of items found in a 4-tuple:
    (item_name, item_id, item_price, item_change)
    """
    search_page = _request_search_page(item)
    search_parser = _search_page_parser(item)
    search_parser.feed(search_page.text)
    return search_parser.get_search_data()


def _command_line_parser(item_argument: str) -> argparse.ArgumentParser:
    """Creates the command line parser."""
    parser = argparse.ArgumentParser(description=short_description)
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
        total_item_data += _search_item_data(item)
    _display._print_item_data(total_item_data)


if (__name__ == "__main__"):
    _main()
