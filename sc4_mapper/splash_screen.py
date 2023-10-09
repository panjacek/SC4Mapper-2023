import logging
import os

import wx
import wx.adv

from sc4_mapper import MAPPER_VERSION, base_dir
from sc4_mapper.overview import OverView

logger = logging.getLogger(__name__)


class SplashScreen(wx.adv.SplashScreen):
    def __init__(self):
        splash_image = os.path.join(base_dir, "static", "splash.jpg")
        bmp = wx.Image(splash_image, wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        super().__init__(bmp, wx.adv.SPLASH_CENTRE_ON_SCREEN | wx.adv.SPLASH_TIMEOUT, 1000, None, -1)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        evt.Skip()
        self.Hide()
        self.ShowMain()

    def ShowMain(self):
        frame = OverView(None, f"NHP SC4Mapper {MAPPER_VERSION} Version", (100, 100))
        frame.Show()
