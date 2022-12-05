"""
Implements caching functionality.

Copyright (C) 2022 moxxos
"""

import sqlite3
import os
from datetime import date

from platformdirs import user_data_dir

from gppc.__description__ import __title__, __author__


_DATABASE_NAME = 'gppc.sql'
_MAINTABLE_NAME = 'items'
_ITEM_ID = 'id'
_ITEM_NAME = 'item_name'
_SM_IMG = 'sm_img'

_PRICE_DAILY = 'price_daily'
_PRICE_AVERAGE = 'price_average'
_TRADE_VOLUME = 'trade_volume'


class DbManager():
    def __init__(self) -> None:
        appdata_path = user_data_dir(__title__, __author__)
        if not os.path.exists(appdata_path):
            os.makedirs(appdata_path)
        self.__db_conn = sqlite3.connect(
            os.path.join(appdata_path, _DATABASE_NAME))
        self.__db_cur = self.__db_conn.cursor()
        self.__init_db()

        self.__past_dates = [desc[0] for desc in self.__db_cur.execute(
            f"SELECT * FROM {_MAINTABLE_NAME}").description][3:]
        self.__past_dates = [self.__format_date(
            past_date) for past_date in self.__past_dates]

    def __init_db(self) -> None:
        res = self.__db_cur.execute(f"""SELECT name
                                        FROM sqlite_master
                                        WHERE name='{_MAINTABLE_NAME}'""")
        if res.fetchone() is not None:
            return
        self.__db_cur.execute(f"""CREATE TABLE
                                {_MAINTABLE_NAME}
                                ({_ITEM_ID}, {_ITEM_NAME}, {_SM_IMG})""")
        self.__db_conn.commit()

    def close_db(self) -> None:
        """Close the db."""
        self.__db_conn.close()

    @property
    def past_dates(self):
        return self.__past_dates

    def add_date_column(self, input_date: date):
        self.__db_cur.execute(f"""ALTER TABLE {_MAINTABLE_NAME}
                                  ADD COLUMN {self.__format_date(input_date)}""")
        self.__db_conn.commit()

    def does_date_exist(self, input_date: date):
        return input_date in self.__past_dates

    def check_item_date(self, item_id: str, input_date: date) -> bool:
        """Check if an item has historical data stored on the input date."""
        if (self.does_date_exist(input_date)):
            item_date = self.get_item_date(item_id, input_date)
            if (item_date is not None):
                return True
        return False

    def store_item_date(self, item_id, input_date: date,
                        price: str, average: str, volume: str):
        """
        Store an items historical data on the given date.
        Assumes the item's basic data and the date exists.
        """
        print(str(input_date) + ' SUCCESSFULLY STORED: '
              + self.__format_date_data(price, average, volume))
        self.__db_cur.execute(
            f"""UPDATE {_MAINTABLE_NAME}
                SET {self.__format_date(input_date)} = ?
                WHERE id = ?
                """, (self.__format_date_data(price, average, volume), item_id))
        self.__db_conn.commit()

    def get_item_date(self, item_id: str, input_date: date | str):
        """Get item data on the input date. Assumes the date exists."""
        if (isinstance(input_date, date)):
            input_date = self.__format_date(input_date)
        res = self.__db_cur.execute(f"""SELECT {input_date}
                                        FROM {_MAINTABLE_NAME} 
                                        WHERE {_ITEM_ID}='{item_id}'""")
        if (item_date := res.fetchone()) is not None:
            return item_date[0]
        return item_date

    def get_item_past(self, item_id: str):
        """
        Get all past date item data.
        Follows Item historical data format:
        (date, price, average, volume)
        """
        past_date_data = []
        for past_date in self.__past_dates:
            if not self.check_item_date(item_id, past_date):
                print('WARNING MISSING DATE DATA: ' + str(past_date))
            else:
                past_date_data.append(
                    (past_date, *self.__format_date_data(
                        date_data_str=self.get_item_date(item_id, past_date))))
        return past_date_data

    def is_item_stored(self, item_id: str) -> bool:
        """Check if an item is stored."""
        res = self.__db_cur.execute(f"""SELECT {_ITEM_ID} 
                                        FROM {_MAINTABLE_NAME} 
                                        WHERE {_ITEM_ID}='{item_id}'""")
        return res.fetchone() is not None

    def store_item(self, item_id: str, item_name: str, item_smimg: str) -> None:
        """Store an item."""
        self.__db_cur.execute(f"""INSERT INTO
                                  {_MAINTABLE_NAME} ({_ITEM_ID}, {_ITEM_NAME}, {_SM_IMG})
                                  VALUES(?, ?, ?)""", (item_id, item_name, item_smimg))
        self.__db_conn.commit()

    def retrieve_item(self, item_id: str) -> tuple[str, str]:
        """Retrieve an item."""
        res = self.__db_cur.execute(
            f"""SELECT {_ITEM_NAME}, {_SM_IMG}
                FROM {_MAINTABLE_NAME}
                WHERE {_ITEM_ID}='{item_id}'""")
        return res.fetchone()

    @ staticmethod
    def __format_date(input_date: date | str) -> str | date:
        if isinstance(input_date, date):
            return '_' + str(input_date).replace('-', '_')
        return date(*list(map(int, input_date.split('_')[1:])))

    @ staticmethod
    def __format_date_data(price=None, average=None, volume=None, date_data_str=None):
        if (price is None and date_data_str is not None):
            return date_data_str.split('|')
        if (price is not None and date_data_str is None):
            return str(price) + '|' + str(average) + '|' + str(volume)
