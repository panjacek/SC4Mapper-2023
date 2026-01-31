import logging
import os
import sys

import wx
import wx.adv

from sc4_mapper import (
    EDITMODE_BIG,
    EDITMODE_MEDIUM,
    EDITMODE_NONE,
    EDITMODE_SMALL,
    EDITMODE_VOID,
    SCROLL_RATE,
    rgnReader,
)
from sc4_mapper.canvas import OverViewCanvas
from sc4_mapper.region_handler import RegionHandler

logger = logging.getLogger(__name__)


class OverView(wx.Frame):
    def __init__(
        self,
        parent,
        title,
        virtualSize,
        pos=wx.DefaultPosition,
        size=wx.DefaultSize,
        style=wx.DEFAULT_FRAME_STYLE | wx.MINIMIZE_BOX | wx.MAXIMIZE_BOX,
    ):
        super().__init__(parent, -1, title, pos, size, style)
        self.region = None
        self.regionName = ""
        self.regionPath = ""
        self.handler = RegionHandler(self)

        self.SetSizeHints(wx.Size(700, 400), wx.DefaultSize)
        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

        self.editMode = EDITMODE_NONE

        # Tools
        self.btnSmall = wx.ToggleButton(self, -1, "Small\nCity")
        self.Bind(wx.EVT_TOGGLEBUTTON, self.SetEditModeSmall, self.btnSmall)
        self.btnMedium = wx.ToggleButton(self, -1, "Medium\nCity")
        self.Bind(wx.EVT_TOGGLEBUTTON, self.SetEditModeMedium, self.btnMedium)
        self.btnBig = wx.ToggleButton(self, -1, "Big\nCity")
        self.Bind(wx.EVT_TOGGLEBUTTON, self.SetEditModeBig, self.btnBig)
        self.btnVoid = wx.ToggleButton(self, -1, "Erase\nCity")
        self.Bind(wx.EVT_TOGGLEBUTTON, self.SetEditModeVoid, self.btnVoid)
        self.btnRevert = wx.Button(self, -1, "Revert\nConfig")
        self.Bind(wx.EVT_BUTTON, self.RevertConfig, self.btnRevert)

        self.btnSave = wx.Button(self, -1, "Save\nImage")
        self.Bind(wx.EVT_BUTTON, self.handler.SaveBmp, self.btnSave)
        self.btnLoadRgn = wx.Button(self, -1, "Load\nRegion")
        self.Bind(wx.EVT_BUTTON, self.handler.OpenRgn, self.btnLoadRgn)
        self.btnCreateRgn = wx.Button(self, -1, "Create\nRegion")
        self.Bind(wx.EVT_BUTTON, self.handler.CreateRgn, self.btnCreateRgn)
        self.btnSaveRgn = wx.Button(self, -1, "Save\nRegion")
        self.Bind(wx.EVT_BUTTON, self.handler.SaveRgn, self.btnSaveRgn)
        self.btnExportRgn = wx.Button(self, -1, "Export\nRegion")
        self.Bind(wx.EVT_BUTTON, self.handler.ExportRgn, self.btnExportRgn)
        self.btnQuit = wx.Button(self, -1, "Quit")
        self.Bind(wx.EVT_BUTTON, self.OnCloseWindow, self.btnQuit)

        self.btnZoomIn = wx.Button(self, -1, "+")
        self.Bind(wx.EVT_BUTTON, self.OnZoomIn, self.btnZoomIn)
        self.btnZoomOut = wx.Button(self, -1, "-")
        self.Bind(wx.EVT_BUTTON, self.OnZoomOut, self.btnZoomOut)

        self.overlayCbx = wx.CheckBox(self, wx.ID_ANY, "Cities\noverlay")
        self.overlayCbx.Bind(wx.EVT_CHECKBOX, self.OnOverlay)
        self.overlayCbx.SetValue(True)

        self.btnEditMode = wx.ToggleButton(self, wx.ID_ANY, "Edit\nConfig.bmp")
        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnToggleEditMode, self.btnEditMode)

        self.back = OverViewCanvas(self, -1, size=size)
        self.back.SetBackgroundColour("WHITE")
        self.back.SetVirtualSize(virtualSize)
        self.back.SetScrollRate(SCROLL_RATE, SCROLL_RATE)
        self.back.Bind(wx.EVT_MOTION, self.OnMouseMove)
        self.back.Bind(wx.EVT_LEFT_UP, self.OnLeftUp)
        self.back.Bind(wx.EVT_LEFT_DOWN, self.OnLeftDown)

        self.box = wx.BoxSizer(wx.VERTICAL)
        boxh = wx.BoxSizer(wx.HORIZONTAL)

        boxh.Add(self.btnSmall, 0)
        self.btnSmall.Hide()
        boxh.Add(self.btnMedium, 0)
        self.btnMedium.Hide()
        boxh.Add(self.btnBig, 0)
        self.btnBig.Hide()
        boxh.Add(self.btnVoid, 0)
        self.btnVoid.Hide()
        boxh.Add(self.btnRevert, 0)
        self.btnRevert.Hide()

        boxh.Add(self.btnLoadRgn, 0)
        boxh.Add(self.btnCreateRgn, 0)
        boxh.Add(self.btnSaveRgn, 0)
        boxh.Add(self.btnExportRgn, 0)
        boxh.Add(self.btnSave, 0)
        boxh.Add(
            wx.StaticLine(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_VERTICAL),
            0,
            wx.EXPAND | wx.RIGHT | wx.LEFT,
            5,
        )
        boxh.Add(self.btnEditMode, 0)
        boxh.Add(self.btnZoomIn, 0, wx.ALIGN_CENTER_VERTICAL)
        boxh.Add(self.btnZoomOut, 0, wx.ALIGN_CENTER_VERTICAL)
        boxh.Add(self.overlayCbx, 0, wx.ALIGN_CENTER_VERTICAL)
        boxh.Add(
            wx.StaticLine(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_VERTICAL),
            0,
            wx.EXPAND | wx.RIGHT | wx.LEFT,
            5,
        )

        boxh.AddStretchSpacer()
        boxh.Add(self.btnQuit, 0, wx.ALIGN_CENTER_VERTICAL)
        self.box.Add(boxh, 0, wx.EXPAND)
        self.box.Add(wx.StaticLine(self), 0, wx.EXPAND)
        self.box.Add(self.back, 1, wx.EXPAND)
        self.box.Fit(self)
        self.SetSizer(self.box)

        self.SetClientSize((800, 600))
        self.mydocs = wx.StandardPaths.Get().GetDocumentsDir()
        self.mydocs = os.path.join(self.mydocs, "SimCity 4/Regions/")

        self.zoomLevel = 1
        self.zoomLevelPow = 0
        self.region = None

        self.btnZoomIn.Enable(False)
        self.btnZoomOut.Enable(False)
        self.btnSaveRgn.Enable(False)
        self.btnSave.Enable(False)
        self.overlayCbx.Enable(False)
        self.btnEditMode.Enable(False)
        self.btnExportRgn.Enable(False)
        self.Center()

    def OnCloseWindow(self, event):
        dlg = wx.MessageDialog(
            self,
            "Are you sure you want to quit ?",
            "SC4Mapper",
            wx.YES_NO | wx.YES_DEFAULT | wx.ICON_INFORMATION,
        )
        res = dlg.ShowModal()
        dlg.Destroy()
        if res == wx.ID_NO:
            return
        self.Destroy()
        sys.exit(0)

    def RevertConfig(self, event):
        self.region.all_cities = rgnReader.parse_config(self.region.original_config, 250.0)
        self.region.config = self.region.BuildConfig()
        self.editMode = EDITMODE_NONE
        self.btnSmall.SetValue(False)
        self.btnMedium.SetValue(False)
        self.btnBig.SetValue(False)
        self.btnVoid.SetValue(False)
        self.back.offX = 0
        self.back.offY = 0
        self.back.UpdateDrawing()
        self.back.Refresh(False)
        self.back.SetFocus()

    def SetEditModeSmall(self, event):
        if self.btnSmall.GetValue():
            self.editMode = EDITMODE_SMALL
            self.btnMedium.SetValue(False)
            self.btnBig.SetValue(False)
            self.btnVoid.SetValue(False)
        else:
            self.editMode = EDITMODE_NONE
            self.back.UpdateDrawing()
        self.back.SetFocus()

    def SetEditModeMedium(self, event):
        if self.btnMedium.GetValue():
            self.editMode = EDITMODE_MEDIUM
            self.btnSmall.SetValue(False)
            self.btnBig.SetValue(False)
            self.btnVoid.SetValue(False)
        else:
            self.editMode = EDITMODE_NONE
            self.back.UpdateDrawing()
        self.back.SetFocus()

    def SetEditModeBig(self, event):
        if self.btnBig.GetValue():
            self.editMode = EDITMODE_BIG
            self.btnMedium.SetValue(False)
            self.btnSmall.SetValue(False)
            self.btnVoid.SetValue(False)
        else:
            self.editMode = EDITMODE_NONE
            self.back.UpdateDrawing()
        self.back.SetFocus()

    def SetEditModeVoid(self, event):
        if self.btnVoid.GetValue():
            self.editMode = EDITMODE_VOID
            self.btnMedium.SetValue(False)
            self.btnBig.SetValue(False)
            self.btnSmall.SetValue(False)
        else:
            self.editMode = EDITMODE_NONE
            self.back.UpdateDrawing()
        self.back.SetFocus()

    def OnToggleEditMode(self, event):
        self.Freeze()
        if self.btnEditMode.GetValue():
            self.btnSmall.SetValue(False)
            self.btnMedium.SetValue(False)
            self.btnBig.SetValue(False)
            self.btnVoid.SetValue(False)

            self.btnSmall.Show()
            self.btnLoadRgn.Hide()
            self.btnMedium.Show()
            self.btnCreateRgn.Hide()
            self.btnBig.Show()
            self.btnSaveRgn.Hide()
            self.btnVoid.Show()
            self.btnExportRgn.Hide()
            self.btnRevert.Show()
            self.btnSave.Hide()
            self.overlayCbx.SetValue(True)
            self.overlayCbx.Enable(False)
            self.editMode = EDITMODE_NONE
            self.back.SetFocus()
        else:
            self.btnSmall.Hide()
            self.btnLoadRgn.Show()
            self.btnMedium.Hide()
            self.btnCreateRgn.Show()
            self.btnBig.Hide()
            self.btnSaveRgn.Show()
            self.btnVoid.Hide()
            self.btnExportRgn.Show()
            self.btnRevert.Hide()
            self.btnSave.Show()
            self.overlayCbx.Enable(True)
        self.back.OnSize(None)
        self.Layout()
        self.Refresh()
        self.Thaw()

    def OnOverlay(self, event):
        self.Freeze()
        self.back.UpdateDrawing()
        self.back.Refresh()
        self.Thaw()

    def OnZoomIn(self, event):
        if self.zoomLevelPow > 0:
            self.zoomLevelPow -= 1
            self.zoomLevel = 2**self.zoomLevelPow
            self.back.SetVirtualSize(
                (
                    self.region.imgSize[0] / self.zoomLevel,
                    self.region.imgSize[1] / self.zoomLevel,
                )
            )
        self.btnZoomIn.Enable(self.zoomLevelPow > 0)
        self.btnZoomOut.Enable(self.zoomLevelPow < 4)
        self.back.OnSize(None)
        self.back.SetFocus()

    def OnZoomOut(self, event):
        if self.zoomLevelPow < 4:
            self.zoomLevelPow += 1
            self.zoomLevel = 2**self.zoomLevelPow
            self.back.SetVirtualSize(
                (
                    self.region.imgSize[0] / self.zoomLevel,
                    self.region.imgSize[1] / self.zoomLevel,
                )
            )
        self.btnZoomIn.Enable(self.zoomLevelPow > 0)
        self.btnZoomOut.Enable(self.zoomLevelPow < 4)
        self.back.OnSize(None)
        self.back.SetFocus()

    def OnMouseMove(self, event):
        if self.btnEditMode.GetValue():
            if self.back.wait is True:
                pass
            elif self.editMode == EDITMODE_NONE:
                if event.Dragging() and self.back.crop is not None:
                    newpos = self.back.CalcUnscrolledPosition(event.GetX(), event.GetY())
                    newpos = [newpos[0] * self.zoomLevel, newpos[1] * self.zoomLevel]
                    newpos = [newpos[0] - self.back.offX, newpos[1] - self.back.offY]
                    newpos = [newpos[0] / 64, newpos[1] / 64]
                    origin = [
                        newpos[0] * 64 + self.back.offX,
                        newpos[1] * 64 + self.back.offY,
                    ]
                    size = 64 + 1
                    if (
                        origin[0] >= 0
                        and origin[1] >= 0
                        and origin[0] + size <= self.region.imgSize[0]
                        and origin[1] + size <= self.region.imgSize[1]
                    ):
                        self.back.crop = [
                            self.back.crop[0],
                            self.back.crop[1],
                            newpos[0],
                            newpos[1],
                        ]
                        logger.info(f"Crop {self.back.crop}")
                        self.back.UpdateDrawing()
                        self.back.wait = True
                        self.back.Refresh(False)

            elif self.editMode == EDITMODE_VOID:
                newpos = self.back.CalcUnscrolledPosition(event.GetX(), event.GetY())
                newpos = [newpos[0] * self.zoomLevel, newpos[1] * self.zoomLevel]
                newpos = [newpos[0] - self.back.offX, newpos[1] - self.back.offY]
                newpos = [newpos[0] / 64, newpos[1] / 64]
                self.back.HighlightCity(self.zoomLevel, self.region, newpos)
                self.back.wait = True
                self.back.Refresh(False)
            else:
                sizes = [0, 1, 2, 4]
                newpos = self.back.CalcUnscrolledPosition(event.GetX(), event.GetY())
                newpos = [newpos[0] * self.zoomLevel, newpos[1] * self.zoomLevel]
                newpos = [newpos[0] - self.back.offX, newpos[1] - self.back.offY]
                newpos = [newpos[0] / 64, newpos[1] / 64]

                origin = [
                    newpos[0] * 64 + self.back.offX,
                    newpos[1] * 64 + self.back.offY,
                ]
                size = sizes[self.editMode] * 64 + 1
                if origin[0] + size > self.region.imgSize[0]:
                    origin[0] = self.region.imgSize[0] - size
                    newpos[0] = (origin[0] - self.back.offX) / 64
                if origin[1] + size > self.region.imgSize[1]:
                    origin[1] = self.region.imgSize[1] - size
                    newpos[1] = (origin[1] - self.back.offY) / 64

                if origin[0] >= 0 and origin[1] >= 0 and origin[0] + size <= self.region.imgSize[0] and origin[1] + size <= self.region.imgSize[1]:
                    self.back.HighlightNewCity(self.zoomLevel, self.region, newpos, sizes[self.editMode])

                self.back.wait = True
                self.back.Refresh(False)

    def OnLeftDown(self, event):
        if self.btnEditMode.GetValue() and self.editMode == EDITMODE_NONE and event.ControlDown():
            newpos = self.back.CalcUnscrolledPosition(event.GetX(), event.GetY())
            newpos = [newpos[0] * self.zoomLevel, newpos[1] * self.zoomLevel]
            newpos = [newpos[0] - self.back.offX, newpos[1] - self.back.offY]
            newpos = [newpos[0] / 64, newpos[1] / 64]
            origin = [newpos[0] * 64 + self.back.offX, newpos[1] * 64 + self.back.offY]
            size = 64 + 1
            if origin[0] >= 0 and origin[1] >= 0 and origin[0] + size <= self.region.imgSize[0] and origin[1] + size <= self.region.imgSize[1]:
                self.back.crop = [newpos[0], newpos[1], newpos[0], newpos[1]]

    def OnLeftUp(self, event):
        if self.btnEditMode.GetValue():
            newpos = self.back.CalcUnscrolledPosition(event.GetX(), event.GetY())
            newpos = [newpos[0] * self.zoomLevel, newpos[1] * self.zoomLevel]
            newpos = [newpos[0] - self.back.offX, newpos[1] - self.back.offY]
            newpos = [newpos[0] / 64, newpos[1] / 64]

            if self.editMode == EDITMODE_NONE:
                if self.back.crop is not None:
                    crop = [
                        min(self.back.crop[0], self.back.crop[2]),
                        min(self.back.crop[1], self.back.crop[3]),
                        max(self.back.crop[0], self.back.crop[2]),
                        max(self.back.crop[1], self.back.crop[3]),
                    ]
                    configSize = (crop[2] - crop[0] + 1, crop[3] - crop[1] + 1)
                    config = rgnReader.BuildBestConfig(configSize)
                    self.region.config.paste(
                        "#000000",
                        (0, 0, self.region.config.size[0], self.region.config.size[1]),
                    )
                    self.region.config.paste(config, (int(crop[0]), int(crop[1])))
                    self.region.all_cities = rgnReader.parse_config(self.region.config, self.region.waterLevel)
                    self.region.config = self.region.BuildConfig()
                self.back.crop = None
            elif self.editMode == EDITMODE_VOID:
                self.region.DeleteCityAt(newpos)
            else:
                sizes = [0, 1, 2, 4]
                origin = [
                    newpos[0] * 64 + self.back.offX,
                    newpos[1] * 64 + self.back.offY,
                ]
                size = sizes[self.editMode] * 64 + 1
                if origin[0] + size > self.region.imgSize[0]:
                    origin[0] = self.region.imgSize[0] - size
                    newpos[0] = (origin[0] - self.back.offX) / 64
                if origin[1] + size > self.region.imgSize[1]:
                    origin[1] = self.region.imgSize[1] - size
                    newpos[1] = (origin[1] - self.back.offY) / 64

                if origin[0] >= 0 and origin[1] >= 0 and origin[0] + size <= self.region.imgSize[0] and origin[1] + size <= self.region.imgSize[1]:
                    currentSize = sizes[self.editMode]
                    done = False
                    logger.info("start split")
                    while not done:
                        done = True
                        cities = self.region.GetCitiesUnder(newpos, currentSize)
                        for city in cities:
                            if city.city_x_size == 1:
                                self.region.all_cities.remove(city)
                            else:
                                done = False
                                newCities = city.split()
                                self.region.all_cities.remove(city)
                                for c in newCities:
                                    self.region.all_cities.append(c)
                    logger.info("end split")
                    self.region.all_cities.append(rgnReader.CityProxy(250.0, newpos[0], newpos[1], currentSize, currentSize))
            logger.info("start build")
            self.region.config = self.region.BuildConfig()
            logger.info("end build")
            self.back.UpdateDrawing()
            self.back.wait = True
            self.back.Refresh(False)
