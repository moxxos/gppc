"""
Implements the caching functionality. Currently works only for item images.

Copyright (C) 2022 moxxos
"""

from gppc.__description__ import __title__, __author__

import sqlite3
import os

from platformdirs import user_data_dir

DATABASE_NAME = 'gppc.sql'
USE_MEMORY = True
MAINTABLE_NAME = 'items'
ITEM_ID = 'id'
ITEM_NAME = 'item_name'
SM_IMG = 'sm_img'


class DbManager():
    def __init__(self) -> None:
        appdata_path = user_data_dir(__title__, __author__)
        if (not os.path.exists(appdata_path)):
            os.makedirs(appdata_path)
        self.db_conn = sqlite3.connect(
            os.path.join(appdata_path, DATABASE_NAME))
        self.db_cur = self.db_conn.cursor()
        self._init_db()

    def _init_db(self) -> None:
        res = self.db_cur.execute(
            f"SELECT name FROM sqlite_master WHERE name='{MAINTABLE_NAME}'")
        if res.fetchone() is not None:
            return
        self.db_cur.execute(f"""CREATE TABLE {MAINTABLE_NAME}(
            {ITEM_ID},
            {ITEM_NAME},
            {SM_IMG})""")
        self.db_conn.commit()

    def close_db(self) -> None:
        self.db_conn.close()

    def is_item_stored(self, item_id: str) -> bool:
        res = self.db_cur.execute(
            f"SELECT {ITEM_ID} FROM {MAINTABLE_NAME} WHERE {ITEM_ID}='{item_id}'")
        return res.fetchone() is not None

    def store_item(self, item_id: str, item_name: str, item_smimg: str) -> None:
        res = self.db_cur.execute(f"INSERT INTO {MAINTABLE_NAME} VALUES(?, ? ,?)", (
            item_id,
            item_name,
            item_smimg
        ))
        self.db_conn.commit()

    def retrieve_item(self, item_id: str) -> tuple[str, str]:
        res = self.db_cur.execute(
            f"SELECT {ITEM_NAME}, {SM_IMG} FROM {MAINTABLE_NAME} WHERE {ITEM_ID}='{item_id}'")
        return res.fetchone()
