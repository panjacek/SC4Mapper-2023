#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys


def encodeFilename(s):
    """
    @param s The name of the file (of type unicode)
    """

    if isinstance(s, type("")):
        return s

    return s.encode(sys.getfilesystemencoding(), "ignore")
