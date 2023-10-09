from distutils.core import Extension, setup

setup(
    name="QFS",
    version="1.0",
    description="Package for QFS compression and decompression",
    ext_modules=[Extension("QFS", ["qfs.c"])],
)
