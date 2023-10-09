from setuptools import find_packages, setup

setup(
    name="SC4Mapper-2013",
    version="2.0.0",
    # url="https://github.com/mypackage.git",
    # author="Author Name",
    # author_email="author@gmail.com",
    description="Description of my package",
    packages=find_packages(),
    package_data={
        "SC4Mapper-2013.QFS": ["qfs.pyd"],
        "SC4Mapper-2013.tools3D": ["tools3D.pyd"],
        "": ["static/*"],
    },
    include_package_data=True,
    zip_safe=False,
)
