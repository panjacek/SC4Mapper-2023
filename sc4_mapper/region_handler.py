import logging
import os
import struct
import zlib

import numpy as Numeric
import tools3D
import wx
from PIL import Image, ImageDraw

from sc4_mapper import (
    MAPPER_VERSION,
    QuestionDialog,
    base_dir,
    rgnReader,
)
from sc4_mapper.helpers import cached_listdir
from sc4_mapper.region_from_file import (
    CreateRgnFromFile,
    SC4MfileHandler,
    SC4MfileHandlerGrey,
    SC4MfileHandlerPNG,
    SC4MfileHandlerRGB,
)

logger = logging.getLogger(__name__)


class RegionHandler:
    def __init__(self, frame):
        self.frame = frame

    def SaveBmp(self, event):
        dlg = wx.FileDialog(
            self.frame,
            message="Save file as ...",
            defaultDir=os.getcwd(),
            defaultFile="",
            wildcard="PNG file (*.png)|*.png|Jpeg file (*.jpg)|*.jpg|Bitmap file (*.bmp)|*.bmp",
            style=wx.FD_SAVE,
        )
        if dlg.ShowModal() == wx.ID_OK:
            wx.BeginBusyCursor()
            path = dlg.GetPath()

            lightDir = rgnReader.normalize((1, -5, -1))
            s = (self.frame.region.height.shape[1], self.frame.region.height.shape[0])
            xO = yO = 0
            colours = [0, "#FF0000", "#00FF00", 0, "#0000FF"]
            sizes = [0, 64, 128, 0, 256]

            dlgProg = wx.ProgressDialog(
                "Saving overview",
                "Please wait while saving overview",
                maximum=len(self.frame.region.all_cities) + len(self.frame.region.missingCities) + 10,
                parent=self.frame,
                style=0,
            )

            im = Image.new("RGB", (self.frame.region.imgSize[0], self.frame.region.imgSize[1]))
            for i, city in enumerate(self.frame.region.all_cities):
                dlgProg.Update(i, "Please wait while saving overview")
                x = int(city.xPos)
                y = int(city.yPos)
                width = sizes[city.city_x_size] + 1
                height = sizes[city.city_y_size] + 1
                x1 = x - xO + self.frame.back.offX
                y1 = y - yO + self.frame.back.offY
                x2 = x1 + width
                y2 = y1 + height

                h = Numeric.zeros((height, width), Numeric.uint16)
                h[:, :] = Numeric.reshape(self.frame.region.height[y1:y2, x1:x2], (height, width))
                h = h.astype(Numeric.float32)
                h /= Numeric.array(10).astype(Numeric.float32)
                rawRGB = tools3D.onePassColors(
                    False,
                    (height, width),
                    self.frame.region.waterLevel,
                    h,
                    rgnReader.GRADIENT_READER.paletteWater,
                    rgnReader.GRADIENT_READER.paletteLand,
                    lightDir,
                )
                del h
                imCity = Image.frombytes("RGB", (width, height), rawRGB)
                del rawRGB
                im.paste(imCity, (x1, y1))
                del imCity

            if self.frame.overlayCbx.GetValue():
                draw = ImageDraw.Draw(im)

                def DrawHided(x, y, width, height):
                    x1 = x
                    y1 = y
                    x2 = x1 + width
                    y2 = y1 + height
                    h = Numeric.zeros((height, width), Numeric.uint16)
                    h[:, :] = Numeric.reshape(self.frame.region.height[y1:y2, x1:x2], (height, width))
                    h = h.astype(Numeric.float32)
                    h /= Numeric.array(10).astype(Numeric.float32)
                    rawRGB = tools3D.onePassColors(
                        False,
                        (height, width),
                        self.frame.region.waterLevel,
                        h,
                        rgnReader.GRADIENT_READER.paletteWater,
                        rgnReader.GRADIENT_READER.paletteLand,
                        lightDir,
                    )
                    del h
                    imCity = Image.frombytes("RGB", (width, height), rawRGB).convert("L").convert("RGB")
                    del rawRGB
                    im.paste(imCity, (x1, y1))
                    del imCity

                # Refactored to avoid i index issues
                current_i = len(self.frame.region.all_cities)
                if self.frame.back.offX > 0:
                    current_i += 1
                    dlgProg.Update(current_i, "Please wait while saving overview")
                    DrawHided(0, 0, self.frame.back.offX, self.frame.region.imgSize[1])

                if self.frame.back.offY > 0:
                    current_i += 1
                    dlgProg.Update(current_i, "Please wait while saving overview")
                    # Note: Original code had self.back.imgSize[0], but OverViewCanvas has no imgSize.
                    # Using region.imgSize[0] instead.
                    DrawHided(0, 0, self.frame.region.imgSize[0], self.frame.back.offY)

                if self.frame.back.offX < 0:
                    current_i += 1
                    dlgProg.Update(current_i, "Please wait while saving overview")
                    DrawHided(
                        self.frame.region.imgSize[0] + self.frame.back.offX,
                        0,
                        -self.frame.back.offX,
                        self.frame.region.imgSize[1],
                    )

                if self.frame.back.offY < 0:
                    current_i += 1
                    dlgProg.Update(current_i, "Please wait while saving overview")
                    DrawHided(
                        0,
                        self.frame.region.imgSize[1] + self.frame.back.offY,
                        self.frame.region.imgSize[0],
                        -self.frame.back.offY,
                    )

                lines = []
                for y in range(int(s[1] / 64)):
                    lines.append(
                        [
                            0 - xO,
                            y * 64 - yO,
                            self.frame.region.original_config.size[0] * 64 - xO,
                            y * 64 - yO,
                        ]
                    )
                for x in range(int(s[0] / 64)):
                    lines.append(
                        [
                            x * 64 - xO,
                            0 - yO,
                            x * 64 - xO,
                            self.frame.region.original_config.size[1] * 64 - yO,
                        ]
                    )
                for x1, y1, x2, y2 in lines:
                    draw.line(
                        [
                            x1 + self.frame.back.offX,
                            y1 + self.frame.back.offY,
                            x2 + self.frame.back.offX,
                            y2 + self.frame.back.offY,
                        ],
                        fill="#222222",
                    )

                for city in self.frame.region.all_cities:
                    x = int(city.xPos)
                    y = int(city.yPos)
                    width = sizes[city.city_x_size]
                    height = sizes[city.city_y_size]
                    draw.rectangle(
                        [
                            x - xO + 1 + self.frame.back.offX,
                            y - yO + 1 + self.frame.back.offY,
                            x - xO + width - 1 + self.frame.back.offX,
                            y - yO + height - 1 + self.frame.back.offY,
                        ],
                        outline=colours[city.city_x_size],
                    )
                for x, y in self.frame.region.missingCities:
                    current_i += 1
                    dlgProg.Update(current_i, "Please wait while saving overview")

                    width = 65
                    height = 65
                    x = int(x * 64)
                    y = int(y * 64)
                    x1 = x - xO + self.frame.back.offX
                    y1 = y - yO + self.frame.back.offY
                    x2 = x - xO + width + self.frame.back.offX
                    y2 = y - yO + height + self.frame.back.offY
                    x1 = max(0, min(x1, self.frame.region.imgSize[0]))
                    y1 = max(0, min(y1, self.frame.region.imgSize[1]))
                    x2 = max(0, min(x2, self.frame.region.imgSize[0]))
                    y2 = max(0, min(y2, self.frame.region.imgSize[1]))

                    width = x2 - x1
                    height = y2 - y1
                    if width <= 0 or height <= 0:
                        continue
                    h = Numeric.zeros((height, width), Numeric.uint16)
                    h[:, :] = Numeric.reshape(self.frame.region.height[y1:y2, x1:x2], (height, width))
                    h = h.astype(Numeric.float32)
                    h /= Numeric.array(10).astype(Numeric.float32)
                    rawRGB = tools3D.onePassColors(
                        False,
                        (height, width),
                        self.frame.region.waterLevel,
                        h,
                        rgnReader.GRADIENT_READER.paletteWater,
                        rgnReader.GRADIENT_READER.paletteLand,
                        lightDir,
                    )
                    imCity = Image.frombytes("RGB", (width, height), rawRGB).convert("L").convert("RGB")
                    del rawRGB
                    im.paste(imCity, (x1, y1))
                    del imCity

            im.save(path)
            dlgProg.Close()
            dlgProg.Destroy()
            wx.EndBusyCursor()

    def CreateRgn(self, event):
        result = QuestionDialog.questionDialog(
            "Do you want to create a region from ?",
            buttons=[
                "SC4M",
                "Grayscale image",
                "16 bit png",
                "RGB image",
                wx.ID_CANCEL,
            ],
        )
        if result == wx.ID_CANCEL or result is None:
            return
        self.frame.btnEditMode.Enable(False)
        if result == "SC4M":
            self.CreateRgnFromSC4M()
        if result == "Grayscale image":
            self.CreateRgnFromGrey()
        if result == "16 bit png":
            self.CreateRgnFromPNG()
        if result == "RGB image":
            self.CreateRgnFromRGB()

    def CreateRgnInit(self):
        self.frame.btnSave.Enable(False)
        self.frame.btnExportRgn.Enable(False)
        self.frame.btnSaveRgn.Enable(False)
        self.frame.region = None

        self.frame.back.SetVirtualSize((100, 100))
        self.frame.zoomLevel = 1
        self.frame.zoomLevelPow = 0

        self.frame.SetTitle(f"NHP SC4Mapper {MAPPER_VERSION} Version ")

    def CreateRgnOk(self, regionName):
        self.frame.btnSave.Enable(True)
        self.frame.btnSaveRgn.Enable(True)
        self.frame.btnExportRgn.Enable(True)
        self.frame.SetTitle(f"NHP SC4Mapper {MAPPER_VERSION} Version - {regionName}")
        self.frame.btnZoomIn.Enable(False)
        self.frame.btnZoomOut.Enable(True)

    def CreateRgnFromSC4M(self):
        dlg = wx.FileDialog(
            self.frame,
            message="Choose a file",
            defaultDir=os.getcwd(),
            defaultFile="",
            wildcard="SC4M file (*.sc4m;*.SC4M)|*.sc4m;*.SC4M",
            style=wx.FD_OPEN,
        )
        if dlg.ShowModal() == wx.ID_OK:
            self.CreateRgnInit()
            path = dlg.GetPath()
            self.frame.regionName = os.path.splitext(os.path.basename(path))[0]
            handler = SC4MfileHandler(path)
            self.frame.region = CreateRgnFromFile(handler, self.frame)
            if self.frame.region is not None:
                self.frame.back.SetVirtualSize(
                    (
                        self.frame.region.imgSize[0],
                        self.frame.region.imgSize[1],
                    )
                )
                self.frame.back.UpdateDrawing()
                self.CreateRgnOk(self.frame.regionName)
                self.frame.btnEditMode.Enable(True)
        dlg.Destroy()

    def CreateRgnFromGrey(self):
        dlg = wx.FileDialog(
            self.frame,
            message="Choose a file",
            defaultDir=os.getcwd(),
            defaultFile="",
            wildcard="Image file (*.png,*.jpg,*.bmp)|*.png;*.jpg;*.bmp",
            style=wx.FD_OPEN,
        )
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()

            self.CreateRgnInit()
            self.frame.regionName = os.path.splitext(os.path.basename(path))[0]
            handler = SC4MfileHandlerGrey(path)
            self.frame.region = CreateRgnFromFile(handler, self.frame)
            if self.frame.region is not None:
                self.frame.back.SetVirtualSize(
                    (
                        self.frame.region.imgSize[0],
                        self.frame.region.imgSize[1],
                    )
                )
                self.frame.back.UpdateDrawing()
                self.CreateRgnOk(self.frame.regionName)
                self.frame.btnEditMode.Enable(True)
        dlg.Destroy()

    def CreateRgnFromPNG(self):
        dlg = wx.FileDialog(
            self.frame,
            message="Choose a file",
            defaultDir=os.getcwd(),
            defaultFile="",
            wildcard="PNG file (*.png)|*.png",
            style=wx.FD_OPEN,
        )
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()

            self.CreateRgnInit()
            self.frame.regionName = os.path.splitext(os.path.basename(path))[0]
            handler = SC4MfileHandlerPNG(path)
            self.frame.region = CreateRgnFromFile(handler, self.frame)
            if self.frame.region is not None:
                self.frame.back.SetVirtualSize(
                    (
                        self.frame.region.imgSize[0],
                        self.frame.region.imgSize[1],
                    )
                )
                self.frame.back.UpdateDrawing()
                self.CreateRgnOk(self.frame.regionName)
                self.frame.btnEditMode.Enable(True)
        dlg.Destroy()

    def CreateRgnFromRGB(self):
        dlg = wx.FileDialog(
            self.frame,
            message="Choose a file",
            defaultDir=os.getcwd(),
            defaultFile="",
            wildcard="Image file (*.png,*.jpg,*.bmp)|*.png;*.jpg;*.bmp",
            style=wx.FD_OPEN,
        )
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()

            self.CreateRgnInit()
            self.frame.regionName = os.path.splitext(os.path.basename(path))[0]
            handler = SC4MfileHandlerRGB(path)
            self.frame.region = CreateRgnFromFile(handler, self.frame)
            if self.frame.region is not None:
                self.frame.back.SetVirtualSize(
                    (
                        self.frame.region.imgSize[0],
                        self.frame.region.imgSize[1],
                    )
                )
                self.frame.back.UpdateDrawing()
                self.CreateRgnOk(self.frame.regionName)
                self.frame.btnEditMode.Enable(True)
        dlg.Destroy()

    def ExportAsRGB(self, path, config, minX, minY, subRgn):
        if os.path.isfile(path):
            dlg = wx.MessageDialog(
                self.frame,
                path + " already exist\nOverwrite it ?",
                "SC4Mapper",
                wx.YES_NO | wx.YES_DEFAULT | wx.ICON_INFORMATION,
            )
            ret = dlg.ShowModal()
            dlg.Destroy()
            if ret == wx.NO:
                return

        wx.BeginBusyCursor()
        im = Image.new("RGB", (config.size[0] * 64 + 1, config.size[1] * 64 + 1))
        dlgProg = wx.ProgressDialog(
            "Exporting as RGB",
            "Please wait while exporting the region",
            maximum=len(self.frame.region.all_cities),
            parent=self.frame,
            style=0,
        )
        for i, city in enumerate(self.frame.region.all_cities):
            dlgProg.Update(i, "Please wait while exporting the region")
            citySave = rgnReader.CityProxy(
                self.frame.region.waterLevel,
                city.city_x_position - minX,
                city.city_y_position - minY,
                city.city_x_size,
                city.city_y_size,
            )
            heightMap = Numeric.zeros((citySave.ySize, citySave.xSize), Numeric.uint16)
            heightMap[::, ::] = self.frame.region.height[
                citySave.yPos + subRgn[1] : citySave.yPos + subRgn[1] + citySave.ySize,
                citySave.xPos + subRgn[0] : citySave.xPos + subRgn[0] + citySave.xSize,
            ]
            red = ((heightMap / Numeric.array(4096, Numeric.uint16)) % Numeric.array(16, Numeric.uint16)) * Numeric.array(16, Numeric.uint16)
            red = red.astype(Numeric.uint8)
            imRed = Image.frombytes("L", (heightMap.shape[1], heightMap.shape[0]), red.tobytes())
            green = ((heightMap / Numeric.array(256, Numeric.uint16)) % Numeric.array(16, Numeric.uint16)) * Numeric.array(16, Numeric.uint16)
            green = green.astype(Numeric.uint8)
            imGreen = Image.frombytes("L", (heightMap.shape[1], heightMap.shape[0]), green.tobytes())
            blue = heightMap % Numeric.array(256, Numeric.uint16)
            blue = blue.astype(Numeric.uint8)
            imBlue = Image.frombytes("L", (heightMap.shape[1], heightMap.shape[0]), blue.tobytes())
            imCity = Image.merge("RGB", (imRed, imGreen, imBlue))
            im.paste(imCity, (citySave.xPos, citySave.yPos))
        dlgProg.Close()
        dlgProg.Destroy()
        self.frame.Refresh()
        wx.Yield()

        try:
            im.save(path)
            pathCfg = os.path.splitext(path)[0]
            pathCfg += "-config.bmp"
            config.save(pathCfg)
        except Exception as save_fail:
            logger.exception(save_fail)
            wx.EndBusyCursor()
            dlg1 = wx.MessageDialog(
                self.frame,
                path + " can't be saved",
                "Export error",
                wx.OK | wx.ICON_ERROR,
            )
            dlg1.ShowModal()
            dlg1.Destroy()
            return
        wx.EndBusyCursor()
        wx.CallAfter(self.ShowSuccess, path)

    def ExportAsPNG(self, path, config, minX, minY, subRgn):
        if os.path.isfile(path):
            dlg = wx.MessageDialog(
                self.frame,
                path + " already exist\nOverwrite it?",
                "SC4Mapper",
                wx.YES_NO | wx.YES_DEFAULT | wx.ICON_INFORMATION,
            )
            ret = dlg.ShowModal()
            dlg.Destroy()
            if ret == wx.NO:
                return
        wx.BeginBusyCursor()

        im = Image.new("I", (config.size[0] * 64 + 1, config.size[1] * 64 + 1))
        dlgProg = wx.ProgressDialog(
            "Exporting as PNG",
            "Please wait while exporting the region",
            maximum=len(self.frame.region.all_cities),
            parent=self.frame,
            style=0,
        )
        for i, city in enumerate(self.frame.region.all_cities):
            dlgProg.Update(i, "Please wait while exporting the region")
            citySave = rgnReader.CityProxy(
                self.frame.region.waterLevel,
                city.city_x_position - minX,
                city.city_y_position - minY,
                city.city_x_size,
                city.city_y_size,
            )
            heightMap = Numeric.zeros((citySave.ySize, citySave.xSize), Numeric.uint16)
            heightMap[::, ::] = self.frame.region.height[
                citySave.yPos + subRgn[1] : citySave.yPos + subRgn[1] + citySave.ySize,
                citySave.xPos + subRgn[0] : citySave.xPos + subRgn[0] + citySave.xSize,
            ]
            heightMap = heightMap.astype(Numeric.int32)
            imCity = Image.frombytes("I", (heightMap.shape[1], heightMap.shape[0]), heightMap.tobytes())
            im.paste(imCity, (citySave.xPos, citySave.yPos))
        dlgProg.Close()
        dlgProg.Destroy()
        self.frame.Refresh()
        wx.Yield()
        try:
            im.save(path)
            pathCfg = os.path.splitext(path)[0]
            pathCfg += "-config.bmp"
            config.save(pathCfg)
        except Exception as save_fail:
            logger.exception(save_fail)
            wx.EndBusyCursor()
            dlg1 = wx.MessageDialog(
                self.frame,
                path + " can't be saved",
                "Export error",
                wx.OK | wx.ICON_ERROR,
            )
            dlg1.ShowModal()
            dlg1.Destroy()
            return
        del im
        wx.EndBusyCursor()
        wx.CallAfter(self.ShowSuccess, path)

    def ShowSuccess(self, path):
        dlg1 = wx.MessageDialog(
            self.frame,
            path + " as been exported",
            "Export done",
            wx.OK | wx.ICON_INFORMATION,
        )
        dlg1.ShowModal()
        dlg1.Destroy()

    def ExportAsSC4M(self, path, config, minX, minY, subRgn):
        if os.path.isfile(path):
            dlg = wx.MessageDialog(
                self.frame,
                path + " already exist\nOverwrite it ?",
                "SC4Mapper",
                wx.YES_NO | wx.YES_DEFAULT | wx.ICON_INFORMATION,
            )
            ret = dlg.ShowModal()
            dlg.Destroy()
            if ret == wx.NO:
                return

        dlg1 = wx.FileDialog(
            self.frame,
            message="Enter a valid hml file that will be displayed on import",
            defaultDir=base_dir,
            defaultFile="",
            wildcard="HTML files (*.HTML)|*.html",
            style=wx.FD_OPEN,
        )
        if dlg1.ShowModal() == wx.ID_OK:
            htmlFileName = dlg1.GetPaths()[0]
        else:
            htmlFileName = None
        dlg1.Destroy()

        wx.BeginBusyCursor()

        dlgProg = wx.ProgressDialog(
            "Exporting as SC4M",
            "Please wait while exporting the region",
            maximum=len(self.frame.region.all_cities),
            parent=self.frame,
            style=0,
        )
        im1 = Image.new("L", (config.size[0] * 64 + 1, config.size[1] * 64 + 1))
        im2 = Image.new("L", (config.size[0] * 64 + 1, config.size[1] * 64 + 1))
        for i, city in enumerate(self.frame.region.all_cities):
            dlgProg.Update(i, "Please wait while exporting the region")
            citySave = rgnReader.CityProxy(
                self.frame.region.waterLevel,
                city.city_x_position - minX,
                city.city_y_position - minY,
                city.city_x_size,
                city.city_y_size,
            )
            heightMap = Numeric.zeros((citySave.ySize, citySave.xSize), Numeric.uint16)
            heightMap[::, ::] = self.frame.region.height[
                citySave.yPos + subRgn[1] : citySave.yPos + subRgn[1] + citySave.ySize,
                citySave.xPos + subRgn[0] : citySave.xPos + subRgn[0] + citySave.xSize,
            ]
            heightMap = heightMap.astype(Numeric.int32)
            imCity = Image.frombytes("RGBA", (heightMap.shape[1], heightMap.shape[0]), heightMap.tobytes())
            imCity1, imCity2 = imCity.split()[:2]
            im1.paste(imCity1, (citySave.xPos, citySave.yPos))
            im2.paste(imCity2, (citySave.xPos, citySave.yPos))
        dlgProg.Close()
        dlgProg.Destroy()
        self.frame.Refresh()
        wx.Yield()

        s = b"SC4M"
        s += struct.pack("L", 0x0200)
        s += struct.pack("L", im1.size[1])
        s += struct.pack("L", im1.size[0])
        s += struct.pack("f", 0)
        if htmlFileName is not None and os.path.isfile(htmlFileName):
            s += b"SC4N"  # author notes
            with open(htmlFileName, "rb") as filehtml:
                line = filehtml.read()
            s += struct.pack("L", len(line))
            s += line
        s += b"SC4C"  # config.bmp included
        s += struct.pack("L", config.size[0])
        s += struct.pack("L", config.size[1])
        configStr = config.tobytes()
        s += struct.pack("L", len(configStr))
        s += configStr
        s += b"SC4D"  # elevation data
        try:
            encoder = zlib.compressobj(9)
            with open(path, "wb") as raw:
                raw.write(encoder.compress(s))
                raw.write(encoder.compress(im1.tobytes()))
                del im1
                raw.write(encoder.compress(im2.tobytes()))
                del im2
                raw.write(encoder.flush())
            pathCfg = os.path.splitext(path)[0]
            pathCfg += "-config.bmp"
            config.save(pathCfg)
        except Exception as compress_err:
            logger.exception(compress_err)
            wx.EndBusyCursor()
            raise
        wx.EndBusyCursor()
        wx.CallAfter(self.ShowSuccess, path)

    def ExportRgn(self, event):
        dlg = wx.FileDialog(
            self.frame,
            message="Export region as ...",
            defaultDir=base_dir,
            defaultFile=self.frame.regionName,
            wildcard="SC4 Terrain files (*.SC4M;*.sc4m)|*.SC4M;*.sc4m|16bit png files (*.png)|*.png|RGB files (*.bmp)|*.bmp",
            style=wx.FD_SAVE,
        )
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            dlg.Destroy()
            ext = os.path.splitext(path)[1].upper()
            minX, minY, maxX, maxY, sizeX, sizeY, config = self.frame.region.crop_config()
            subRgn = [
                minX * 64 + self.frame.back.offX,
                minY * 64 + self.frame.back.offY,
                maxX * 64 + 1 + self.frame.back.offX,
                maxY * 64 + 1 + self.frame.back.offY,
            ]

            if ext == ".SC4M":
                self.ExportAsSC4M(path, config, minX, minY, subRgn)
            if ext == ".BMP":
                self.ExportAsRGB(path, config, minX, minY, subRgn)
            if ext == ".PNG":
                self.ExportAsPNG(path, config, minX, minY, subRgn)

        else:
            dlg.Destroy()
        self.frame.Refresh(False)

    def SaveRgn(self, event):
        dlg = wx.DirDialog(
            self.frame,
            "Choose or create a directory for the region:",
            defaultPath=self.frame.mydocs,
            style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON,
        )
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            name = os.path.basename(path)
            dlg.Destroy()
        else:
            dlg.Destroy()
            return None

        try:
            os.makedirs(path)
        except OSError as error:
            # error[0] might be errno.EEXIST (17)
            if error.errno == 17:
                dlg = wx.MessageDialog(
                    self.frame,
                    (
                        "A region with this name already exists or at least the region folder already exists\n"
                        "Do you want to save anyway (removing previous region)?"
                    ),
                    "Warning",
                    wx.YES_NO | wx.NO_DEFAULT | wx.ICON_INFORMATION,
                )
                ret = dlg.ShowModal()
                dlg.Destroy()
                if ret == wx.ID_NO:
                    return
                try:
                    allfiles = cached_listdir(path)
                    valid = [".SC4", ".INI", ".BMP", ".PNG"]
                    allfiles = [f for f in allfiles if os.path.splitext(f)[1].upper() in valid]
                    for fname in allfiles:
                        os.unlink(os.path.join(path, fname))
                except OSError:
                    dlg = wx.MessageDialog(
                        self.frame,
                        ("A problem has occured while cleaning the region folder\nYou may try to clean it yourself"),
                        "Error while saving region",
                        wx.OK | wx.ICON_ERROR,
                    )
                    dlg.ShowModal()
                    dlg.Destroy()
                    return
            else:
                dlg = wx.MessageDialog(
                    self.frame,
                    ("A problem has occured while creating the region folder\nYou should enter a valid folder name as region name"),
                    "Error while saving region",
                    wx.OK | wx.ICON_ERROR,
                )
                dlg.ShowModal()
                dlg.Destroy()
                return

        wx.BeginBusyCursor()
        self.frame.region.folder = path
        dlg1 = wx.ProgressDialog(
            "Saving region",
            "Please wait while saving the region",
            maximum=len(self.frame.region.all_cities),
            parent=self.frame,
            style=0,
        )
        minX, minY, maxX, maxY, sizeX, sizeY, config = self.frame.region.crop_config()
        subRgn = [
            minX * 64 + self.frame.back.offX,
            minY * 64 + self.frame.back.offY,
            maxX * 64 + 1 + self.frame.back.offX,
            maxY * 64 + 1 + self.frame.back.offY,
        ]
        config.save(os.path.join(path, "config.bmp"))
        try:
            saved = self.frame.region.Save(dlg1, minX, minY, subRgn)
        except Exception as save_exc:
            logger.warning(save_exc)
            saved = False
        wx.EndBusyCursor()
        dlg1.Close()
        dlg1.Destroy()
        if saved is False:
            dlg = wx.MessageDialog(
                self.frame,
                ("A problem has occured while saving the cities files\nSome or all of the cities might not have been saved correctly"),
                "Error while saving region",
                wx.OK | wx.ICON_ERROR,
            )
            dlg.ShowModal()
            dlg.Destroy()
            return
        self.frame.regionName = name
        self.frame.SetTitle(f"NHP SC4Mapper {MAPPER_VERSION} Version - {name}")

    def OpenRgn(self, event):
        self.frame.btnEditMode.Enable(False)
        try:
            r = self.LoadARegion()
        except:
            raise

        if r is None:
            return

        self.frame.btnEditMode.Enable(False)
        self.frame.btnSave.Enable(True)
        self.frame.btnExportRgn.Enable(True)
        self.frame.btnSaveRgn.Enable(True)
        self.frame.btnZoomIn.Enable(False)
        self.frame.btnZoomOut.Enable(True)
        self.frame.overlayCbx.Enable(True)
        self.frame.back.offX = 0
        self.frame.back.offY = 0

        self.frame.region = r
        self.frame.zoomLevel = 1
        self.frame.zoomLevelPow = 0
        self.frame.btnEditMode.Enable(True)
        self.frame.back.SetVirtualSize((self.frame.region.height.shape[1], self.frame.region.height.shape[0]))

        self.frame.SetFocus()
        self.frame.SetTitle(f"NHP SC4Mapper {MAPPER_VERSION} Version - {self.frame.regionName}")
        self.frame.Layout()
        self.frame.Refresh()
        self.frame.Update()

        # Give wx time to process layout events
        wx.SafeYield()

        logger.info(f"Frame ClientSize: {self.frame.GetClientSize()}")
        logger.info(f"Canvas (back) Size: {self.frame.back.GetSize()}")
        logger.info(f"Canvas (back) ClientSize: {self.frame.back.GetClientSize()}")

        # Force a reasonable size if it looks broken (1,1 is commonly a 'not sized yet' placeholder)
        if self.frame.back.GetClientSize() == (1, 1):
            logger.warning("Canvas size is (1,1), attempting to force resize based on Frame size")
            # Estimate toolbar height ~100px? Just a heuristic fallback
            w, h = self.frame.GetClientSize()
            self.frame.back.SetSize((w, h - 50))
            wx.SafeYield()
            logger.info(f"Canvas (back) ClientSize after force: {self.frame.back.GetClientSize()}")

        self.frame.back.OnSize(None)

    def LoadARegion(self):
        # In this case we include a "New directory" button.
        dlg = wx.DirDialog(
            self.frame,
            "Choose a directory:",
            defaultPath=self.frame.mydocs,
            style=wx.DEFAULT_DIALOG_STYLE | wx.DD_DIR_MUST_EXIST,
        )
        if dlg.ShowModal() == wx.ID_OK:
            regionPath = dlg.GetPath()
        else:
            dlg.Destroy()
            return None

        if not os.path.isdir(regionPath):
            regionPath = os.path.split(regionPath)[0]
        logger.debug(regionPath)

        dlg.Destroy()
        waterLevel = 250

        wx.BeginBusyCursor()
        dlg = wx.ProgressDialog(
            "Loading region",
            "Please wait while loading the region",
            maximum=6,
            parent=self.frame,
            style=0,
        )

        try:
            dlg.Update(0)
            NewRegion = rgnReader.SC4Region(regionPath, waterLevel, dlg)
            if NewRegion.all_cities is None:
                wx.EndBusyCursor()
                dlg.Close()
                dlg.Destroy()
                dlg = wx.MessageDialog(
                    self.frame,
                    "No cities found",
                    "Error while loading region",
                    wx.OK | wx.ICON_ERROR,
                )
                dlg.ShowModal()
                dlg.Destroy()
                return None
            NewRegion.show(dlg, True)
            dlg.Close()
            dlg.Destroy()

            if not NewRegion.is_valid():
                wx.EndBusyCursor()
                dlg = wx.MessageDialog(
                    self.frame,
                    "This folder seems not to be a valid region",
                    "Error while loading region",
                    wx.OK | wx.ICON_ERROR,
                )
                dlg.ShowModal()
                dlg.Destroy()
                return None

            if NewRegion.is_valid() and NewRegion.config is None:
                wx.EndBusyCursor()
                dlg = wx.MessageDialog(
                    self.frame,
                    "There isn't any config.bmp",
                    "Warning while loading region",
                    wx.OK | wx.ICON_INFORMATION,
                )
                dlg.ShowModal()
                dlg.Destroy()
            wx.EndBusyCursor()
            self.frame.regionName = os.path.splitext(os.path.split(regionPath)[1])[0]
            return NewRegion
        except:
            wx.EndBusyCursor()
            dlg.Destroy()
            raise
