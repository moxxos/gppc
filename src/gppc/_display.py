"""
Implements the command line display functionality of gppc.

Copyright (C) 2022 moxxos
"""

from io import BytesIO
from PIL import Image

import requests
from climage import climage


def _get_item_pic(pic_link: str) -> str:
    pic_req = requests.get(pic_link, headers={'user-agent': 'Mozilla/5.0'},
                           timeout=100)
    item_gif = Image.open(BytesIO(pic_req.content))
    item_alpha = item_gif.convert('RGBA').getchannel('A')
    item_jpg = Image.new('RGBA', item_gif.size, (0, 0, 0, 255))
    item_jpg.paste(item_gif, mask=item_alpha)
    item_jpg = item_jpg.convert('RGB')
    item_pic = climage._toAnsi(item_jpg,
                               oWidth=7,
                               is_unicode=True,
                               color_type=0,
                               palette='default')
    return item_pic


def _print_item_simple(item: str, price: str, change: str, item_url, sm_img: str):
    newline_1 = sm_img.find('\n')
    newline_2 = sm_img[newline_1 + 1:].find('\n') + newline_1 + 1
    newline_3 = sm_img[newline_2 + 1:].find('\n') + newline_2 + 1
    print(sm_img[0:newline_1], end=' ')
    print('\033]8;;' + item_url + '\033\\'
          + item + '\033]8;;\033\\', end='')
    print(sm_img[newline_1:newline_2], end='')
    print('  \u251C\u2500 ' + price
          + sm_img[newline_2:newline_3], end='')
    print('  \u2514\u2500 '
          + change.replace(' ', '') + sm_img[newline_3:], end='')
