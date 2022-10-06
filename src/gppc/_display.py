"""Implements the command line display functionality of gppc."""

import requests
from climage import climage

from PIL import Image
from io import BytesIO


def _get_item_pic(pic_src: str) -> Image:
    headers = {
        'user-agent': 'Mozilla/5.0'
    }
    pic_req = requests.get(pic_src, headers=headers)
    return Image.open(BytesIO(pic_req.content))


def _print_item_data(item_data: list[tuple[str, str, str, str, str, str]]) -> None:

    for item in item_data:
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
        n1 = item_str.find('\n')
        n2 = item_str[n1 + 1:].find('\n') + n1 + 1
        n3 = item_str[n2 + 1:].find('\n') + n2 + 1
        print(item_str[0:n1], end=' ')
        print('\033]8;;' + item[4] + '\033\\' +
              item[0] + '\033]8;;\033\\', end='')
        print(item_str[n1:n2], end='')
        print('  \u251C\u2500 ' + item[2] + item_str[n2:n3], end='')
        print('  \u2514 ' + item[3] + item_str[n3:], end='')


def _print_item_data_old(item_data: list[tuple[str, str, str, str]]) -> None:
    longest_prop = [0, 0, 0, 0]
    for item in item_data:
        longest_prop = list(
            map(lambda a, b: max(a, len(b)), longest_prop, item))

    item_pic = _ready_test_image()

    for item in item_data:
        # 4 element array of 2-tuples containing padding for
        # the left and right of each item property:
        # [(name_padding_left, name_padding_right), ...]
        padding_array = list(
            map(lambda a, b: ((x := abs((y := len(b) - a))//2), x + (y % 2 > 0)), longest_prop, item))
        item_str = " | Item: %(name_pad_l)s%(name)s%(name_pad_r)s | ID: %(id_pad_l)s%(id)s%(id_pad_r)s | Price: %(price_pad_l)s%(price)s%(price_pad_r)s | 24h Change: %(change_pad_l)s%(change)s%(change_pad_r)s" % {
            'name': item[0], 'name_pad_l': ' '*padding_array[0][0], 'name_pad_r': ' '*padding_array[0][1],
            'id': item[1], 'id_pad_l': ' '*padding_array[1][0], 'id_pad_r': ' '*padding_array[1][1],
            'price': item[2], 'price_pad_l': ' '*padding_array[2][0], 'price_pad_r': ' '*padding_array[2][1],
            'change': item[3], 'change_pad_l': ' '*padding_array[3][0], 'change_pad_r': ' '*padding_array[3][1]}
        item_str = item_pic[0:159+164] + item_str + item_pic[159+164:]
        print(item_str + ' and the link is ' + item[4])
