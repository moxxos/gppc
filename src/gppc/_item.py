"""
Encapsulates all data of a single item.

Copyright (C) 2022 moxxos
"""

from html.parser import HTMLParser
import requests

from gppc._gppc import _search_item_data


_SCRIPT_PRICE = 'average180'
_SCRIPT_TRADE = 'trade180'


class Item():

    class __ItemPageParser(HTMLParser):
        def __init__(self, item) -> None:
            super().__init__()
            self.__item = item
            self.__data = ''
            self.__in_stats_div = False
            self.__in_stats_ul = False
            self.__is_gp_change = False

            self.gp_change_stats = []
            self.pc_change_stats = []
            self.raw_item_history = ''

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            if (tag == 'div' and ('class', 'stats') in attrs):
                self.__in_stats_div = True

            if (tag == 'ul' and self.__in_stats_div):
                self.__in_stats_ul = True

            if tag == 'span':
                if ('class', 'stats__gp-change') in attrs:
                    self.__is_gp_change = True
                elif ('class', 'stats__pc-change') in attrs:
                    self.__is_gp_change = False

        def handle_endtag(self, tag: str) -> None:
            if (tag == 'div' and self.__in_stats_div):
                self.__in_stats_div = self.__in_stats_ul = False

            if (tag == 'span' and self.__in_stats_ul):
                if (self.__is_gp_change):
                    self.gp_change_stats.append(self.__data)
                else:
                    self.pc_change_stats.append(self.__data)

        def handle_data(self, data: str) -> None:
            if (data.find(_SCRIPT_PRICE) != -1):
                self.raw_item_history = data
            self.__data = data

    def __init__(self, item: str):
        if ((item := item.capitalize()) in
            (item_list := list(map(lambda item_tuple: item_tuple[0],
                                   search_results := _search_item_data(item))))):
            item_link = search_results[(
                item_index := item_list.index(item))][4]
            item_page = requests.get(item_link,
                                     headers={'user-agent': 'Mozilla/5.0'})
            self.__item = item
            self.__item_data = search_results[item_index]
            self.__item_parser = self.__ItemPageParser(item)
            self.__item_parser.feed(item_page.text)
            self.gp_change_stats = self.__item_parser.gp_change_stats
            self.pc_change_stats = self.__item_parser.pc_change_stats[::2]
            self.raw_item_history = self.__item_parser.raw_item_history
