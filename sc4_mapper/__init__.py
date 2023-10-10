import os
import sys

SCROLL_RATE = 1
EDITMODE_NONE = 0
EDITMODE_SMALL = 1
EDITMODE_MEDIUM = 2
EDITMODE_BIG = 3
EDITMODE_VOID = 4


MAPPER_VERSION = "2023.0b"

if getattr(sys, "frozen", None):
    base_dir = sys._MEIPASS
else:
    base_dir = os.path.dirname(__file__)
