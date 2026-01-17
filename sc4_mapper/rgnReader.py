import logging
import os.path
import struct
import sys
import time
from enum import Enum

# FIXME: SHHHH no no no
from math import sqrt

# import JpegImagePlugin
import numpy as Numeric

# import PngImagePlugin
import QFS
import tools3D
import wx
from PIL import Image, ImageDraw

# import BmpImagePlugin
from sc4_mapper.gradient_reader import GradientReader

logger = logging.getLogger(__name__)

Image._initialized = 2
generic_saveValue = 3
COMPRESSED_SIG = 0xFB10

# FIXME: hacky hacks
GRADIENT_READER = GradientReader("static/basicColors.ini")

# FIXME: thats hack for missing dircache... not sure its needed
global_cache = {}


def cached_listdir(path):
    res = global_cache.get(path)
    if res is None:
        res = os.listdir(path)
        global_cache[path] = res
    return res


def normalize(p1):
    dx = float(p1[0])
    dy = float(p1[1])
    dz = float(p1[2])
    norm = sqrt(dx * dx + dy * dy + dz * dz)
    try:
        return (p1[0] / norm, p1[1] / norm, p1[2] / norm)
    except Exception as exc:
        logger.warning(exc)
        return (0, 0, 0)


# TODO: this is not used
def compute_one_rgb(bLight, height, waterLevel, region):
    lightDir = normalize((1, -5, -1))
    rawRGB = tools3D.onePassColors(
        bLight,
        height.shape,
        waterLevel,
        height,
        GRADIENT_READER.paletteWater,
        GRADIENT_READER.paletteLand,
        lightDir,
    )
    rgb = Numeric.fromstring(rawRGB, Numeric.int8)
    rgb = Numeric.reshape(rgb, (height.shape[0], height.shape[1], 3))
    return rgb


class TGIenum(Enum):
    heights = (0xA9DD6FF4, 0xE98F9525, 0x00000001)
    terrain = (0xA9DD6FF4, 0xE98F9525, 0x00000001)


class CitySize(Enum):
    SMALL = 1
    MEDIUM = 2
    LARGE = 4


class SC4Entry:
    def __init__(self, buffer, idx):
        self.compressed = False
        logger.debug(f"{buffer} - {len(buffer)}")
        self.buffer = buffer
        # FIXME: this is broken atm
        # t, g, i, self.fileLocation, self.filesize = struct.unpack("3Lll", buffer)
        t, g, i, self.fileLocation, self.filesize = struct.unpack("3iii", buffer)
        logger.debug(f"{t}, {g}, {i}, {self.fileLocation}, {self.filesize}")
        self.TGI = {"t": t, "g": g, "i": i}
        self.initialFileLocation = self.fileLocation
        self.order = idx
        logger.debug(f"{self.TGI} -- {self.fileLocation}, {self.filesize}")

    def read_file(self, read_full=True, decompress=False):
        logger.debug("Reading full")
        self.raw_content = None
        with open(self.file_name) as sc4_file:
            sc4_file.seek(self.fileLocation)
            self.raw_content = sc4_file.read(self.filesize)
            logger.debug(self.raw_content)

    def ReadFile(self, sc4, readWhole=True, decompress=False):
        self.rawContent = None
        if readWhole:
            logger.debug("Reading full")
            sc4.seek(self.fileLocation)
            self.rawContent = sc4.read(self.filesize)
            if decompress:
                if len(self.rawContent) >= 8:
                    compress_sig = struct.unpack("H", self.rawContent[0x04 : 0x04 + 2])[
                        0
                    ]
                    if compress_sig == COMPRESSED_SIG:
                        self.compressed = True
            if self.compressed:
                if decompress:
                    logger.info("Compressed file")
                uncompress = QFS.decode(self.rawContent[4:])
                self.content = uncompress
            else:
                if decompress:
                    logger.info("Uncompressed file")
                self.content = self.rawContent

    def IsItThisTGI(self, tgi):
        logger.debug(f"{tgi} vs self={self.TGI}:")
        return (
            tgi[0] == self.TGI["t"]
            and tgi[1] == self.TGI["g"]
            and tgi[2] == self.TGI["i"]
        )

    def GetDWORD(self, pos):
        return struct.unpack("i", self.content[pos : pos + 4])[0]

    def GetString(self, pos, length):
        return self.content[pos : pos + length]


class SaveFile:
    """Class to be able to create a SC4 save file to hold city information, starting from a blank city"""

    def __init__(self, fileName):
        """load filename which should be a blank city"""
        self.fileName = fileName
        # FIXME: whyyyy whyyy... with openme
        self.sc4 = open(self.fileName, "rb")
        self.ReadHeader()
        self.read_entries()

    def ReadHeader(self):
        """read the SC4 DBPF header"""
        self.header = self.sc4.read(96)
        # FIXME: py2 badddas
        # self.header = self.header[0:0x30] + "\0" * 12 + self.header[0x30 + 12 : 96]
        self.header = self.header[0:0x30] + bytes(12) + self.header[0x30 + 12 : 96]
        raw = struct.unpack("4s17i24s", self.header)
        self.fileVersionMajor = raw[1]
        self.fileVersionMinor = raw[2]
        self.dateCreated = raw[3]
        self.dateUpdated = raw[4]

        self.indexRecordType = raw[8]
        self.indexRecordEntryCount = raw[9]
        self.indexRecordPosition = raw[10]
        self.indexRecordLength = raw[11]
        self.holeRecordEntryCount = raw[12]
        self.holeRecordPosition = raw[13]
        self.holeRecordLength = raw[14]

    def read_entries(self):
        """Create entries for writing them later"""
        self.entries = []
        self.sc4.seek(self.indexRecordPosition)
        header = self.sc4.read(self.indexRecordLength)
        for idx in range(self.indexRecordEntryCount):
            entry = SC4Entry(header[idx * 20 : idx * 20 + 20], idx)

            if entry.IsItThisTGI(
                (0xA9DD6FF4, 0xE98F9525, 0x00000001)
            ) or entry.IsItThisTGI((0xCA027EDB, 0xCA027EE1, 0x00000000)):
                entry.ReadFile(self.sc4, True, True)
            else:
                entry.ReadFile(self.sc4)
            self.entries.append(entry)
        self.sc4.close()

    def Save(self, city_x_position, city_y_position, heightMap, saveName):
        """Save a city
        read all entries
        create a save file
        replace the height,city info and region picture entry
        save all entries
        """
        global generic_saveValue
        time.sleep(0.1)
        self.heightMap = heightMap
        # FIXME: redundant
        """
        xSize = self.heightMap.shape[0]
        ySize = self.heightMap.shape[1]
        """
        newData = QFS.encode(struct.pack("H", 0x2) + self.heightMap.tostring())
        newData = struct.pack("l", len(newData)) + newData
        self.indexRecordPosition = 96
        self.dateUpdated = int(time.time()) + generic_saveValue * 65535
        generic_saveValue += 1
        self.header = (
            self.header[0:0x1C]
            + struct.pack("I", self.dateUpdated)
            + self.header[0x1C + 4 : 0x28]
            + struct.pack("l", self.indexRecordPosition)
            + self.header[0x28 + 4 : 96]
        )
        with open(self.fileName, "rb") as sc4:
            for entry in self.entries:
                if entry.IsItThisTGI(
                    (0xA9DD6FF4, 0xE98F9525, 0x00000001)
                ) or entry.IsItThisTGI((0xCA027EDB, 0xCA027EE1, 0x00000000)):
                    entry.ReadFile(sc4, True, True)
                if entry.rawContent is None:
                    entry.ReadFile(sc4, True)
        # FIXME: .... nope dangerzone
        while 1:
            try:
                self.sc4 = open(saveName, "wb")
                break
            except IOError:
                dlg = wx.MessageDialog(
                    None,
                    "file %s seems to be ReadOnly\nDo you want to skip?(Yes)\nOr retry ?(No)"
                    % (saveName),
                    "Warning",
                    wx.YES_NO | wx.ICON_QUESTION,
                )
                result = dlg.ShowModal()
                dlg.Destroy()
                if result == wx.ID_YES:
                    return False
        self.sc4.write(self.header)
        self.sc4.truncate(self.indexRecordPosition)
        self.sc4.seek(self.indexRecordPosition)
        pos = self.indexRecordPosition + self.indexRecordLength
        for entry in self.entries:
            entry.fileLocation = pos
            newbuffer = (
                entry.buffer[0:0x0C]
                + struct.pack("l", entry.fileLocation)
                + entry.buffer[0x0C + 4 :]
            )
            if entry.IsItThisTGI((0xA9DD6FF4, 0xE98F9525, 0x00000001)):  # heights
                newbuffer = (
                    entry.buffer[0:0x0C]
                    + struct.pack("l", entry.fileLocation)
                    + struct.pack("l", len(newData))
                    + entry.buffer[0x10 + 4 :]
                )
                entry.rawContent = newData
                entry.compressed = 1
                entry.filesize = len(newData)
            if entry.IsItThisTGI((0xCA027EDB, 0xCA027EE1, 0x00000000)):  # city info
                v = self.dateUpdated
                entry.content = (
                    entry.content[0:0x04]
                    + struct.pack("I", city_x_position)
                    + struct.pack("I", city_y_position)
                    + entry.content[0x0C:39]
                    + struct.pack("I", v)
                    + entry.content[39 + 4 :]
                )
                newDataCity = entry.rawContent[:]
                newDataCity = QFS.encode(entry.content)
                newDataCity = struct.pack("l", len(newDataCity)) + newDataCity
                newbuffer = (
                    entry.buffer[0:0x0C]
                    + struct.pack("l", entry.fileLocation)
                    + struct.pack("l", len(newDataCity))
                    + entry.buffer[0x10 + 4 :]
                )
                entry.rawContent = newDataCity
                entry.compressed = 1
                entry.filesize = len(newDataCity)
            if entry.IsItThisTGI((0x8A2482B9, 0x4A2482BB, 0x00000000)):  # region view
                n = os.path.splitext(saveName)[0]
                png = open(n + ".PNG", "rb")
                pngData = png.read()
                png.close()
                os.unlink(n + ".PNG")
                newbuffer = (
                    entry.buffer[0:0x0C]
                    + struct.pack("I", entry.fileLocation)
                    + struct.pack("I", len(pngData))
                    + entry.buffer[0x10 + 4 :]
                )
                entry.rawContent = pngData
                entry.compressed = 0
                entry.filesize = len(pngData)
            if entry.IsItThisTGI(
                (0x8A2482B9, 0x4A2482BB, 0x00000002)
            ):  # alpha region view
                n = os.path.splitext(saveName)[0]
                png = open(n + "_alpha.PNG", "rb")
                pngData = png.read()
                png.close()
                os.unlink(n + "_alpha.PNG")
                newbuffer = (
                    entry.buffer[0:0x0C]
                    + struct.pack("I", entry.fileLocation)
                    + struct.pack("I", len(pngData))
                    + entry.buffer[0x10 + 4 :]
                )
                entry.rawContent = pngData
                entry.compressed = 0
                entry.filesize = len(pngData)
            self.sc4.write(newbuffer)
            pos += entry.filesize
        for entry in self.entries:
            self.sc4.write(entry.rawContent)
        self.sc4.close()
        return True


def Save(city, folder, color, waterLevel):
    """Save a city file, build the thumbnail for region view"""
    mainPath = sys.path[0]
    # FIXME: this looks bad
    os.chdir(mainPath)
    if city.city_x_size == CitySize.SMALL.value:
        name = "City - Small.sc4"
    if city.city_x_size == CitySize.MEDIUM.value:
        name = "City - Medium.sc4"
    if city.city_x_size == CitySize.LARGE.value:
        name = "City - Large.sc4"
    city.fileName = (
        folder
        + "/"
        + "City - New city(%03d-%03d).sc4"
        % (city.city_x_position, city.city_y_position)
    )
    BuildThumbnail(city, color, waterLevel)
    saved = SaveFile(name)
    return saved.Save(
        city.city_x_position, city.city_y_position, city.heightMap, city.fileName
    )


def BuildThumbnail(city, colors, waterLevel):
    """Build the region view images (normal&alpha)"""
    n = os.path.splitext(city.fileName)[0]
    minx, miny, maxx, maxy, r = tools3D.generateImage(
        waterLevel, city.heightMap.shape, city.heightMap.tostring(), colors
    )
    logger.info(city.heightMap.shape, len(colors))
    logger.info(minx, miny, maxx, maxy)
    maxx += 2
    offset = len(r) / 2
    im = Image.fromstring("RGB", (514, 428), r[:offset])
    im = im.crop([minx, miny, maxx, maxy])
    im.save(n + ".PNG")
    im = Image.fromstring("RGB", (514, 428), r[offset:])
    im = im.crop([minx, miny, maxx, maxy])
    im.save(n + "_alpha.PNG")
    return


class SC4City:
    """SC4 city class"""

    def check_position(self, x: int, y: int) -> bool:
        """check if the city is at a specific coordinate ( in config.bmp coordinate )"""
        return x == self.city_x_position and y == self.city_y_position

    def split(self):
        """spliting a city, only for medium or large city, divide the city in 4 smallers cities"""
        if self.city_x_size == 1:
            logger.info("city is too small to split")
            return []

        return [
            CityProxy(
                250,
                self.city_x_position,
                self.city_y_position,
                self.city_x_size / 2,
                self.city_y_size / 2,
            ),
            CityProxy(
                250,
                self.city_x_position + self.city_x_size / 2,
                self.city_y_position,
                self.city_x_size / 2,
                self.city_y_size / 2,
            ),
            CityProxy(
                250,
                self.city_x_position + self.city_x_size / 2,
                self.city_y_position + self.city_y_size / 2,
                self.city_x_size / 2,
                self.city_y_size / 2,
            ),
            CityProxy(
                250,
                self.city_x_position,
                self.city_y_position + self.city_y_size / 2,
                self.city_x_size / 2,
                self.city_y_size / 2,
            ),
        ]


class SC4File(SC4City):
    """A file representing a saved city on the regions folder"""

    def __init__(self, fileName):
        self.fileName = fileName

    def read_header(self):
        with open(self.fileName, "rb") as sc4_file_obj:
            self.header = sc4_file_obj.read(96)
        # FIXME: thats some black magic at this hour... no idea...
        # self.header = self.header[0:0x30] + "\0" * 12 + self.header[0x30 + 12 : 96]
        self.header = self.header[0:0x30] + bytes(12) + self.header[0x30 + 12 : 96]
        raw = struct.unpack("4s17i24s", self.header)
        logger.debug(raw)

        assert raw[0] == b"DBPF"

        self.fileVersionMajor = raw[1]
        self.fileVersionMinor = raw[2]
        self.dateCreated = raw[3]
        self.dateUpdated = raw[4]

        self.indexRecordType = raw[8]
        self.indexRecordEntryCount = raw[9]
        self.indexRecordPosition = raw[10]
        self.indexRecordLength = raw[11]
        self.holeRecordEntryCount = raw[12]
        self.holeRecordPosition = raw[13]
        self.holeRecordLength = raw[14]

        logger.info(
            f"{os.path.split(self.fileName)[1]} {self.indexRecordPosition} "
            f"{self.indexRecordEntryCount} {self.indexRecordLength} "
        )

    def read_entries(self):
        """Read all entries, only a few are read deeply and only the height entry is kept"""
        self.entries = []
        with open(self.fileName, "rb") as sc4_file_obj:
            sc4_file_obj.seek(self.indexRecordPosition)
            header = sc4_file_obj.read(self.indexRecordLength)

        logger.debug(header)
        for idx in range(self.indexRecordEntryCount):
            entry = SC4Entry(header[idx * 20 : idx * 20 + 20], idx)

            if entry.IsItThisTGI(
                (0xA9DD6FF4, 0xE98F9525, 0x00000001)
            ) or entry.IsItThisTGI((0xCA027EDB, 0xCA027EE1, 0x00000000)):
                # entry.ReadFile(self.sc4, True, True)
                with open(self.fileName, "rb") as sc4_file_obj:
                    entry.read_file(sc4_file_obj, True, True)

            if entry.IsItThisTGI((0xA9DD6FF4, 0xE98F9525, 0x00000001)):
                logger.info("This was the terrain")
                self.heightMapEntry = entry

            if entry.IsItThisTGI((0xCA027EDB, 0xCA027EE1, 0x00000000)):
                logger.info(f"This was the city info: {entry.compressed}")
                # FIXME:?????
                logger.info(f"version {hex(entry.GetDWORD(0x00))}")
                version = entry.GetDWORD(0x00)
                self.city_x_position = entry.GetDWORD(0x04)
                self.city_y_position = entry.GetDWORD(0x08)
                self.city_x_size = entry.GetDWORD(0x0C)
                self.city_y_size = entry.GetDWORD(0x10)
                logger.info(
                    f"\ncity tile X = {self.city_x_position} "
                    f"city tile Y = {self.city_y_position}"
                    f"\ncity size X = {self.city_x_size} "
                    f"city size Y = {self.city_y_size}"
                )
                offsetLen = 64
                if version == 0xD0001:
                    offsetLen = 64
                if version == 0xA0001:
                    offsetLen = 63
                if version == 0x90001:
                    offsetLen = 59
                sizeName = entry.GetDWORD(offsetLen)
                logger.info(f"name city length={sizeName}")
                if sizeName < 100:
                    self.cityName = entry.GetString(offsetLen + 4, sizeName)
                    logger.info(self.cityName)
                else:
                    logger.info(f"xxxxxxxxxxxxxxxxxxxxoldv {version}")
                    self.cityName = "weird name"
        logger.info("finished reading the sc4")
        logger.info("--" * 20)

        # FIXME: above can exit without actual size
        self.ySize = self.city_y_size * 64 + 1
        self.xSize = self.city_x_size * 64 + 1
        self.xPos = self.city_x_position * 64
        self.yPos = self.city_y_position * 64
        header = None


class CityProxy(SC4City):
    """A proxy for an empty city"""

    def __init__(self, waterLevel, xPos, yPos, xSize, ySize):
        self.city_x_position = xPos
        self.city_y_position = yPos
        self.city_x_size = xSize
        self.city_y_size = ySize
        self.cityName = "Not created yet"
        self.ySize = self.city_y_size * 64 + 1
        self.xSize = self.city_x_size * 64 + 1
        self.xPos = self.city_x_position * 64
        self.yPos = self.city_y_position * 64
        self.fileName = None


def parse_config(config, waterLevel):
    """Read the config.bmp, verify it, and create the city proxies for it"""
    verified = Numeric.zeros(config.size, Numeric.int8)

    def redish(value):
        """True for small city"""
        (r, g, b) = value
        if r > g and r > b and r > 250:
            return True
        return False

    def greenish(value):
        """True for medium city"""
        (r, g, b) = value
        if g > r and g > b and g > 250:
            return True
        return False

    def blueish(value):
        """True for big city"""
        (r, g, b) = value
        if b > r and b > g and b > 250:
            return True
        return False

    def VerifyMedium(x, y):
        """Verify the 2x2 pixels from x,y are green"""
        rgbs = (
            config.getpixel((x + 1, y)),
            config.getpixel((x, y + 1)),
            config.getpixel((x + 1, y + 1)),
        )
        for rgb in rgbs:
            if not greenish(rgb):
                assert 0
        verified[x, y] = 1
        verified[x + 1, y] = 1
        verified[x, y + 1] = 1
        verified[x + 1, y + 1] = 1

    def VerifyLarge(x, y):
        """Verify the 4x4 pixels from x,y are blue"""
        rgbs = (
            config.getpixel((x + 1, y)),
            config.getpixel((x + 2, y)),
            config.getpixel((x + 3, y)),
            config.getpixel((x, y + 1)),
            config.getpixel((x + 1, y + 1)),
            config.getpixel((x + 2, y + 1)),
            config.getpixel((x + 3, y + 1)),
            config.getpixel((x, y + 2)),
            config.getpixel((x + 1, y + 2)),
            config.getpixel((x + 2, y + 2)),
            config.getpixel((x + 3, y + 2)),
            config.getpixel((x, y + 3)),
            config.getpixel((x + 1, y + 3)),
            config.getpixel((x + 2, y + 3)),
            config.getpixel((x + 3, y + 3)),
        )
        for rgb in rgbs:
            if not blueish(rgb):
                assert 0
        for j in range(4):
            for i in range(4):
                verified[x + i, y + j] = 1

    big = 0
    bigs = []
    small = 0
    smalls = []
    medium = 0
    mediums = []
    for y in range(config.size[1]):
        for x in range(config.size[0]):
            if verified[x, y] == 0:
                rgb = config.getpixel((x, y))
                if blueish(rgb):
                    try:
                        VerifyLarge(x, y)
                        bigs.append((x, y))
                        big += 1
                    except Exception as exc:
                        logger.warning(f"{x}, {y} not blue: {exc}")
                        raise
                if greenish(rgb):
                    try:
                        VerifyMedium(x, y)
                        mediums.append((x, y))
                        medium += 1
                    except Exception as exc:
                        logger.warning(f"{x}, {y} not green: {exc}")
                        raise
                if redish(rgb):
                    smalls.append((x, y))
                    small += 1

    for name, x in zip(["big", "medium", "small"], [big, medium, small]):
        logger.info(f"{name}={x}")
    cities = (
        [CityProxy(waterLevel, c[0], c[1], 1, 1) for c in smalls]
        + [CityProxy(waterLevel, c[0], c[1], 2, 2) for c in mediums]
        + [CityProxy(waterLevel, c[0], c[1], 4, 4) for c in bigs]
    )
    return cities


def BuildBestConfig(configSize):
    """Create a config.bmp that will be filled with as most big cities as it can, then medium then small"""
    im = Image.new("RGB", configSize, "#0000FF")
    nbBigX = configSize[0] / 4
    nbMediumX = 0
    nbSmallX = 0
    rX = configSize[0] % 4
    if rX == 1 or rX == 3:
        nbSmallX = 1
    if rX == 3 or rX == 2:
        nbMediumX = 1
    nbBigY = configSize[1] / 4
    # nbSmallY = 0
    nbMediumY = 0
    rY = configSize[1] % 4
    # FIXME: redundant
    """if rY == 1 or rY == 3:
        nbSmallY = 1
    """
    if rY == 3 or rY == 2:
        nbMediumY = 1
    logger.info(configSize[0], rX, nbBigX, "(B)", nbMediumX, "(M)", nbSmallX, "(S)")
    im.paste("#00FF00", (nbBigX * 4, 0, configSize[0], configSize[1]))
    im.paste("#00FF00", (0, nbBigY * 4, configSize[0], configSize[1]))
    im.paste("#FF0000", (nbBigX * 4 + nbMediumX * 2, 0, configSize[0], configSize[1]))
    im.paste("#FF0000", (0, nbBigY * 4 + nbMediumY * 2, configSize[0], configSize[1]))
    return im


class SC4Region:
    "a SC4 region, contains cities, layout and height map"

    def __init__(self, folder, waterLevel, dlg, config=None):
        self.waterLevel = waterLevel
        self.folder = folder
        self.dlg = dlg

        self.all_cities = []
        self.all_city_file_names = []
        self.original_config = None

        if config is not None:
            self.folder = None
            self.config = config
            self.config = self.config.convert("RGB")
            self.original_config = self.config.copy()
            self.all_cities = parse_config(self.config, waterLevel)
        else:
            self._init_config()

    def _compare_saves_vs_config(self):
        """Verify saves vs config"""
        for save in self.all_city_file_names:
            if self.dlg is not None:
                self.dlg.Update(
                    1, "Please wait while loading the region" + "\nReading " + save
                )
            sc4 = SC4File(os.path.join(self.folder, save))
            sc4.read_header()
            sc4.read_entries()
            for i, city in enumerate(self.all_cities):
                if city.check_position(sc4.city_x_position, sc4.city_y_position):
                    if (
                        isinstance(city, CityProxy)
                        and city.city_x_position == sc4.city_x_position
                        and city.city_y_position == sc4.city_y_position
                        and city.city_x_size == sc4.city_x_size
                        and city.city_y_size == sc4.city_y_size
                    ):
                        self.all_cities = self.all_cities[:i] + self.all_cities[i + 1 :]
                    else:
                        # FIXME: move to ui module
                        dlg1 = wx.MessageDialog(
                            None,
                            "It seems that the config.bmp does not match the savegames present in the region folder",
                            "error",
                            wx.OK | wx.ICON_ERROR,
                        )
                        dlg1.ShowModal()
                        dlg1.Destroy()
                        self.all_cities = None
                        return
            self.all_cities.append(sc4)

        self.config = self.BuildConfig()
        self.original_config = self.BuildConfig()

        if self.dlg:
            self.dlg.Update(1, "Please wait while loading the region")

    def _init_config(self):
        all_files = cached_listdir(self.folder)
        logger.debug(all_files)
        self.all_city_file_names = [
            x for x in all_files if os.path.splitext(x)[1] == ".sc4"
        ]
        try:
            config_file_name = utils.encodeFilename(
                os.path.join(self.folder, "config.bmp")
            )
            config_file_name = os.path.join(self.folder, "config.bmp")
            logger.debug(f"{config_file_name} - {type(config_file_name)}")
            # self.config = Image.open(config_file_name)
            # config_file_name = "/app/region_tests/San Francisco/config.bmp"
            with open(config_file_name, "rb") as bmp_temp:
                self.config = Image.open(bmp_temp).copy()
        except Exception as exc:
            logger.exception(exc)
            self.config = None
            raise

    def crop_config(self):
        "find the bbox of valid cities and return the new resized config"
        sizeX = sizeY = 0
        minX = minY = maxX = maxY = None
        for city in self.all_cities:
            if minX is None or city.city_x_position < minX:
                minX = city.city_x_position
            if minY is None or city.city_y_position < minY:
                minY = city.city_y_position
            if maxX is None or city.city_x_position + city.city_x_size > maxX:
                maxX = city.city_x_position + city.city_x_size
            if maxY is None or city.city_y_position + city.city_y_size > maxY:
                maxY = city.city_y_position + city.city_y_size
        sizeX = maxX - minX
        sizeY = maxY - minY
        config = self.config.crop((minX, minY, maxX, maxY))
        logger.info("crop size", minX, minY, maxX, maxY, sizeX, sizeY)
        return minX, minY, maxX, maxY, sizeX, sizeY, config

    def BuildConfig(self):
        """Build a nice config.bmp with slight colors changes, also fill the missingCities"""
        sizeX = sizeY = 0
        bigs = []
        smalls = []
        mediums = []
        for city in self.all_cities:
            if city.city_x_size == 4:
                bigs.append((city.city_x_position, city.city_y_position))
            if city.city_x_size == 2:
                mediums.append((city.city_x_position, city.city_y_position))
            if city.city_x_size == 1:
                smalls.append((city.city_x_position, city.city_y_position))
            if city.city_x_position + city.city_x_size > sizeX:
                sizeX = city.city_x_position + city.city_x_size
            if city.city_y_position + city.city_y_size > sizeY:
                sizeY = city.city_y_position + city.city_y_size
        if self.original_config:
            sizeX = self.original_config.size[0]
            sizeY = self.original_config.size[1]
        config = Image.new("RGB", (sizeX, sizeY))
        draw = ImageDraw.Draw(config)
        for c in smalls:
            reds = ("#FF7777", "#FF0000")
            color = c[0] + c[1]
            draw.rectangle([c, (c[0], c[1])], fill=reds[color % 2])
        for c in mediums:
            colors = ("#00FF00", "#99FF00", "#00FF99", "#55FF55")
            color = c[0] + c[1]
            draw.rectangle([c, (c[0] + 1, c[1] + 1)], fill=colors[color % 4])
        for c in bigs:
            colors = (
                "#0000FF",
                "#4000FF",
                "#8000FF",
                "#C000FF",
                "#0040FF",
                "#4040FF",
                "#8040FF",
                "#C040FF",
                "#0080FF",
                "#4080FF",
                "#8080FF",
                "#C080FF",
                "#00C0FF",
                "#40C0FF",
                "#80C0FF",
                "#C0C0FF",
            )
            color = c[0] + c[1]
            draw.rectangle([c, (c[0] + 3, c[1] + 3)], fill=colors[color % 16])
        self.missingCities = []
        for y in range(sizeY):
            for x in range(sizeX):
                if self.GetCityUnder((x, y)) is None:
                    self.missingCities.append((x, y))
        return config

    def DeleteCityAt(self, pos):
        "find the city at a certain x,y and remove it"
        for i, city in enumerate(self.all_cities):
            if (
                pos[0] >= city.city_x_position
                and pos[0] < city.city_x_position + city.city_x_size
                and pos[1] >= city.city_y_position
                and pos[1] < city.city_y_position + city.city_y_size
            ):
                self.all_cities = self.all_cities[:i] + self.all_cities[i + 1 :]
                break

    def GetCityUnder(self, pos):
        "find the city at a certain x,y"
        for city in self.all_cities:
            if (
                pos[0] >= city.city_x_position
                and pos[0] < city.city_x_position + city.city_x_size
                and pos[1] >= city.city_y_position
                and pos[1] < city.city_y_position + city.city_y_size
            ):
                return city
        return None

    def GetCitiesUnder(self, pos, size):
        "find all cities under rect"
        cities = []
        for city in self.all_cities:

            def collide(x1, y1, w1, h1, x2, y2, w2, h2):
                return not (
                    x1 >= x2 + w2 or x1 + w1 <= x2 or y1 >= y2 + h2 or y1 + h1 <= y2
                )

            if collide(
                pos[0],
                pos[1],
                size,
                size,
                city.city_x_position,
                city.city_y_position,
                city.city_x_size,
                city.city_y_size,
            ):
                cities.append(city)
        return cities

    def is_valid(self):
        "the region is valid if there is at least one city or the config.bmp is ok"
        return len(self.all_cities) > 0 or self.config is not None

    def Save(self, dlg, minX, minY, subRgn):
        "save the region to SC4File"
        logger.info("saving")
        saved = True
        for i, city in enumerate(self.all_cities):
            dlg.Update(
                i,
                "Please wait while saving the region"
                + "\nSaving "
                + " City - New city(%03d-%03d).sc4"
                % (city.city_x_position, city.city_y_position),
            )
            citySave = CityProxy(
                self.waterLevel,
                city.city_x_position - minX,
                city.city_y_position - minY,
                city.city_x_size,
                city.city_y_size,
            )
            citySave.heightMap = Numeric.zeros(
                (citySave.ySize, citySave.xSize), Numeric.uint16
            )
            citySave.heightMap[::, ::] = self.height[
                citySave.yPos + subRgn[1] : citySave.yPos + subRgn[1] + citySave.ySize,
                citySave.xPos + subRgn[0] : citySave.xPos + subRgn[0] + citySave.xSize,
            ]
            citySave.heightMap = citySave.heightMap.astype(
                Numeric.float32
            ) / Numeric.asarray(10, Numeric.float32)
            x1 = citySave.xPos
            y1 = citySave.yPos
            x2 = x1 + citySave.xSize
            y2 = y1 + citySave.ySize
            logger.info(x1, y1, x2, y2)
            logger.info(
                citySave.yPos + subRgn[2],
                "to",
                citySave.yPos + subRgn[2] + citySave.ySize,
                "and",
                citySave.xPos + subRgn[0],
                "to",
                citySave.xPos + subRgn[0] + citySave.xSize,
            )
            lightDir = normalize((1, -5, -1))
            rawRGB = tools3D.onePassColors(
                False,
                citySave.heightMap.shape,
                self.waterLevel,
                citySave.heightMap,
                GRADIENT_READER.paletteWater,
                GRADIENT_READER.paletteLand,
                lightDir,
            )
            logger.info(citySave.heightMap.shape, len(rawRGB))
            try:
                if not Save(citySave, self.folder, rawRGB, self.waterLevel):
                    saved = False
            except Exception as exc:
                logger.exception(exc)
                logger.debug(
                    (
                        "problem while saving:\n"
                        f"{citySave.fileName} {city.city_x_position}, {city.city_y_position}"
                        f"{city.city_x_size}, {city.city_y_size}"
                    )
                )
                saved = False
            citySave.heightMap = None
        return saved

    def show(self, dlg, readFiles=False):
        "compute size/shape and load the heightmap if readFiles is True"
        imgSize = [0, 0]
        if self.config:
            imgSize[0] = self.config.size[0]
            imgSize[1] = self.config.size[1]

        for city in self.all_cities:
            x = city.city_x_position + city.city_x_size
            y = city.city_y_position + city.city_y_size
            if imgSize[0] < x:
                imgSize[0] = x
            if imgSize[1] < y:
                imgSize[1] = y

        self.imgSize = [a * 64 + 1 for a in imgSize]
        self.shape = [self.imgSize[1], self.imgSize[0]]

        if readFiles is False:
            return

        dlg.Update(2, "Please wait while loading the region\nBuilding textures")
        self.height = Numeric.zeros(self.shape, Numeric.uint16)
        for city in self.all_cities:
            if hasattr(city, "heightMapEntry"):
                self.height[
                    city.yPos : city.yPos + city.ySize,
                    city.xPos : city.xPos + city.xSize,
                ] = Numeric.reshape(
                    (
                        Numeric.fromstring(
                            city.heightMapEntry.content[2:], Numeric.float32
                        )
                        * Numeric.array(10, Numeric.float32)
                    ).astype(Numeric.uint16),
                    (city.ySize, city.xSize),
                )
                del city.heightMapEntry
            else:
                self.height[
                    city.yPos : city.yPos + city.ySize,
                    city.xPos : city.xPos + city.xSize,
                ] = Numeric.ones(
                    (city.ySize, city.xSize), Numeric.uint16
                ) * Numeric.array(self.waterLevel - 50).astype(Numeric.uint16)
            city.height = None
        dlg.Update(2, "Please wait while loading the region\nBuilding textures")
        logger.info("region read")
