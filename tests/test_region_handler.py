from unittest.mock import MagicMock, patch

import numpy as Numeric
import pytest
import wx

from sc4_mapper.region_handler import RegionHandler


@pytest.fixture
def wx_app():
    app = wx.App()
    yield app
    app.Destroy()


def test_region_handler_init():
    mock_frame = MagicMock()
    handler = RegionHandler(mock_frame)
    assert handler.frame == mock_frame


def test_create_rgn_init():
    mock_frame = MagicMock()
    handler = RegionHandler(mock_frame)

    handler.CreateRgnInit()

    mock_frame.btnSave.Enable.assert_called_with(False)
    mock_frame.btnExportRgn.Enable.assert_called_with(False)
    mock_frame.btnSaveRgn.Enable.assert_called_with(False)
    assert mock_frame.region is None
    mock_frame.back.SetVirtualSize.assert_called_with((100, 100))
    assert mock_frame.zoomLevel == 1
    assert mock_frame.zoomLevelPow == 0


def test_create_rgn_ok():
    mock_frame = MagicMock()
    handler = RegionHandler(mock_frame)

    handler.CreateRgnOk("TestRegion")

    mock_frame.btnSave.Enable.assert_called_with(True)
    mock_frame.btnSaveRgn.Enable.assert_called_with(True)
    mock_frame.btnExportRgn.Enable.assert_called_with(True)
    mock_frame.btnZoomIn.Enable.assert_called_with(False)
    mock_frame.btnZoomOut.Enable.assert_called_with(True)


@patch("sc4_mapper.region_handler.wx.DirDialog")
@patch("sc4_mapper.region_handler.wx.ProgressDialog")
@patch("sc4_mapper.region_handler.rgnReader.SC4Region")
def test_load_a_region_success(mock_sc4_region, mock_prog_dlg, mock_dir_dlg, wx_app, mocker):
    mock_frame = MagicMock()
    handler = RegionHandler(mock_frame)

    # Mock DirDialog
    mock_dir_inst = mock_dir_dlg.return_value
    mock_dir_inst.ShowModal.return_value = wx.ID_OK
    mock_dir_inst.GetPath.return_value = "/mock/path"

    # Mock SC4Region
    mock_region_inst = mock_sc4_region.return_value
    mock_region_inst.all_cities = [MagicMock()]
    mock_region_inst.is_valid.return_value = True

    with patch("os.path.isdir", return_value=True):
        res = handler.LoadARegion()

    assert res == mock_region_inst
    assert mock_frame.regionName == "path"
    mock_region_inst.show.assert_called_once()
    mock_prog_dlg.return_value.Update.assert_called_with(0)


@patch("sc4_mapper.region_handler.wx.DirDialog")
def test_load_a_region_cancel(mock_dir_dlg, wx_app):
    mock_frame = MagicMock()
    handler = RegionHandler(mock_frame)

    mock_dir_inst = mock_dir_dlg.return_value
    mock_dir_inst.ShowModal.return_value = wx.ID_CANCEL

    res = handler.LoadARegion()

    assert res is None
    mock_dir_inst.Destroy.assert_called_once()


@patch("sc4_mapper.region_handler.wx.FileDialog")
@patch("sc4_mapper.region_handler.wx.ProgressDialog")
@patch("sc4_mapper.region_handler.zlib.compressobj")
@patch("builtins.open", new_callable=MagicMock)
def test_export_as_sc4m_success(mock_open, mock_zlib, mock_prog_dlg, mock_file_dlg, wx_app):
    mock_frame = MagicMock()
    handler = RegionHandler(mock_frame)

    # Mock FileDialog for HTML file
    mock_file_inst = mock_file_dlg.return_value
    mock_file_inst.ShowModal.return_value = wx.ID_OK
    mock_file_inst.GetPaths.return_value = ["/mock/notes.html"]

    # Mock region and cities
    mock_city = MagicMock()
    mock_city.city_x_position = 0
    mock_city.city_y_position = 0
    mock_city.city_x_size = 1
    mock_city.city_y_size = 1

    mock_frame.region.all_cities = [mock_city]
    mock_frame.region.waterLevel = 250
    mock_frame.region.height = Numeric.zeros((100, 100), Numeric.uint16)

    mock_config = MagicMock()
    mock_config.size = (4, 4)

    # Mock zlib
    mock_compressor = mock_zlib.return_value
    mock_compressor.compress.return_value = b"compressed_data"
    mock_compressor.flush.return_value = b"flushed_data"

    handler.ExportAsSC4M("/mock/out.sc4m", mock_config, 0, 0, [0, 0, 4, 4])

    assert mock_open.call_count >= 1
    mock_prog_dlg.return_value.Update.assert_called()
    mock_config.save.assert_called()


@patch("sc4_mapper.region_handler.wx.ProgressDialog")
@patch("sc4_mapper.region_handler.Image")
def test_export_as_rgb_success(mock_image, mock_prog_dlg, wx_app):
    mock_img_new = mock_image.new
    mock_frame = MagicMock()
    handler = RegionHandler(mock_frame)

    mock_city = MagicMock()
    mock_city.xPos = 0
    mock_city.yPos = 0
    mock_city.city_x_position = 0
    mock_city.city_y_position = 0
    mock_city.city_x_size = 1
    mock_city.city_y_size = 1

    mock_frame.region.all_cities = [mock_city]
    mock_frame.region.height = Numeric.zeros((100, 100), Numeric.uint16)

    mock_config = MagicMock()
    mock_config.size = (4, 4)

    handler.ExportAsRGB("/mock/out.bmp", mock_config, 0, 0, [0, 0, 4, 4])

    mock_img_new.assert_called()
    mock_prog_dlg.return_value.Update.assert_called()
    mock_config.save.assert_called()


@patch("sc4_mapper.region_handler.wx.ProgressDialog")
@patch("sc4_mapper.region_handler.Image")
def test_export_as_png_success(mock_image, mock_prog_dlg, wx_app):
    mock_img_new = mock_image.new
    mock_frame = MagicMock()
    handler = RegionHandler(mock_frame)

    mock_city = MagicMock()
    mock_city.xPos = 0
    mock_city.yPos = 0
    mock_city.city_x_position = 0
    mock_city.city_y_position = 0
    mock_city.city_x_size = 1
    mock_city.city_y_size = 1

    mock_frame.region.all_cities = [mock_city]
    mock_frame.region.height = Numeric.zeros((100, 100), Numeric.uint16)

    mock_config = MagicMock()
    mock_config.size = (4, 4)

    handler.ExportAsPNG("/mock/out.png", mock_config, 0, 0, [0, 0, 4, 4])

    mock_img_new.assert_called()
    mock_prog_dlg.return_value.Update.assert_called()
    mock_config.save.assert_called()
