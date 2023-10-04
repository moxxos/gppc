"""
Encapsulates all historical data of a single item.

Copyright (C) 2022 moxxos
"""

from collections.abc import Iterator
from datetime import datetime
from html.parser import HTMLParser

import requests
import pandas

from gppc._constant import _MAP_API, _ITEM_URL, _REQUEST_HEADER, _HISTORY_API, _TIMESTEP_PARAMETER
from gppc._db import DbManager
from gppc._display import _get_item_pic

_RAW_LIST = requests.get(_MAP_API, headers=_REQUEST_HEADER, timeout=100).json()
_NAME_LIST = list(map(lambda i: i['name'], _RAW_LIST))

_VAR_PRICE = 'average180'
_VAR_TRADE = 'trade180'
_DATA_START = '.push([new Date(\''
_DATA_END = '), '

_PRICE_LEN = len(_VAR_PRICE)
_TRADE_LEN = len(_VAR_TRADE)
_DATA_START_LEN = len(_DATA_START)
_DATA_END_LEN = len(_DATA_END)
_TIMESTEP_MAP = {'1day': '5m', '2week': '1h', '3month': '6h', '1year': '24h'}

ItemHistoryData = tuple[str, str, str, str]

# temporary bool in place of giving user option between api and osrs ge site
_TEMP_USE_API = True


class Catalog(list):
    """Represents a list of items."""

    def __init__(self, *items) -> None:
        self.__id_map = {}  # id -> name
        self.__name_map = {}  # name -> id
        self.__pos_map = {}  # name -> position in raw list
        for item_name in (items if items else _NAME_LIST):
            try:
                if items:
                    item_name = item_name[0].capitalize() + item_name[1:]
                self.__id_map.update(
                    {(id := _RAW_LIST[(pos := _NAME_LIST.index(item_name))])['id']: item_name})
                self.__name_map.update({item_name: id})
                self.__pos_map.update({item_name: pos})
                # print("Successfully added: " + item_name)
            except ValueError:
                print(item_name + " was not found")
        # print(self.__id_map.values())
        super().__init__(self.__id_map.values())

    def __getitem__(self, key):
        if isinstance(key, int):
            return Item((item_name := super().__getitem__(key)), self.__pos_map[item_name])
        return Item(key, self.__pos_map[key])
        # I can make item do all the hard lifting from here I think

    def __iter__(self) -> Iterator:
        for item_name in super().__iter__():
            yield Item(item_name, self.__pos_map[item_name])

    def save_history(self, timestep=None):
        if timestep and timestep not in _TIMESTEP_MAP.keys():
            raise ValueError('timestep must be one of: ' + str(list(_TIMESTEP_MAP.keys())))
        for item in self:
            if (timestep):
                item._Item__get_recent_history(_TIMESTEP_MAP[timestep])
                item.save_history(timestep)
            else:
                for ts in _TIMESTEP_MAP.values():
                    item._Item__get_recent_history(ts)
                item.save_history()


class Item():
    """Encapsulates all historical data of a single item."""

    def __init__(self, item_name: str, _raw_list_pos: int = None):
        if ((item_name := item_name[0].capitalize() + item_name[1:]) in _NAME_LIST):
            _raw_list_pos = _raw_list_pos if _raw_list_pos else _NAME_LIST.index(item_name)
            self.__info = _RAW_LIST[_raw_list_pos]
            self.__change = None
            self.__recent_history = {'5m': None, '1h': None, '6h': None, '24h': None}

            # these might not even be necessary until relevant information is called
            # e.g. current price, item pic, recent history
            # self.__init_item_basic()
            # self.__init_item_stats()

        else:
            raise ValueError('Item not found: ' + item_name)

    def __init_item_basic(self):
        # Store item basic data if it does not already exist
        db_man = DbManager()

        if db_man.is_item_stored(self.__item_data[1]):
            _, self.__item_pic = db_man.retrieve_item(self.__item_data[1])
        else:
            self.__item_pic = _get_item_pic(self.__item_data[5], 7)
            db_man.store_item(self.__item_data[1], self.__item_data[0], self.__item_pic)

        db_man.close_db()

    # offer two ways to get item data
    # use api for default since it will be faster
    # user can eventually set preffered option
    # if api is down use osrs ge site as backup and vice versa
    def __get_raw_history(self, timestep):
        raw_history = requests.get(_HISTORY_API.replace(_TIMESTEP_PARAMETER, timestep) + str(self.__info['id']),
                                   headers=_REQUEST_HEADER,
                                   timeout=100).json()['data']
        return raw_history if raw_history else None

    def __get_recent_history(self, timestep) -> pandas.DataFrame:
        if (timestep not in _TIMESTEP_MAP.values()):
            raise ValueError('Timestep must one of: ' + str(list(_TIMESTEP_MAP.values())))
        history = self.__get_raw_history(timestep)
        if (history):
            history = pandas.DataFrame(history)
            # drop any missing data
            history = history.drop(history[(history['highPriceVolume'] == 0)
                                           & (history['lowPriceVolume'] == 0)].index)
            # store timestamp copy of history for possiblilty of save to database
            self.__recent_history[timestep] = pandas.DataFrame(history)
        else:
            print('Missing API history data for: ' + self.__info['name'])
        return history

    def save_history(self, timestep=None):
        DbMan = DbManager()
        if (not DbMan.item_table_exists(self.__info['id'])):
            DbMan.create_item_table(self.__info['id'])
        if (timestep):
            if (timestep not in _TIMESTEP_MAP.keys()):
                raise ValueError('Timestep must one of: ' + str(list(_TIMESTEP_MAP.keys())))
            new_records = DbMan.store_item_history(
                self.__info['id'], self.__recent_history[_TIMESTEP_MAP[timestep]])
        else:
            new_records = 0
            for ts in self.__recent_history:
                if (self.__recent_history[ts] is not None):
                    new_records = new_records + DbMan.store_item_history(
                        self.__info['id'], self.__recent_history[ts])
        DbMan.close_db()
        print(str(new_records) + ' new records added for item: ' + self.__info['name'])

    def __init_stats_no_api(self):

        item_page = requests.get(_ITEM_URL + str(self.__info['id']),
                                 headers=_REQUEST_HEADER,
                                 timeout=100)
        item_parser = self._ItemPageParser()
        item_parser.feed(item_page.text)

        gp_change_stats = item_parser.gp_change_stats
        pc_change_stats = item_parser.pc_change_stats[::2]
        self.__change = pandas.DataFrame([gp_change_stats, pc_change_stats],
                                         index=['Change', 'Percentage'],
                                         columns=['24hr', '1 month', '3 month', '6 month'])

        raw_item_history = item_parser.raw_item_history
        self.__recent_history = Item.__process_raw_history(raw_item_history, [])
        self.__current_price = (current := self.__recent_history[178])[1]
        self.__current_average = current[2]

    @property
    def name(self) -> str:
        return self.__info['name']

    @property
    def id(self) -> str:
        return self.__info['id']

    @property
    def examine(self) -> str:
        return self.__info['examine']

    @property
    def members(self) -> bool:
        return self.__info['members']

    @property
    def lowalch(self) -> int:
        return self.__info['lowalch']

    @property
    def highalch(self) -> int:
        return self.__info['highalch']

    @property
    def limit(self) -> int:
        return self.__info['limit']

    @property
    def value(self) -> int:
        return self.__info['value']

    """
    @property
    def price(self) -> int:
        if not self.__current_price:
            self.__init_stats()
        return self.__current_price

    @property
    def average(self) -> int:
        if not self.__current_average:
            self.__init_stats()
        return self.__current_average

    @property
    def change(self) -> pandas.DataFrame:
        if not self.__change:
            self.__init_stats()
        return self.__change
    """

    @property
    def history_1day(self):
        # convert timestamp to readable datetime
        history = self.__get_recent_history('5m')
        if (history is not None):
            history['timestamp'] = history['timestamp'].map(datetime.fromtimestamp)
        return history

    @property
    def history_2week(self):
        history = self.__get_recent_history('1h')
        if (history is not None):
            history['timestamp'] = history['timestamp'].map(datetime.fromtimestamp)
        return history

    @property
    def history_3month(self):
        history = self.__get_recent_history('6h')
        if (history is not None):
            history['timestamp'] = history['timestamp'].map(datetime.fromtimestamp)
        return history

    @property
    def history_1year(self):
        history = self.__get_recent_history('24h')
        if (history is not None):
            history['timestamp'] = history['timestamp'].map(datetime.fromtimestamp)
        return history

    @property
    def full_history(self):
        """
        Stores recent historical item data in the cache. If the item
        already exists it will read the existing data and add any new historical data.
        """
        self.save_history()
        DbMan = DbManager()
        history = DbMan.get_item_history(self.__info['id'])
        DbMan.close_db()
        if (history is not None):
            history['timestamp'] = history['timestamp'].map(datetime.fromtimestamp)
        return history

    @staticmethod
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
    
    # OSRS website backup below
    @staticmethod
    def __format_history(data_historical: list[ItemHistoryData]):
        data = list(map(lambda date_data: date_data[1:], data_historical))
        dates = list(map(lambda date_data: date_data[0], data_historical))
        return pandas.DataFrame(data, index=dates,
                                columns=['Price',
                                         'Average',
                                         'Volume']).rename_axis('Date')

    @staticmethod
    def __format_price(price: str):
        if price.find('k') + 1:
            return int(float(price.split('k')[0]) * 1000)
        if price.find('m') + 1:
            return int(float(price.split('m')[0]) * 1000000)
        if price.find('b') + 1:
            return int(float(price.split('b')[0]) * 1000000000)
        return int(price.replace(',', ''))

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
