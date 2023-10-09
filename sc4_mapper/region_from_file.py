import logging
import struct

import numpy as Numeric
import wx
import wx.adv
import wx.lib.masked as masked
from PIL import Image

from sc4_mapper import about, base_dir, rgnReader, zipUtils
from sc4_mapper.rgnReader import SC4Region

logger = logging.getLogger(__name__)


class SC4MfileHandler:
    def __init__(self, file_name):
        self.file_name = file_name

    def read(self):
        config = None
        with open(self.file_name, "rb") as raw:
            zipped = zipUtils.ZipInputStream(raw)
            s = zipped.read(4).decode()
            if s != "SC4M":
                logger.warning(f"{s} != SC4M")
                raise OSError("SC4M")
            version = struct.unpack("i", zipped.read(4))[0]
            if version != 0x0200:
                raise OSError("Version")
            ySize = struct.unpack("i", zipped.read(4))[0]
            xSize = struct.unpack("i", zipped.read(4))[0]
            # FIXME: looks like redundant
            mini = struct.unpack("f", zipped.read(4))[0]

            logger.debug(f"ySize={ySize} xSize={xSize} mini={mini}")

            temp = zipped.read(4).decode()
            logger.debug(f"Chk SC4N: {temp}")

            if temp == "SC4N":
                lenHtml = struct.unpack("i", zipped.read(4))[0]
                logger.debug(lenHtml)
                if lenHtml:
                    # FIXME: no ui should be here?
                    htmlText = zipped.read(lenHtml).decode()
                    logger.debug(htmlText)
                    # raise NotImplementedError
                    import os

                    os.chdir(os.path.split(self.file_name)[0])
                    try:
                        authorNotes = about.AuthorBox(self, htmlText)
                        wx.EndBusyCursor()
                        authorNotes.ShowModal()
                        wx.BeginBusyCursor()
                        authorNotes.Destroy()
                    except Exception as exc:
                        logger.warning(exc)
                        pass
                    os.chdir(base_dir)

                temp = zipped.read(4).decode()
                logger.info(temp)
            if temp == "SC4C":
                configSize = struct.unpack("ii", zipped.read(8))
                lenstring = struct.unpack("i", zipped.read(4))[0]

                logger.debug(f"configSize={configSize} lenstring={lenstring}")
                # FIXME: need to read hot to switch fromstring to new way, TEST
                imString = zipped.read(lenstring)
                # config = Image.fromarray(Numeric.array(imString), "RGB")
                with Image.frombytes("RGB", configSize, Numeric.array(imString)) as _im_config:
                    config = _im_config.copy()
                # config = Image.fromstring("RGB", configSize, imString)
                temp = zipped.read(4).decode()
                logger.info(f"config: {temp}")
            if temp != "SC4D":
                logger.warning(temp)
                raise OSError("SC4D")
            r = Numeric.frombuffer(zipped.read(xSize * ySize), Numeric.uint8)
            rH = Numeric.frombuffer(zipped.read(xSize * ySize), Numeric.uint8)
            zipped = None
        r = r.astype(Numeric.uint16)
        rH = rH.astype(Numeric.uint16)
        rH *= Numeric.array(256).astype(Numeric.uint16)
        r += rH
        del rH

        return r, config


class SC4MfileHandlerGrey:
    def __init__(self, file_name):
        self.file_name = file_name

    def read(self):
        with Image.open(self.file_name) as im:
            if im.mode != "L":
                im = im.convert("L")
            data = Numeric.array(im, dtype=Numeric.uint16)
            return data.flatten()


class SC4MfileHandlerPNG:
    def __init__(self, file_name):
        self.file_name = file_name

    def read(self):
        with Image.open(self.file_name) as im:
            # PNG 16-bit grayscale can be "I;16" or "I"
            if im.mode not in ("I;16", "I"):
                logger.warning(f"Unexpected PNG mode {im.mode}, converting to 16-bit")
                im = im.convert("I")
            data = Numeric.array(im, dtype=Numeric.uint16)
            return data.flatten()


class SC4MfileHandlerRGB:
    def __init__(self, file_name):
        self.file_name = file_name

    def read(self):
        with Image.open(self.file_name) as im:
            if im.mode != "RGB":
                im = im.convert("RGB")
            data = Numeric.array(im, dtype=Numeric.uint16)
            # Encoding: H = ((Red >> 4) << 12) | ((Green >> 4) << 8) | Blue
            red = data[:, :, 0]
            green = data[:, :, 1]
            blue = data[:, :, 2]
            height = (((red >> 4) << 12) | ((green >> 4) << 8) | blue).astype(Numeric.uint16)
            return height.flatten()


class CreateRgnFromFileDialog(wx.Dialog):
    """Dialog for entering region setting ( file , size , name, config.bmp )"""

    def __init__(self, parent, title, wildCard, bAllowScale=False):
        self.wildCard = wildCard
        wx.Dialog.__init__(self)
        self.SetExtraStyle(wx.FRAME_EX_CONTEXTHELP)
        self.Create(parent, -1, title)

        labelFileName = wx.StaticText(self, -1, "Filename:")
        self.fileName = wx.TextCtrl(self, -1, "", size=(300, -1), style=wx.TE_READONLY)
        browseFile = wx.Button(self, -1, "...", size=(40, -1))
        if bAllowScale:
            label = wx.StaticText(self, -1, "Scale factor:")
            self.imageFactor = wx.ComboBox(self, -1, "Default factor", size=(150, -1), style=wx.CB_DROPDOWN)
            scaleTable = [
                "100m",
                "250m",
                "500m",
                "Default factor",
                "1000m",
                "1500m",
                "2000m",
                "import.dat",
                "2500m",
                "3000m",
                "3500m",
                "4000m",
                "4500m",
                "5000m",
            ]
            for s in scaleTable:
                self.imageFactor.Append(s)
        self.fromConfig = wx.RadioButton(self, -1, "Config.bmp", style=wx.RB_GROUP)
        self.configFileName = wx.TextCtrl(self, -1, "", size=(200, -1), style=wx.TE_READONLY)
        browseConfig = wx.Button(self, -1, "...", size=(40, -1))
        self.fromSize = wx.RadioButton(self, -1, "Specify size (tiles):")
        self.sizeX = masked.NumCtrl(self, value=8, integerWidth=4, allowNegative=False, min=2, size=(60, -1))
        self.sizeY = masked.NumCtrl(self, value=8, integerWidth=4, allowNegative=False, min=2, size=(60, -1))
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Filename row
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(labelFileName, 0, wx.ALIGN_CENTRE_VERTICAL | wx.ALL, 10)
        box.Add(self.fileName, 1, wx.ALIGN_CENTRE_VERTICAL | wx.ALL, 10)
        box.Add(browseFile, 0, wx.ALIGN_CENTRE_VERTICAL | wx.ALL, 10)
        sizer.Add(box, 0, wx.EXPAND)

        if bAllowScale:
            # Scale factor row
            box = wx.BoxSizer(wx.HORIZONTAL)
            box.Add(label, 0, wx.ALIGN_CENTRE_VERTICAL | wx.ALL, 10)
            box.Add(self.imageFactor, 0, wx.ALIGN_CENTRE_VERTICAL | wx.ALL, 10)
            sizer.Add(box, 0, wx.EXPAND)

        # Config row
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.fromConfig, 0, wx.ALIGN_CENTRE_VERTICAL | wx.ALL, 10)
        box.Add(self.configFileName, 1, wx.ALIGN_CENTRE_VERTICAL | wx.ALL, 10)
        box.Add(browseConfig, 0, wx.ALIGN_CENTRE_VERTICAL | wx.ALL, 10)
        sizer.Add(box, 0, wx.EXPAND)

        # Size row
        box = wx.BoxSizer(wx.HORIZONTAL)
        box.Add(self.fromSize, 0, wx.ALIGN_CENTRE_VERTICAL | wx.ALL, 10)
        box.Add(self.sizeX, 0, wx.ALIGN_CENTRE_VERTICAL | wx.ALL, 10)
        box.Add(wx.StaticText(self, -1, "x"), 0, wx.ALIGN_CENTRE_VERTICAL)
        box.Add(self.sizeY, 0, wx.ALIGN_CENTRE_VERTICAL | wx.ALL, 10)
        sizer.Add(box, 0, wx.EXPAND)
        line = wx.StaticLine(self, -1, size=(20, -1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW | wx.ALL, 5)
        btnsizer = wx.StdDialogButtonSizer()
        self.btnOk = wx.Button(self, wx.ID_OK, size=(80, -1))
        self.btnOk.SetDefault()
        btnsizer.AddButton(self.btnOk)
        btn = wx.Button(self, wx.ID_CANCEL, size=(80, -1))
        btnsizer.AddButton(btn)
        btnsizer.Realize()
        sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 10)
        self.SetSizer(sizer)
        self.SetMinSize((500, 400))
        self.Center()
        sizer.Fit(self)
        self.Bind(wx.EVT_BUTTON, self.OnBrowseFile, browseFile)
        self.Bind(wx.EVT_BUTTON, self.OnBrowseConfig, browseConfig)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnSelectSize, self.fromSize)
        self.Bind(wx.EVT_RADIOBUTTON, self.OnSelectConfig, self.fromConfig)
        self.sizeX.Enable(True)
        self.sizeY.Enable(True)
        self.configFileName.Enable(False)
        self.fromConfig.SetValue(False)
        self.fromSize.SetValue(True)
        self.btnOk.Enable(False)

    def GetImageFactor(self):
        """return the factor for standard terran mod or a real value"""
        s = self.imageFactor.GetValue()
        scales = {
            "100m": 1.3725,
            "250m": 1.9608,
            "500m": 2.9412,
            "Default factor": 3.0,
            "1000m": 4.9020,
            "1500m": 6.8627,
            "2000m": 8.8235,
            "import.dat": 9.7832,
            "2500m": 10.7843,
            "3000m": 12.7451,
            "3500m": 14.7059,
            "4000m": 16.6667,
            "4500m": 18.6275,
            "5000m": 20.5882,
        }
        if s in scales.keys():
            return scales[s]

        try:
            return float(s)
        except Exception as exc:
            logger.warning(exc)
            return 3.0

    def OnSelectConfig(self, event):
        self.sizeX.Enable(False)
        self.sizeY.Enable(False)
        self.configFileName.Enable(True)

    def OnSelectSize(self, event):
        self.sizeX.Enable(True)
        self.sizeY.Enable(True)
        self.configFileName.Enable(False)

    def OnBrowseFile(self, event):
        dlg = wx.FileDialog(
            self,
            message="Choose a file",
            # FIXME: get rid of this.
            defaultDir=base_dir,
            defaultFile="",
            wildcard=self.wildCard,
            style=wx.FD_OPEN,
        )
        if dlg.ShowModal() == wx.ID_OK:
            paths = dlg.GetPaths()
            dlg.Destroy()
            try:
                logger.debug(paths)
                im = None
                with open(paths[0], "rb") as im_file:
                    im = Image.open(im_file)
                x = (im.size[0] - 1) / 64
                y = (im.size[1] - 1) / 64
                self.fileName.SetValue(paths[0])
                self.sizeX.SetValue(x)
                self.sizeY.SetValue(y)
            except Exception("Not Valid Image!") as image_err:
                logger.warning(image_err)
                dlg1 = wx.MessageDialog(self, "This is not a valid file", "Error", wx.OK | wx.ICON_ERROR)
                dlg1.ShowModal()
                dlg1.Destroy()
                return
            del im
            self.btnOk.Enable(True)
        dlg.Destroy()

    def OnBrowseConfig(self, event):
        dlg = wx.FileDialog(
            self,
            message="Choose a config.bmp",
            defaultDir=base_dir,
            defaultFile="",
            wildcard="config (*.bmp)|*config.bmp",
            style=wx.FD_OPEN,
        )
        if dlg.ShowModal() == wx.ID_OK:
            paths = dlg.GetPaths()
            dlg.Destroy()
            self.configFileName.SetValue(paths[0])
            try:
                im = None
                with open(paths[0], "rb") as im_file:
                    im = Image.open(im_file)
                x = im.size[0]
                y = im.size[1]
                self.sizeX.SetValue(x)
                self.sizeY.SetValue(y)
            except Exception("bad config") as bad_config:
                logger.warning(bad_config)
                dlg1 = wx.MessageDialog(self, "This is not a valid config", "Error", wx.OK | wx.ICON_ERROR)
                dlg1.ShowModal()
                dlg1.Destroy()
                return
            del im
            self.fromConfig.SetValue(True)
            self.fromSize.SetValue(False)
            self.sizeX.Enable(False)
            self.sizeY.Enable(False)
            self.configFileName.Enable(True)
        dlg.Destroy()


def CreateRgnFromFile(handler, frame):
    config = None
    r = None
    scale = 1.0

    if isinstance(handler, SC4MfileHandler):
        r, config = handler.read()
    else:
        # Determine wildcard based on handler
        wild = "*.*"
        if isinstance(handler, SC4MfileHandlerGrey):
            wild = "Image file (*.png;*.jpg;*.bmp)|*.png;*.jpg;*.bmp"
        elif isinstance(handler, SC4MfileHandlerPNG):
            wild = "PNG file (*.png)|*.png"
        elif isinstance(handler, SC4MfileHandlerRGB):
            wild = "Image file (*.png;*.jpg;*.bmp)|*.png;*.jpg;*.bmp"

        dlg = CreateRgnFromFileDialog(frame, "Import parameters", wild, bAllowScale=True)
        dlg.fileName.SetValue(handler.file_name)

        # Try to guess size from image
        try:
            with Image.open(handler.file_name) as im:
                x = (im.size[0] - 1) // 64
                y = (im.size[1] - 1) // 64
                dlg.sizeX.SetValue(x)
                dlg.sizeY.SetValue(y)
            dlg.btnOk.Enable(True)
        except Exception as exc:
            logger.warning(exc)

        if dlg.ShowModal() == wx.ID_OK:
            scale = dlg.GetImageFactor()
            handler.file_name = dlg.fileName.GetValue()
            r = handler.read()

            if dlg.fromConfig.GetValue():
                configPath = dlg.configFileName.GetValue()
                with Image.open(configPath) as im_config:
                    config = im_config.copy()
            else:
                x = int(dlg.sizeX.GetValue())
                y = int(dlg.sizeY.GetValue())
                config = rgnReader.BuildBestConfig((x, y))
        else:
            dlg.Destroy()
            return None
        dlg.Destroy()

    if r is not None and config is not None:
        if scale != 1.0:
            r = (r.astype(Numeric.float32) * scale).astype(Numeric.uint16)

        # Create the region
        region = SC4Region(None, 250, None, config=config)

        # Initialize the region view
        region.show(None, readFiles=False)

        # Assign the heightmap
        try:
            # Try to reshape. if it fails, the image might have wrong dimensions
            if r.size != region.shape[0] * region.shape[1]:
                logger.warning(f"Heightmap size {r.size} mismatch with region shape {region.shape}. Resizing.")
                # This is a bit slow because we have to go back to Image
                temp_im = Image.fromarray(r.reshape((-1, int(Numeric.sqrt(r.size)))) if Numeric.sqrt(r.size).is_integer() else r.reshape((1, -1)))
                temp_im = temp_im.resize((region.imgSize[0], region.imgSize[1]), Image.Resampling.BILINEAR)
                r = Numeric.array(temp_im, dtype=Numeric.uint16)

            region.height = r.reshape(region.shape)
        except Exception as e:
            logger.error(f"Failed to assign heightmap: {e}")
            return None

        return region

    return None
