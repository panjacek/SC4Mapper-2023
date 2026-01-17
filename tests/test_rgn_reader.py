import logging
import os

import pytest

from sc4_mapper.rgnReader import CitySize, SC4Entry, SC4File, SC4Region

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def TGI_terrain():
    return (0xA9DD6FF4, 0xE98F9525, 0x00000001)


@pytest.fixture(scope="session")
def region_example_folder(request):
    return os.path.join(request.config.rootdir, "region_tests", "San Francisco")


@pytest.fixture(scope="session")
def sc4_file_example_path(region_example_folder):
    return os.path.join(region_example_folder, "City - New City.sc4")


class TestSC4Entry:
    pass


class TestSC4File:
    def test_init(self, sc4_file_example_path):
        sc4_file = SC4File(sc4_file_example_path)
        assert sc4_file.fileName == sc4_file_example_path

    def test_at_pos(self, sc4_file_example_path):
        sc4_file = SC4File(sc4_file_example_path)
        sc4_file.city_x_position = 0
        sc4_file.city_y_position = 10
        assert sc4_file.check_position(0, 10)

    def test_split_small(self, sc4_file_example_path):
        sc4_file = SC4File(sc4_file_example_path)
        sc4_file.city_x_size = CitySize.SMALL.value
        assert sc4_file.split() == []

    @pytest.mark.skip("TODO")
    def test_split_large(self, sc4_file_example_path):
        sc4_file = SC4File(sc4_file_example_path)
        sc4_file.city_x_size = CitySize.LARGE.value
        assert sc4_file.split() == []

    @pytest.mark.skip("TODO")
    def test_split_medium(self, sc4_file_example_path):
        sc4_file = SC4File(sc4_file_example_path)
        sc4_file.city_x_size = CitySize.SMALL.value
        assert sc4_file.split() == []

    # TODO: expand
    def test_read_header(self, sc4_file_example_path):
        sc4_file = SC4File(sc4_file_example_path)
        sc4_file.read_header()
        assert sc4_file.indexRecordEntryCount == 116

    def test_read_entries_loop(self, sc4_file_example_path, mocker):
        sc4_entry_mock = mocker.patch("sc4_mapper.rgnReader.SC4Entry")
        sc4_entry_mock().GetDWORD.return_value = 100
        sc4_file = SC4File(sc4_file_example_path)
        sc4_file.read_header()
        sc4_file.read_entries()

        assert sc4_entry_mock.call_count == 1 + sc4_file.indexRecordEntryCount

    def test_read_entries_version_offset(self, sc4_file_example_path, mocker):
        sc4_entry_mock = mocker.patch("sc4_mapper.rgnReader.SC4Entry")
        sc4_entry_mock().GetDWORD.return_value = 100
        sc4_file = SC4File(sc4_file_example_path)
        sc4_file.read_header()
        sc4_file.read_entries()

        assert sc4_entry_mock.call_count == 1 + sc4_file.indexRecordEntryCount


class TestSC4Region:
    def test_init_region_with_config(self, mocker, region_example_folder):
        parse_mock = mocker.patch("sc4_mapper.rgnReader.parse_config")
        config = mocker.MagicMock()
        region = SC4Region(region_example_folder, 200, None, config=config)

        assert region.waterLevel == 200
        assert region.folder is None

        assert config.convert.called_once()
        assert region.original_config
        assert parse_mock.called_once()

    def test_init_region_no_config(self, mocker, region_example_folder):
        init_mock = mocker.patch("sc4_mapper.rgnReader.SC4Region._init_config")
        region = SC4Region(region_example_folder, 200, None, config=None)

        assert region.waterLevel == 200
        assert init_mock.called_once()

    def test_is_valid(self, region_example_folder):
        # TODO: make SC4Reg fixture
        region = SC4Region(region_example_folder, 200, None, config=None)
        assert region.is_valid()
