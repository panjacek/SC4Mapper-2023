"""this will read gradients files for coloring the landscape"""

import configparser
import logging

logger = logging.getLogger(__name__)


class GradientReader:
    def __init__(self, fileName):
        self.paletteWater = {}
        self.paletteLand = {}
        self.bgColor = (0, 128, 255)

        self.bgColor, self.paletteWater, self.paletteLand = self.ReadGradientConfig(fileName)
        logger.info(f"{self.bgColor}, {self.paletteWater}, {self.paletteLand}")

    def HTMLColorToRGB(self, colorstring):
        """convert #RRGGBB to an (R, G, B) tuple"""
        colorstring = colorstring.strip()
        if colorstring[0] == "#":
            colorstring = colorstring[1:]
        if len(colorstring) != 6:
            raise ValueError(f"input #{colorstring} is not in #RRGGBB format")
        r, g, b = colorstring[:2], colorstring[2:4], colorstring[4:]
        r, g, b = [int(n, 16) for n in (r, g, b)]
        return (r, g, b)

    def ReadGradientConfig(self, fileName):
        try:
            cp = configparser.ConfigParser()
            cp.read(fileName)
            values = cp.items("background")
            values = [(0, self.HTMLColorToRGB(v[1])) for v in values]
            values.sort(key=lambda x: x[0])
            bgColor = {}
            for v in values:
                bgColor[v[0]] = v[1]

            values = cp.items("land")
            values = [(int(v[0]), self.HTMLColorToRGB(v[1])) for v in values]
            values.sort(key=lambda x: x[0])
            paletteLand = {}
            for v in values:
                paletteLand[v[0]] = v[1]
            values = cp.items("water")
            values = [(int(v[0]), self.HTMLColorToRGB(v[1])) for v in values]
            values.sort(key=lambda x: x[0])
            paletteWater = {}
            for v in values:
                paletteWater[v[0]] = v[1]
            logger.info(paletteWater)
            logger.info(paletteLand)
            return bgColor[0], paletteWater, paletteLand
        except Exception as exc:
            logger.warning(exc)
            return (
                (0, 128, 255),
                {0: (123, 189, 214), 200: (0, 8, 74)},
                {0: (123, 189, 214), 100: (0, 206, 0), 1000: (255, 255, 255)},
            )
