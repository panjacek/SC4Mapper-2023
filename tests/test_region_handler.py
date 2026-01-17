from unittest.mock import MagicMock
from sc4_mapper.region_handler import RegionHandler


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
