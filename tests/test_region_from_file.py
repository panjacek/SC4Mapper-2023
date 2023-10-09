import os
import struct
import tempfile
import zlib

import numpy as Numeric
import pytest
from PIL import Image

from sc4_mapper.region_from_file import (
    SC4MfileHandler,
    SC4MfileHandlerGrey,
    SC4MfileHandlerPNG,
    SC4MfileHandlerRGB,
)


def test_sc4m_file_handler():
    # Create a mock SC4M file
    x_size = 64
    y_size = 64

    # Header: SC4M + version + ySize + xSize + mini
    header = b"SC4M" + struct.pack("i", 0x0200) + struct.pack("i", y_size) + struct.pack("i", x_size) + struct.pack("f", 0.0)

    # Data: SC4D + low bytes + high bytes
    data_low = b"\x01" * (x_size * y_size)
    data_high = b"\x00" * (x_size * y_size)
    sc4d = b"SC4D" + data_low + data_high

    full_data = header + sc4d
    compressed_data = zlib.compress(full_data)

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(compressed_data)
        tmp_path = tmp.name

    try:
        handler = SC4MfileHandler(tmp_path)
        r, config = handler.read()

        assert r.shape == (x_size * y_size,)
        assert Numeric.all(r == 1)
        assert config is None  # Since we didn't provide SC4C
    finally:
        os.unlink(tmp_path)


def test_sc4m_file_handler_with_notes_and_config():
    x_size = 64
    y_size = 64

    header = b"SC4M" + struct.pack("i", 0x0200) + struct.pack("i", y_size) + struct.pack("i", x_size) + struct.pack("f", 0.0)

    # SC4N (Notes)
    notes = b"Hello Notes"
    sc4n = b"SC4N" + struct.pack("i", len(notes)) + notes

    # SC4C (Config)
    config_w = 4
    config_h = 4
    config_data = b"\xff\x00\x00" * (config_w * config_h)  # Red config
    sc4c = b"SC4C" + struct.pack("ii", config_w, config_h) + struct.pack("i", len(config_data)) + config_data

    # SC4D
    data_low = b"\x01" * (x_size * y_size)
    data_high = b"\x00" * (x_size * y_size)
    sc4d = b"SC4D" + data_low + data_high

    # Full data with SC4N and SC4C
    # Note: SC4MfileHandler.read expects SC4N then SC4C then SC4D if present
    full_data = header + sc4n + sc4c + sc4d
    compressed_data = zlib.compress(full_data)

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(compressed_data)
        tmp_path = tmp.name

    try:
        # Mocking wx to avoid showing dialog during tests
        from unittest.mock import MagicMock

        import wx

        # We need to mock wx.App and wx.Dialog.ShowModal
        wx.App()
        with pytest.MonkeyPatch().context() as m:
            m.setattr("wx.adv.AboutDialogInfo", MagicMock())
            # SC4MfileHandler uses about.AuthorBox
            m.setattr("sc4_mapper.about.AuthorBox", MagicMock())

            handler = SC4MfileHandler(tmp_path)
            r, config = handler.read()

            assert r.shape == (x_size * y_size,)
            assert config is not None
            assert config.size == (config_w, config_h)
    finally:
        os.unlink(tmp_path)


def test_grey_handler():
    with tempfile.NamedTemporaryFile(suffix=".bmp", delete=False) as tmp:
        img = Image.new("L", (10, 10), color=100)
        img.save(tmp.name)
        tmp_path = tmp.name

    try:
        handler = SC4MfileHandlerGrey(tmp_path)
        data = handler.read()
        assert data.shape == (100,)
        assert Numeric.all(data == 100)
    finally:
        os.unlink(tmp_path)


def test_png_handler():
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        # Create a 16-bit PNG if possible, or just 8-bit as it converts anyway
        img = Image.new("I", (10, 10), color=1000)
        img.save(tmp.name)
        tmp_path = tmp.name

    try:
        handler = SC4MfileHandlerPNG(tmp_path)
        data = handler.read()
        assert data.shape == (100,)
        assert Numeric.all(data == 1000)
    finally:
        os.unlink(tmp_path)


def test_rgb_handler():
    with tempfile.NamedTemporaryFile(suffix=".bmp", delete=False) as tmp:
        # R=16, G=16, B=0 -> Height = ((1 << 12) | (1 << 8) | 0) = 4096 + 256 = 4352
        img = Image.new("RGB", (10, 10), color=(16, 16, 0))
        img.save(tmp.name)
        tmp_path = tmp.name

    try:
        handler = SC4MfileHandlerRGB(tmp_path)
        data = handler.read()
        assert data.shape == (100,)
        # (1 << 12) | (1 << 8) | 0 = 0x1100 = 4352
        assert Numeric.all(data == 4352)
    finally:
        os.unlink(tmp_path)
