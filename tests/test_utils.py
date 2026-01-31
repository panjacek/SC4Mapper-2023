import pytest

from sc4_mapper import utils


@pytest.mark.parametrize("fancy_name", ["plain", "óóóćź", "ŁŁŁó", "что-нибудь"])
def test_encode_filename_string(fancy_name):
    assert fancy_name == utils.encodeFilename(fancy_name)


def test_encode_filename_none():
    with pytest.raises(AttributeError):
        utils.encodeFilename(None)


def test_encode_filename_bytes():
    # In Python 3, bytes don't have .encode(), so this should fail if passed bytes
    # and it's not detected as a string.
    b = b"some_bytes"
    with pytest.raises(AttributeError):
        utils.encodeFilename(b)
