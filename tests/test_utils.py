import pytest

from sc4_mapper import utils, zipUtils


@pytest.mark.parametrize("fancy_name", ["plain", "óóóćź", "ŁŁŁó", "что-нибудь"])
def test_encode_filename(fancy_name):
    assert fancy_name == utils.encodeFilename(fancy_name)


# TODO:
# def test_zip_stream
