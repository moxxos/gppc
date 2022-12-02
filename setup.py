#!/usr/bin/env python3
import os.path

from setuptools import setup


def _read_description(description_path: str) -> str | None:
    """Read a description from source."""
    here = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(here, description_path),
              'r', encoding='utf-8') as description_file:
        file_ext = description_path.split(".")[1]
        if file_ext == 'py':
            for line in description_file.read().splitlines():
                if line.startswith('__short_description__'):
                    delim = '"""' if '"""' in line else '"' if '"' in line else "'"
                    return line.split(delim)[1]
        elif file_ext == 'md':
            return description_file.read()


setup(
    description=_read_description('src/gppc/__description__.py'),
    long_description=_read_description(
        'README.md') + '\n' + _read_description('CHANGELOG.md'),
    long_description_content_type='text/markdown',
    url='https://pypi.org/project/gppc/',
    project_urls={
        'Source': 'https://github.com/moxxos/gppc'
    }
)
