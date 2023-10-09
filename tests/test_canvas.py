from unittest.mock import MagicMock, patch

import numpy as Numeric
import pytest
import wx

from sc4_mapper.canvas import OverViewCanvas


@pytest.fixture
def wx_app():
    app = wx.App()
    yield app
    app.Destroy()


def test_canvas_init(wx_app):
    mock_parent = wx.Frame(None)
    mock_parent.region = None
    canvas = OverViewCanvas(mock_parent, -1, size=(100, 100))

    assert canvas.parent == mock_parent
    assert canvas.bmp is None
    assert canvas.buffer is None

    canvas.Destroy()


@patch("sc4_mapper.canvas.tools3D.onePassColors")
@patch("sc4_mapper.canvas.wx.BufferedDC")
@patch("sc4_mapper.canvas.wx.Bitmap")
@patch("sc4_mapper.canvas.wx.Image")
def test_canvas_update_drawing(mock_image, mock_bitmap, mock_dc, mock_one_pass, wx_app):
    mock_parent = wx.Frame(None)
    mock_parent.zoomLevel = 1
    mock_parent.region = MagicMock()
    mock_parent.region.height = Numeric.zeros((200, 200), Numeric.uint16)
    mock_parent.region.waterLevel = 250
    mock_parent.region.imgSize = (200, 200)
    mock_parent.overlayCbx = MagicMock()
    mock_parent.overlayCbx.GetValue.return_value = False

    canvas = OverViewCanvas(mock_parent, -1, size=(100, 100))
    # Mock some methods to avoid real wx calls failing in headless
    canvas.GetViewStart = MagicMock(return_value=(0, 0))
    canvas.ClientSize = (100, 100)

    mock_one_pass.return_value = b"\x00" * (100 * 100 * 3)

    canvas.UpdateDrawing()

    mock_one_pass.assert_called()
    mock_image.assert_called()
    mock_dc.assert_called()

    canvas.Destroy()


def test_canvas_draw_rectangle(wx_app):
    mock_parent = wx.Frame(None)
    mock_parent.region = None
    mock_parent.zoomLevel = 1
    canvas = OverViewCanvas(mock_parent, -1)
    canvas.offX = 10
    canvas.offY = 20

    mock_dc = MagicMock()
    canvas.DrawRectangle(mock_dc, 5, 5, 50, 50)

    mock_dc.DrawRectangle.assert_called_with(15, 25, 50, 50)

    canvas.Destroy()
