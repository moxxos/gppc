"""
Encapsulates all historical data of a single item.

Copyright (C) 2022 moxxos
"""

from datetime import date
from html.parser import HTMLParser

import requests
import pandas

from gppc._gppc import _search_item_data
from gppc._db import DbManager
from gppc._display import _get_item_pic

_VAR_PRICE = 'average180'
_VAR_TRADE = 'trade180'
_DATA_START = '.push([new Date(\''
_DATA_END = '), '

_PRICE_LEN = len(_VAR_PRICE)
_TRADE_LEN = len(_VAR_TRADE)
_DATA_START_LEN = len(_DATA_START)
_DATA_END_LEN = len(_DATA_END)

ItemHistoryData = tuple[str, str, str, str]


class Item():
    """Encapsulates all historical data of a single item."""

    def __init__(self, item: str):
        if ((item := item.capitalize()) in
            (item_list := list(map(lambda item_tuple: item_tuple[0],
                                   search_results := _search_item_data(item))))):
            # (item_name, item_id, item_price, item_change, item_url, item_pic_url)
            self.__item_data = search_results[item_list.index(item)]
            self.__name = self.__item_data[0]
            self.__id = self.__item_data[1]
            self.__price = self.__item_data[2]
            self.__change = self.__item_data[3]
            self.__url = self.__item_data[4]
            self.__init_item()

            item_page = requests.get(self.__url,
                                     headers={'user-agent': 'Mozilla/5.0'},
                                     timeout=100)
            self.__item_parser = self._ItemPageParser()
            self.__item_parser.feed(item_page.text)

            self.__gp_change_stats = self.__item_parser.gp_change_stats
            self.__pc_change_stats = self.__item_parser.pc_change_stats[::2]
            self.__raw_item_history = self.__item_parser.raw_item_history
            self.__recent_historical = Item.__process_raw_history(
                self.__raw_item_history, [])
        else:
            raise Exception('Item not found')

    def __init_item(self):
        # Store item basic data if it does not already exist
        db_man = DbManager()

        if db_man.is_item_stored(self.__item_data[1]):
            _, self.__item_pic = db_man.retrieve_item(self.__item_data[1])
        else:
            self.__item_pic = _get_item_pic(self.__item_data[5])
            db_man.store_item(self.__item_data[1],
                              self.__item_data[0], self.__item_pic)

        db_man.close_db()

    @property
    def name(self) -> str:
        return self.__name

    @property
    def id(self) -> str:
        return self.__id

    @property
    def current_price(self) -> str:
        return self.__price

    @property
    def change_24h(self) -> str:
        return self.__change

    @property
    def recent_history(self) -> pandas.DataFrame:
        """Returns the most recent 6-month item history."""
        return Item.__format_history(self.__recent_historical)

    @property
    def gp_change_stats(self):
        return tuple(self.__gp_change_stats)

    @property
    def pc_change_stats(self):
        return tuple(self.__pc_change_stats)

    @property
    def full_history(self):
        """
        Stores recent historical item date in the cache. Then retrieves
        all item history data.
        """

        self.__init_item()  # for debugging purposes
        self.save_history()
        db_man = DbManager()
        full_historical = tuple(db_man.get_item_past(self.__item_data[1]))

        db_man.close_db()

        return Item.__format_history(full_historical)

    def save_history(self, verbose=False) -> None:
        """
        Stores recent historical item data in the cache. If the item
        already exists it will read the existing data and add any new historical data.
        """

        update_count = 0
        create_count = 0
        db_man = DbManager()

        for item_date_data in self.__recent_historical:
            # Date, Price, Average, Volume
            if not db_man.does_date_exist(item_date_data[0]):
                db_man.add_date_column(item_date_data[0])
                create_count += 1
            if not db_man.check_item_date(self.__item_data[1], item_date_data[0]):
                db_man.store_item_date(
                    self.__item_data[1], *item_date_data, verbose=verbose)
                update_count += 1

        db_man.close_db()
        if (create_count or update_count):
            print(
                f"SAVED ITEM: {self.__item_data[0]}, id: {self.__item_data[1]}")
        if create_count:
            print(f"{create_count} NEW DATES CREATED")
        if update_count:
            print(f"{update_count} RECORDS UPDATED")

    @ staticmethod
    def __process_raw_history(raw_data: str,
                              output_array: list[str, str]):

        if (price_loc := raw_data.find(_VAR_PRICE + _DATA_START)) == -1:
            return output_array

        item_date = raw_data[price_loc + _PRICE_LEN + _DATA_START_LEN:
                             price_loc + (end_paren_loc := raw_data[price_loc:].
                                          find(_DATA_END)) - 1]
        price = raw_data[(loc := price_loc
                          + end_paren_loc + _DATA_END_LEN):
                         loc + (comma_loc := raw_data[loc:].find(','))]
        average = raw_data[(loc := loc + comma_loc):loc
                           + (bracket_loc := raw_data[loc:].find(']'))]
        if raw_data[loc:].find(_VAR_TRADE + _DATA_START) == -1:
            trade = "No Trade Volume Data Available"
        else:
            trade_loc = raw_data[(loc := loc + bracket_loc):].find(',')
            trade = raw_data[(loc := loc + trade_loc):loc + raw_data[loc:].find(']')]
            trade = trade.strip(_DATA_END)
        output_array.append((date(*(list(map(int, item_date.split('/'))))),
                             price,
                             average.strip(_DATA_END),
                             trade))
        return Item.__process_raw_history(raw_data[loc:], output_array)

    @staticmethod
    def __format_history(data_historical: list[ItemHistoryData]):
        data = list(map(lambda date_data: date_data[1:], data_historical))
        dates = list(map(lambda date_data: date_data[0], data_historical))
        return pandas.DataFrame(data, index=dates,
                                columns=['Price',
                                         'Average',
                                         'Volume']).rename_axis('Date')

    class _ItemPageParser(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.__data = ''
            self.__in_stats_div = False
            self.__in_stats_ul = False
            self.__is_gp_change = False

            self.gp_change_stats = []
            self.pc_change_stats = []
            self.raw_item_history = ''

        def handle_starttag(self, tag: str,
                            attrs: list[tuple[str, str | None]]) -> None:
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
                if self.__is_gp_change:
                    self.gp_change_stats.append(self.__data)
                else:
                    self.pc_change_stats.append(self.__data)

        def handle_data(self, data: str) -> None:
            if data.find(_VAR_PRICE) != -1:
                self.raw_item_history = data
            self.__data = data
