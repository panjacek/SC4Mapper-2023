from distutils.core import Extension, setup

setup(
    name="tools3D",
    version="1.0",
    description="sc4 mapper tools3D",
    ext_modules=[Extension("tools3D", ["tools3D.cpp"])],
)
