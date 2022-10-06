#!/usr/bin/env python3
import os.path
from setuptools import setup


def _read_short(description_path):
    """Read a short description from source."""
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, description_path), 'r') as _description_py:
        for line in _description_py.read().splitlines():
            if line.startswith('_short_description'):
                delim = '"""' if '"""' in line else '"' if '"' in line else "'"
                return line.split(delim)[1]


def _write_short(description_name, description_path):
    """Dynamically write a short description file for pyproject.toml."""
    short_txt = open(description_name, "w")
    desc = _read_short(description_path)
    short_txt.write(str(desc))
    short_txt.close


_write_short('SHORT.txt', 'src/gppc/_description_.py')


setup()
