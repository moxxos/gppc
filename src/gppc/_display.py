"""
Implements the command line display functionality of gppc.

Copyright (C) 2022 moxxos
"""

from gppc._db import DbManager

import requests
from climage import climage

from PIL import Image
from io import BytesIO
import os

USE_DB = True


def _get_item_pic(pic_src: str) -> Image:
    pic_req = requests.get(pic_src, headers={'user-agent': 'Mozilla/5.0'})
    return Image.open(BytesIO(pic_req.content))


def _print_item_data(item_data: list[tuple[str, str, str, str, str, str]]) -> None:
    DbMan = None
    if (USE_DB):
        DbMan = DbManager()
    os.system('')  # Windows shenanigans
    for item in item_data:
        if (DbMan and DbMan.is_item_stored(item[1])):
            _, item_str = DbMan.retrieve_item(item[1])
        else:
            item_gif = _get_item_pic(item[5])
            item_alpha = item_gif.convert('RGBA').getchannel('A')
            item_jpg = Image.new('RGBA', item_gif.size, (0, 0, 0, 255))
            item_jpg.paste(item_gif, mask=item_alpha)
            item_jpg = item_jpg.convert('RGB')
            item_str = climage._toAnsi(item_jpg,
                                       oWidth=7,
                                       is_unicode=True,
                                       color_type=0,
                                       palette='default')
            if (DbMan):
                DbMan.store_item(
                    item[1],
                    item[0],
                    item_str)
        n1 = item_str.find('\n')
        n2 = item_str[n1 + 1:].find('\n') + n1 + 1
        n3 = item_str[n2 + 1:].find('\n') + n2 + 1
        print(item_str[0:n1], end=' ')
        print('\033]8;;' + item[4] + '\033\\' +
              item[0] + '\033]8;;\033\\', end='')
        print(item_str[n1:n2], end='')
        print('  \u251C\u2500 ' + item[2] + item_str[n2:n3], end='')
        print('  \u2514\u2500 ' +
              item[3].replace(' ', '') + item_str[n3:], end='')
    if (DbMan):
        DbMan.close_db()
