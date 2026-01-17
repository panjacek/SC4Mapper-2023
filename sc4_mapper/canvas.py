import logging
import numpy as Numeric
import tools3D
import wx
from sc4_mapper import SCROLL_RATE, EDITMODE_NONE, rgnReader

logger = logging.getLogger(__name__)


class OverViewCanvas(wx.ScrolledWindow):
    def __init__(self, parent, id=-1, size=wx.DefaultSize):
        wx.ScrolledWindow.__init__(
            self,
            parent,
            id,
            (0, 0),
            size=size,
            style=wx.SUNKEN_BORDER | wx.FULL_REPAINT_ON_RESIZE,
        )
        self.parent = parent
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_SCROLLWIN, self.OnScroll)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_CHAR, self.OnKeyDown)
        self.bmp = None
        self.drag = False
        self.buffer = None
        self.wait = False
        self.crop = None
        self.offX = 0
        self.offY = 0
        self.OnSize(None)

    def OnKeyDown(self, event):
        if self.parent.btnEditMode.GetValue() and self.parent.editMode == EDITMODE_NONE:
            if self.wait is True:
                return
            if event.GetModifiers() != wx.MOD_CONTROL:
                return
            if event.GetKeyCode() == wx.WXK_LEFT:
                for _ in range(self.parent.zoomLevel):
                    offX = self.offX - 1
                    deletes = []
                    for city in self.parent.region.all_cities:
                        if city.xPos + offX < 0:
                            deletes.append((city.city_x_position, city.city_y_position))
                    if len(deletes) == 0:
                        self.offX = offX
                self.UpdateDrawing()
                self.wait = True
                self.Refresh(False)
            if event.GetKeyCode() == wx.WXK_RIGHT:
                for _ in range(self.parent.zoomLevel):
                    offX = self.offX + 1
                    deletes = []
                    for city in self.parent.region.all_cities:
                        if (
                            city.xPos + city.xSize + offX
                            > self.parent.region.imgSize[0]
                        ):
                            deletes.append((city.city_x_position, city.city_y_position))
                    if len(deletes) == 0:
                        self.offX = offX
                self.UpdateDrawing()
                self.wait = True
                self.Refresh(False)
            if event.GetKeyCode() == wx.WXK_UP:
                for _ in range(self.parent.zoomLevel):
                    offY = self.offY - 1
                    deletes = []
                    for city in self.parent.region.all_cities:
                        if city.yPos + offY < 0:
                            deletes.append((city.city_x_position, city.city_y_position))
                    if len(deletes) == 0:
                        self.offY = offY
                self.UpdateDrawing()
                self.wait = True
                self.Refresh(False)
            if event.GetKeyCode() == wx.WXK_DOWN:
                for _ in range(self.parent.zoomLevel):
                    offY = self.offY + 1
                    deletes = []
                    for city in self.parent.region.all_cities:
                        if (
                            city.yPos + city.ySize + offY
                            > self.parent.region.imgSize[1]
                        ):
                            deletes.append((city.city_x_position, city.city_y_position))
                    if len(deletes) == 0:
                        self.offY = offY
                self.UpdateDrawing()
                self.wait = True
                self.Refresh(False)

    def OnEraseBackground(self, event):
        pass

    def OnSize(self, event):
        size = self.ClientSize
        if event:
            size = event.GetSize()
        if self.parent.region:
            if self.buffer is None or (
                self.buffer.GetWidth() != size[0] or self.buffer.GetHeight() != size[1]
            ):
                self.buffer = wx.Bitmap(*size)
            self.UpdateDrawing(newSize=size)
        else:
            self.buffer = None
        if event:
            event.Skip()

    def OnScroll(self, event):
        size = self.ClientSize
        x, y = self.GetViewStart()
        if self.parent.region:
            if self.buffer is None or (
                self.buffer.GetWidth() != size[0] or self.buffer.GetHeight() != size[1]
            ):
                self.buffer = wx.EmptyBitmap(*size)
            wx.CallAfter(self.UpdateDrawing)
        else:
            self.buffer = None
        event.Skip()

    def UpdateDrawing(self, pos=None, newSize=None, finish=True):
        lightDir = rgnReader.normalize((1, -5, -1))
        size = self.ClientSize
        if newSize:
            size = newSize

        if self.parent.zoomLevel == 1:
            sizeDest = (
                min(size[0], self.parent.region.height.shape[1]),
                min(size[1], self.parent.region.height.shape[0]),
            )
            sizeSource = sizeDest
        else:
            sizeDest = (
                min(
                    size[0], self.parent.region.height.shape[1] / self.parent.zoomLevel
                ),
                min(
                    size[1], self.parent.region.height.shape[0] / self.parent.zoomLevel
                ),
            )
            sizeSource = (
                sizeDest[0] * self.parent.zoomLevel,
                sizeDest[1] * self.parent.zoomLevel,
            )
        logger.info(f"{sizeDest} {sizeSource}")
        if pos:
            x, y = pos
        else:
            x, y = self.GetViewStart()
        x *= SCROLL_RATE
        y *= SCROLL_RATE
        x *= self.parent.zoomLevel
        y *= self.parent.zoomLevel
        logger.debug(f"Drawing from {x}, {y}")
        heightMap = Numeric.zeros((sizeDest[1], sizeDest[0]), Numeric.uint16)
        try:
            heightMap[::, ::] = self.parent.region.height[
                y : y + sizeSource[1] : self.parent.zoomLevel,
                x : x + sizeSource[0] : self.parent.zoomLevel,
            ]
        except ValueError:
            wx.CallAfter(self.UpdateDrawing, None)
            return
        heightMap = heightMap.astype(Numeric.float32)
        heightMap /= Numeric.array(10).astype(Numeric.float32)
        rawRGB = tools3D.onePassColors(
            False,
            heightMap.shape,
            self.parent.region.waterLevel,
            heightMap,
            rgnReader.GRADIENT_READER.paletteWater,
            rgnReader.GRADIENT_READER.paletteLand,
            lightDir,
        )
        img = wx.EmptyImage(heightMap.shape[1], heightMap.shape[0])
        img.SetData(rawRGB)

        dc = wx.BufferedDC(None, self.buffer)
        dc.BeginDrawing()
        dc.SetBackground(wx.Brush("Light Gray"))
        dc.Clear()
        dc.DrawBitmap(wx.BitmapFromImage(img), 0, 0, False)

        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.SetBrush(wx.Brush("Light Gray"))
        dc.SetLogicalFunction(wx.OR)
        dc.DrawRectangle(
            0 - x / self.parent.zoomLevel,
            0 - y / self.parent.zoomLevel,
            self.offX / self.parent.zoomLevel,
            self.parent.region.imgSize[1] / self.parent.zoomLevel,
        )
        dc.DrawRectangle(
            0 - x / self.parent.zoomLevel,
            0 - y / self.parent.zoomLevel,
            self.parent.region.imgSize[0] / self.parent.zoomLevel,
            self.offY / self.parent.zoomLevel,
        )
        dc.DrawRectangle(
            (self.parent.region.imgSize[0] + self.offX) / self.parent.zoomLevel
            - x / self.parent.zoomLevel,
            0 - y / self.parent.zoomLevel,
            -self.offX / self.parent.zoomLevel,
            self.parent.region.imgSize[1] / self.parent.zoomLevel,
        )
        dc.DrawRectangle(
            0 - x / self.parent.zoomLevel,
            (self.parent.region.imgSize[1] + self.offY) / self.parent.zoomLevel
            - y / self.parent.zoomLevel,
            self.parent.region.imgSize[0] / self.parent.zoomLevel,
            -self.offY / self.parent.zoomLevel,
        )
        dc.SetLogicalFunction(wx.COPY)

        if self.parent.overlayCbx.GetValue():
            self.AddMasked(
                dc,
                self.parent.zoomLevel,
                self.parent.region,
                x / self.parent.zoomLevel,
                y / self.parent.zoomLevel,
            )
            self.AddGrid(
                dc,
                self.parent.zoomLevel,
                self.parent.region,
                x / self.parent.zoomLevel,
                y / self.parent.zoomLevel,
            )
            self.AddOverlay(
                dc,
                self.parent.zoomLevel,
                self.parent.region,
                x / self.parent.zoomLevel,
                y / self.parent.zoomLevel,
            )
        if self.crop is not None:
            dc.SetPen(wx.TRANSPARENT_PEN)
            dc.SetBrush(wx.Brush("Light Gray"))
            dc.SetLogicalFunction(wx.XOR)
            crop = [
                min(self.crop[0], self.crop[2]),
                min(self.crop[1], self.crop[3]),
                max(self.crop[0], self.crop[2]),
                max(self.crop[1], self.crop[3]),
            ]
            self.DrawRectangle(
                dc,
                (crop[0] * 64 - x) / self.parent.zoomLevel,
                (crop[1] * 64 - y) / self.parent.zoomLevel,
                ((crop[2] - crop[0]) * 64 + 65) / self.parent.zoomLevel,
                ((crop[3] - crop[1]) * 64 + 65) / self.parent.zoomLevel,
            )
            dc.SetLogicalFunction(wx.COPY)
        if finish:
            dc.EndDrawing()
        self.wait = True
        wx.CallAfter(self.Refresh, False)
        if finish is False:
            return dc

    def AddGrid(self, dc, zoomLevel, region, xO, yO):
        lines = []
        s = (region.height.shape[1], region.height.shape[0])
        for y in range(int(s[1] / 64)):
            lines.append(
                [
                    0 - xO,
                    y * int(64 / zoomLevel) - yO,
                    region.originalConfig.size[0] * int(64 / zoomLevel) - xO,
                    y * int(64 / zoomLevel) - yO,
                ]
            )
        for x in range(int(s[0] / 64)):
            lines.append(
                [
                    x * int(64 / zoomLevel) - xO,
                    0 - yO,
                    x * int(64 / zoomLevel) - xO,
                    region.originalConfig.size[1] * int(64 / zoomLevel) - yO,
                ]
            )
        dc.SetPen(wx.Pen("Light Gray"))
        dc.DrawLineList(
            [
                (
                    x1 + self.offX / zoomLevel,
                    y1 + self.offY / zoomLevel,
                    x2 + self.offX / zoomLevel,
                    y2 + self.offY / zoomLevel,
                )
                for x1, y1, x2, y2 in lines
            ]
        )

    def AddOverlay(self, dc, zoomLevel, region, xO, yO):
        dc.SetPen(wx.Pen("WHITE"))
        dc.SetBrush(wx.Brush("WHITE", wx.TRANSPARENT))
        colours = [
            0,
            wx.Colour(255, 0, 0),
            wx.Colour(0, 255, 0),
            0,
            wx.Colour(0, 0, 255),
        ]
        # These sizes correspond to SC4 city sizes
        sizes = [0, 64, 128, 0, 256]
        for city in region.all_cities:
            x = int(city.xPos / zoomLevel)
            y = int(city.yPos / zoomLevel)
            width = sizes[city.city_x_size] / zoomLevel
            height = sizes[city.city_y_size] / zoomLevel
            dc.SetPen(wx.Pen("WHITE"))
            dc.SetBrush(wx.Brush("WHITE", wx.TRANSPARENT))
            dc.SetPen(wx.Pen(colours[city.city_x_size]))
            dc.SetBrush(wx.Brush(colours[city.city_x_size], wx.TRANSPARENT))
            self.DrawRectangle(dc, x - xO, y - yO, width, height)
            self.DrawRectangle(dc, x - xO + 1, y - yO + 1, width - 2, height - 2)

    def AddMasked(self, dc, zoomLevel, region, xO, yO):
        dc.SetPen(wx.Pen("LIGHT GRAY"))
        dc.SetBrush(wx.Brush("LIGHT GRAY", wx.CROSSDIAG_HATCH))
        width = 64 / zoomLevel
        height = 64 / zoomLevel
        for x, y in region.missingCities:
            x = int(x * 64 / zoomLevel)
            y = int(y * 64 / zoomLevel)
            self.DrawRectangle(dc, x - xO, y - yO, width, height)

    def HighlightCity(self, zoomLevel, region, pos):
        dc = self.UpdateDrawing(finish=False)
        xO, yO = self.GetViewStart()
        colours = [
            0,
            wx.Colour(255, 0, 0),
            wx.Colour(0, 255, 0),
            0,
            wx.Colour(0, 0, 255),
        ]
        for city in region.all_cities:
            if (
                pos[0] >= city.city_x_position
                and pos[0] < city.city_x_position + city.city_x_size
                and pos[1] >= city.city_y_position
                and pos[1] < city.city_y_position + city.city_y_size
            ):
                x = int(city.xPos / zoomLevel)
                y = int(city.yPos / zoomLevel)
                width = int(city.xSize / zoomLevel)
                height = int(city.ySize / zoomLevel)
                dc.SetPen(wx.Pen(colours[city.city_x_size]))
                dc.SetBrush(wx.Brush(colours[city.city_x_size], wx.CROSSDIAG_HATCH))
                self.DrawRectangle(dc, x + 1 - xO, y + 1 - yO, width - 2, height - 2)
                self.DrawRectangle(dc, x - xO, y - yO, width, height)
                self.DrawRectangle(dc, x - xO - 1, y - 1 - yO, width + 2, height + 2)
                break
        dc.EndDrawing()

    def HighlightNewCity(self, zoomLevel, region, pos, size):
        dc = self.UpdateDrawing(finish=False)
        xO, yO = self.GetViewStart()
        colours = [
            0,
            wx.Colour(255, 0, 0),
            wx.Colour(0, 255, 0),
            0,
            wx.Colour(0, 0, 255),
        ]
        x = int(pos[0] * 64 / zoomLevel)
        y = int(pos[1] * 64 / zoomLevel)
        width = size * 64 / zoomLevel
        height = size * 64 / zoomLevel
        dc.SetPen(wx.Pen(colours[size]))
        dc.SetBrush(wx.Brush(colours[size], wx.TRANSPARENT))
        self.DrawRectangle(dc, x + 1 - xO, y + 1 - yO, width - 2, height - 2)
        self.DrawRectangle(dc, x - xO, y - yO, width, height)
        self.DrawRectangle(dc, x - 1 - xO, y - 1 - yO, width + 2, height + 2)
        dc.EndDrawing()

    def DrawRectangle(self, dc, x, y, width, height):
        dc.DrawRectangle(
            int(x + self.offX / self.parent.zoomLevel),
            int(y + self.offY / self.parent.zoomLevel),
            int(width),
            int(height),
        )

    def OnPaint(self, event):
        if self.buffer is None:
            self.clear = False
            self.wait = False
            dc = wx.PaintDC(self)
            self.DoPrepareDC(dc)
            dc.SetBackground(wx.Brush(self.GetBackgroundColour()))
            dc.Clear()
        if self.buffer is not None:
            self.wait = False
            dc = wx.BufferedPaintDC(self, self.buffer, wx.BUFFER_CLIENT_AREA)
