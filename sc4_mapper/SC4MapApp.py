#!/usr/bin/env python3
# -*- coding: latin-1 -*-
import tools3D
import wx  # This module uses the new wx namespace
import wx.adv

# FIXME: no idea...
try:
    version = tools3D.GetVersion()
    if version != "v1.0d":
        raise ValueError
except ValueError as tools_crash:
    print(tools_crash)

    class ErrApp(wx.App):
        def OnInit(self):
            dlg = wx.MessageDialog(
                None,
                (
                    "It seems that there is a conflicting dll\n",
                    "Please make sure to uninstall previous version\nAnd reinstall this one",
                ),
                "Error",
                wx.OK | wx.ICON_ERROR,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return False

    app = ErrApp(False)
    app.MainLoop()
    exit()


import logging
import os
import os.path
import sys

from sc4_mapper import MAPPER_VERSION
from sc4_mapper.overview import OverView

logging.basicConfig(level="DEBUG")
logger = logging.getLogger(__name__)


# FIXME: new WX
# class SplashScreen(wx.SplashScreen):
class SplashScreen(wx.adv.SplashScreen):
    def __init__(self):
        bmp = wx.Image(os.path.join(basedir, "static/splash.jpg"), wx.BITMAP_TYPE_JPEG).ConvertToBitmap()
        super().__init__(bmp, wx.adv.SPLASH_CENTRE_ON_SCREEN | wx.adv.SPLASH_TIMEOUT, 1000, None, -1)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, evt):
        evt.Skip()
        self.Hide()
        self.ShowMain()

    def ShowMain(self):
        frame = OverView(None, "NHP SC4Mapper %s Version" % MAPPER_VERSION, (100, 100))
        # frame = OverView(self, "NHP SC4Mapper %s Version" % MAPPER_VERSION, (100, 100))
        frame.Show()


class SC4App(wx.App):
    def OnInit(self):
        splash = SplashScreen()
        splash.Show()
        return True


def main():
    mainPath = sys.path[0]
    os.chdir(mainPath)
    app = SC4App(False)
    app.MainLoop()


if __name__ == "__main__":
    if getattr(sys, "frozen", None):
        basedir = sys._MEIPASS
    else:
        basedir = os.path.dirname(__file__)
    logger.info(basedir)
    # FIXME: WTF is this?
    mainPath = sys.path[0]
    os.chdir(mainPath)
    main()
