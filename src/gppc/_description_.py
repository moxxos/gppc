"""Contains description info."""

import os

_short_description = "Check OSRS Grand Exchange prices from the command line. Includes limited module functionality."


def _read_md_files(*md_files):
    read_md_files = {}
    md_file_prefix = '../../'
    file_path = os.path.dirname(__file__)
    if (os.getcwd() != file_path):
        file_path = os.chdir(file_path)
    for md_file in md_files:
        with open(md_file_prefix + md_file + '.md', encoding='utf-8') as read_md_file:
            read_md_files[md_file] = read_md_file.read()
    return read_md_files


_long_description = """
%(README)s  

%(CHANGELOG)s
""" % _read_md_files('README', 'CHANGELOG')
