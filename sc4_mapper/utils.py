#!/usr/bin/env python

import sys


def encodeFilename(s):
    """
    @param s The name of the file (of type unicode)
    """

    if isinstance(s, str):
        return s

    return s.encode(sys.getfilesystemencoding(), "ignore")
