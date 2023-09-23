"""
Implements caching functionality.

Copyright (C) 2022 moxxos
"""

import sqlite3
import os
from datetime import date

import pandas
from platformdirs import user_data_dir

from gppc.__description__ import __title__, __author__

_DATABASE_NAME = 'gppc.sql'
_INFO_TABLE = 'info_table'
_ITEM_ID = 'id'
_ITEM_NAME = 'name'
_ITEM_EXAMINE = 'examine'
_ITEM_MEMBERS = 'members'
_ITEM_LIMIT = 'limit'
_ITEM_LOW_ALCH = 'lowalch'
_ITEM_HIGH_ALCH = 'highalch'
_ITEM_VALUE = 'value'
_ITEM_WIKI_IMG = 'icon'  # name of item image on the wiki
_ITEM_IMG = 'default_img'  # transformed ANSI terminal image
_DATE = 'timestamp'  # will always be UNIX timestamp
_AVG_HIGH = 'avgHighPrice'
_AVG_LOW = 'avgLowPrice'
_HIGH_VOL = 'highPriceVolume'
_LOW_VOL = 'lowPriceVolume'


class DbManager():
    """
    Each item has it's own table that looks like:
                Table Name: id
    date  |  avg high  |  avg low  |  high vol  |  low vol
    date1 |    high1   |    low1   |   highvol1 |   lowvol1
    date2 | ...
    .
    .
    .

    There's also a table that relates name to id to item pic:
                Table Name: name_id_pic
    name  |  id  |  default pic  | ...? maybe more columns for user size pictures?
    item1 |  id1 |  item pic 1
    item2 | ...
    .
    .
    .
    """

    def __init__(self) -> None:

        appdata_path = user_data_dir(__title__, __author__)
        if not os.path.exists(appdata_path):
            os.makedirs(appdata_path)
        # Connect to databse if it exists.
        # If not create databse and connect.
        self.__db_conn = sqlite3.connect(os.path.join(appdata_path, _DATABASE_NAME))
        # Create cursor to manipulate databse.
        self.__db_cur = self.__db_conn.cursor()

        # Create name_id_pic table if it does not exist.
        result = self.__db_cur.execute(f"""
                                       SELECT name
                                       FROM sqlite_master
                                       WHERE name='{_INFO_TABLE}'""")
        if result.fetchone() is None:
            # limit is sql keyword use 'limit't column name instead
            self.__db_cur.execute(f"""
                                  CREATE TABLE {_INFO_TABLE} (
                                    {_ITEM_ID},
                                    {_ITEM_NAME},
                                    {_ITEM_EXAMINE},
                                    {_ITEM_MEMBERS},
                                    '{_ITEM_LIMIT}',
                                    {_ITEM_LOW_ALCH},
                                    {_ITEM_HIGH_ALCH},
                                    {_ITEM_VALUE},
                                    {_ITEM_WIKI_IMG},
                                    {_ITEM_IMG})""")

    def close_db(self) -> None:
        """Close the db."""
        self.__db_conn.close()

    def store_item_info(self, item_info: dict, item_img: str):
        if 'limit' not in item_info.values():
            item_info.update({'limit': None})
        self.__db_cur.execute(f"""
                              INSERT INTO {_INFO_TABLE} (
                                {_ITEM_ID},
                                {_ITEM_NAME},
                                {_ITEM_EXAMINE},
                                {_ITEM_MEMBERS},
                                '{_ITEM_LIMIT}',
                                {_ITEM_LOW_ALCH},
                                {_ITEM_HIGH_ALCH},
                                {_ITEM_VALUE},
                                {_ITEM_WIKI_IMG},
                                {_ITEM_IMG})
                                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                              (
                                  item_info[_ITEM_ID],
                                  item_info[_ITEM_NAME],
                                  item_info[_ITEM_EXAMINE],
                                  item_info[_ITEM_MEMBERS],
                                  item_info[_ITEM_LIMIT],
                                  item_info[_ITEM_LOW_ALCH],
                                  item_info[_ITEM_HIGH_ALCH],
                                  item_info[_ITEM_VALUE],
                                  item_info[_ITEM_WIKI_IMG],
                                  item_img))
        self.__db_conn.commit()

    def retrieve_item_info(self, item_id: int):
        result = self.__db_cur.execute(f"""
                                       SELECT *
                                       FROM {_INFO_TABLE}
                                       WHERE {_ITEM_ID}={str(item_id)}""")
        return result.fetchone()

    def create_item_table(self, item_id: int) -> None:
        self.__db_cur.execute(f"""
                              CREATE TABLE
                              {'item' + str(item_id)} 
                              ({_DATE} PRIMARY KEY,
                              {_AVG_HIGH},
                              {_AVG_LOW},
                              {_HIGH_VOL},
                              {_LOW_VOL})""")
        self.__db_conn.commit()

    def item_table_exists(self, item_id: int) -> bool:
        return self.__db_cur.execute(f"""
                                     SELECT name
                                     FROM sqlite_master
                                     WHERE name='{self.id_to_tablename(item_id)}'""").fetchone()

    def store_item_history(self, item_id: int, history: pandas.DataFrame):
        past_dates = [row[0] for row in self.__db_cur.execute(f"""
                                                              SELECT {_DATE}
                                                              FROM {self.id_to_tablename(item_id)} 
                                                              ORDER BY {_DATE}""").fetchall()]

        # debug stuff
        # if (past_dates):
        #    print(past_dates[len(past_dates) - 1])
        # print(history.iloc[0][_DATE])

        # if there are past dates and earliest date to be stored is less than latest
        # existing stamp then check for dupilcate dates and drop
        if (past_dates and history.iloc[0][_DATE] < past_dates[len(past_dates) - 1]):
            history = history.drop(history[history[_DATE].isin(past_dates)].index)
        # else no stored dates yet or earliest data to be stored timestamp
        # is greater than latest existing time stamp just store right away
        history.to_sql(self.id_to_tablename(item_id),
                       self.__db_conn, if_exists='append', index=False)
        self.__db_conn.commit()
        return len(history)

    def get_item_history(self, item_id: int):
        history = (self.__db_cur.execute(f"""
                                         SELECT *
                                         FROM {self.id_to_tablename(item_id)}
                                         ORDER BY {_DATE}""").fetchall())
        if (history):
            return pandas.DataFrame(history).set_axis([
                _DATE, _AVG_HIGH, _AVG_LOW, _HIGH_VOL, _LOW_VOL], axis=1)
        return None

    @staticmethod
    def id_to_tablename(item_id: int):
        return 'item' + str(item_id)


def foo():
    print('foo')
