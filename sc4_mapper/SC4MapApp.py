#!/usr/bin/env python3
# -*- coding: latin-1 -*-
import logging

import tools3D
import wx  # This module uses the new wx namespace
import wx.adv

from sc4_mapper import base_dir
from sc4_mapper.splash_screen import SplashScreen

logging.basicConfig(
    format="[%(asctime)s.%(msecs)03d][%(filename)s:%(lineno)d][%(levelname)s]:%(message)s",
    datefmt="%Y%m%d-%H:%M:%S",
    level="DEBUG",
)
logger = logging.getLogger(__name__)


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


class SC4App(wx.App):
    def OnInit(self):
        splash = SplashScreen()
        splash.Show()
        return True


def check_tools_pyd():
    # FIXME: no idea...
    try:
        version = tools3D.GetVersion()
        if version != "v1.0d":
            raise ValueError(version)
        return True
    except ValueError as tools_crash:
        print(tools_crash)
        app = ErrApp(False)
        app.MainLoop()
        exit()


def main():
    assert check_tools_pyd()
    logger.info(base_dir)
    # mainPath = sys.path[0]
    # os.chdir(mainPath)
    app = SC4App(False)
    app.MainLoop()


if __name__ == "__main__":
    main()
