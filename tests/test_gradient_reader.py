"""Tests for the wx-free gradient config parser."""

import pytest

from sc4_mapper.core.gradient_reader import GradientReader

VALID_INI = """\
[background]
0 = #0080FF

[land]
0 = #123456
1000 = #FFFFFF

[water]
0 = #ABCDEF
200 = #00080A
"""


def make_reader(tmp_path, content):
    ini = tmp_path / "basicColors.ini"
    ini.write_text(content)
    return GradientReader(str(ini))


def test_html_color_to_rgb_parses():
    gr = GradientReader.__new__(GradientReader)  # skip ini loading
    assert gr.HTMLColorToRGB("#FF8000") == (255, 128, 0)
    assert gr.HTMLColorToRGB("ff8000") == (255, 128, 0)


def test_html_color_to_rgb_rejects_bad_input():
    gr = GradientReader.__new__(GradientReader)
    with pytest.raises(ValueError):
        gr.HTMLColorToRGB("#FFF")
    with pytest.raises(ValueError):
        gr.HTMLColorToRGB("zzzzzz")


def test_valid_config_parsed(tmp_path):
    gr = make_reader(tmp_path, VALID_INI)
    assert gr.bgColor == (0, 128, 255)
    assert gr.paletteWater == {0: (171, 205, 239), 200: (0, 8, 10)}
    assert gr.paletteLand == {0: (18, 52, 86), 1000: (255, 255, 255)}


def test_missing_file_falls_back_to_defaults(tmp_path):
    gr = GradientReader(str(tmp_path / "nope.ini"))
    assert gr.bgColor == (0, 128, 255)
    assert gr.paletteWater == {0: (123, 189, 214), 200: (0, 8, 74)}
    assert gr.paletteLand == {0: (123, 189, 214), 100: (0, 206, 0), 1000: (255, 255, 255)}


def test_malformed_ini_falls_back_to_defaults(tmp_path):
    gr = make_reader(tmp_path, "[background]\n0 = notacolor\n")
    assert gr.bgColor == (0, 128, 255)
    assert gr.paletteLand == {0: (123, 189, 214), 100: (0, 206, 0), 1000: (255, 255, 255)}
