import logging
import os

import pytest

from sc4_mapper.rgnReader import CitySize, SC4File, SC4Region

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def TGI_terrain():
    return (0xA9DD6FF4, 0xE98F9525, 0x00000001)


@pytest.fixture(scope="session")
def region_example_folder(request):
    path = os.path.join(request.config.rootdir, "region_tests", "San Francisco")
    if not os.path.exists(path):
        pytest.skip("Region tests folder not found")
    return path


@pytest.fixture(scope="session")
def sc4_file_example_path(region_example_folder):
    return os.path.join(region_example_folder, "City - New City.sc4")


@pytest.fixture
def mock_sc4_file():
    """Returns an SC4File instance with a dummy path, no file I/O performed in __init__"""
    return SC4File("dummy/path/to/city.sc4")


class TestSC4Entry:
    pass


class TestSC4File:
    def test_init(self, mock_sc4_file):
        assert mock_sc4_file.fileName == "dummy/path/to/city.sc4"

    def test_at_pos(self, mock_sc4_file):
        mock_sc4_file.city_x_position = 0
        mock_sc4_file.city_y_position = 10
        assert mock_sc4_file.check_position(0, 10)

    def test_split_small(self, mock_sc4_file):
        mock_sc4_file.city_x_size = CitySize.SMALL.value
        assert mock_sc4_file.split() == []

    def test_split_large(self, mock_sc4_file):
        mock_sc4_file.city_x_size = CitySize.LARGE.value
        mock_sc4_file.city_y_size = CitySize.LARGE.value
        mock_sc4_file.city_x_position = 0
        mock_sc4_file.city_y_position = 0

        splitted = mock_sc4_file.split()
        assert len(splitted) == 4
        assert splitted[0].city_x_size == 2
        assert splitted[0].city_x_position == 0
        assert splitted[1].city_x_position == 2
        assert splitted[2].city_y_position == 2

    def test_split_medium(self, mock_sc4_file):
        mock_sc4_file.city_x_size = CitySize.MEDIUM.value
        mock_sc4_file.city_y_size = CitySize.MEDIUM.value
        mock_sc4_file.city_x_position = 10
        mock_sc4_file.city_y_position = 10

        splitted = mock_sc4_file.split()
        assert len(splitted) == 4
        assert splitted[0].city_x_size == 1
        assert splitted[0].city_x_position == 10
        assert splitted[1].city_x_position == 11
        assert splitted[2].city_y_position == 11

    # Tests requiring actual file I/O
    def test_read_header(self, sc4_file_example_path):
        sc4_file = SC4File(sc4_file_example_path)
        sc4_file.read_header()
        assert sc4_file.indexRecordEntryCount == 116

    def test_read_entries(self, sc4_file_example_path, mocker):
        sc4_entry_mock = mocker.patch("sc4_mapper.rgnReader.SC4Entry")
        sc4_entry_mock().GetDWORD.return_value = 100
        sc4_file = SC4File(sc4_file_example_path)
        sc4_file.read_header()
        sc4_file.read_entries()

        assert sc4_entry_mock.call_count == 1 + sc4_file.indexRecordEntryCount


def test_save_invalid_size(mocker):
    from sc4_mapper.rgnReader import Save

    city = mocker.MagicMock()
    city.city_x_size = 99
    with pytest.raises(ValueError, match="Invalid city size: 99"):
        Save(city, "some_folder", [], 250)


class TestSC4Region:
    def test_init_region_with_config(self, mocker):
        # This uses valid logic but shouldn't need a real folder if paths are mocked or unused for listdir
        # SC4Region(..., config=...) calls parse_config and skips _init_config (which does listdir)
        parse_mock = mocker.patch("sc4_mapper.rgnReader.parse_config")
        config = mocker.MagicMock()
        region = SC4Region("/dummy/region/path", 200, None, config=config)

        assert region.waterLevel == 200
        assert region.folder is None

        config.convert.assert_called_once()
        assert region.original_config
        parse_mock.assert_called_once()

    def test_init_region_no_config(self, mocker):
        # Mocks _init_config, so no file access needed
        init_mock = mocker.patch("sc4_mapper.rgnReader.SC4Region._init_config")
        region = SC4Region("/dummy/region/path", 200, None, config=None)

        assert region.waterLevel == 200
        init_mock.assert_called_once()

    def test_is_valid(self, region_example_folder):
        # This one probably needs real files or complex mocking. Leaving as integration test.
        # TODO: make SC4Reg fixture
        region = SC4Region(region_example_folder, 200, None, config=None)
        assert region.is_valid()
