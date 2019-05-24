import sys
import webbrowser

import infogetter
import htmldrawer

"""
Entry point for the script, it stitches together infogetter and htmldrawer, then uses webbrowser to immediately open
the HTML report.

Usage:
    'python bckg_info.py URL | FILEPATH'
    URL: valid URL
    FILEPATH (OPTIONAL): valid path to save the data, defaults at ./output
"""


def call(url, path):
    """
    We create the InfoGetter instance, run it, then pass InfoGetter.data and InfoGetter.filepath to htmldrawer.
    We then open the default the HTML report with webbrowser library.

    :param url: str, valid URL
    :param path: str or None
    :return: None
    """
    ig = infogetter.InfoGetter(url, path)
    data = ig.run()
    path = ig.filepath

    htmldrawer.html_draw(data, path)
    webbrowser.open(path + '/output.html')


# Exceptions


class NoUrl(Exception):
    pass


# Entry point


if __name__ == '__main__':
    try:
        uri = sys.argv[1]
    except IndexError:
        raise NoUrl()

    # Optional
    try:
        filepath = sys.argv[2]
    except IndexError:
        filepath = None

    call(uri, filepath)
