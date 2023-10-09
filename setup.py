from setuptools import find_packages, setup

setup(
    name="SC4Mapper-2013",
    version="2.0.0",
    description="SC4 Region import/export tool",
    packages=find_packages(),
    package_data={
        "sc4_mapper": ["*.pyd", "*.so", "static/*"],
    },
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "numpy",
        "pillow",
        "wxPython",
    ],
)
