from unittest.mock import MagicMock, patch

import pytest
import wx

from sc4_mapper import EDITMODE_NONE, EDITMODE_SMALL
from sc4_mapper.overview import OverView


@pytest.fixture
def wx_app():
    app = wx.App()
    yield app
    app.Destroy()


@patch("sc4_mapper.overview.OverViewCanvas")
@patch("sc4_mapper.overview.RegionHandler")
def test_overview_init(mock_handler, mock_canvas, wx_app):
    frame = OverView(None, "Test Title", (800, 600))

    assert "Test Title" in frame.GetTitle()
    assert frame.btnZoomIn.IsEnabled() is False
    assert frame.btnZoomOut.IsEnabled() is False
    assert frame.btnSaveRgn.IsEnabled() is False
    assert frame.btnSave.IsEnabled() is False
    assert frame.overlayCbx.IsEnabled() is False
    assert frame.btnEditMode.IsEnabled() is False

    frame.Destroy()


@patch("sc4_mapper.overview.OverViewCanvas")
@patch("sc4_mapper.overview.RegionHandler")
def test_overview_toggle_edit_mode(mock_handler, mock_canvas, wx_app):
    frame = OverView(None, "Test", (800, 600))

    # Enter edit mode
    frame.btnEditMode.SetValue(True)
    frame.OnToggleEditMode(None)

    assert frame.btnSmall.IsShown() is True
    assert frame.btnLoadRgn.IsShown() is False
    assert frame.overlayCbx.IsEnabled() is False

    # Exit edit mode
    frame.btnEditMode.SetValue(False)
    frame.OnToggleEditMode(None)

    assert frame.btnSmall.IsShown() is False
    assert frame.btnLoadRgn.IsShown() is True
    assert frame.overlayCbx.IsEnabled() is True

    frame.Destroy()


@patch("sc4_mapper.overview.OverViewCanvas")
@patch("sc4_mapper.overview.RegionHandler")
def test_overview_set_edit_mode(mock_handler, mock_canvas, wx_app):
    frame = OverView(None, "Test", (800, 600))

    # Set small city mode
    frame.btnSmall.SetValue(True)
    frame.SetEditModeSmall(None)
    assert frame.editMode == EDITMODE_SMALL

    # Unset small city mode
    frame.btnSmall.SetValue(False)
    frame.SetEditModeSmall(None)
    assert frame.editMode == EDITMODE_NONE

    frame.Destroy()


@patch("sc4_mapper.overview.OverViewCanvas")
@patch("sc4_mapper.overview.RegionHandler")
def test_overview_zoom(mock_handler, mock_canvas, wx_app):
    frame = OverView(None, "Test", (800, 600))
    frame.region = MagicMock()
    frame.region.imgSize = (1024, 1024)
    frame.zoomLevelPow = 1

    frame.OnZoomIn(None)
    assert frame.zoomLevelPow == 0
    assert frame.zoomLevel == 1
    mock_canvas.return_value.SetVirtualSize.assert_called()

    frame.OnZoomOut(None)
    assert frame.zoomLevelPow == 1
    assert frame.zoomLevel == 2

    frame.Destroy()
