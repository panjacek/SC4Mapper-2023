SC4Mapper-2013
==============

![ZIP](http://imageshack.us/a/img803/7351/screenshot060r.jpg)
SC4 Region import/export tool

# FIXME dead link
check [SC4Devotion](http://sc4devotion.com/forums/index.php?topic=15455.0) for more informations, might need registration

and [LEX](http://sc4devotion.com/csxlex/lex_filedesc.php?lotGET=2880) to get Windows executable
 
Executables files need to be uploaded on the [LEX](http://sc4devotion.com/csxlex/) at [SC4Devotion](http://www.sc4devotion.com)


# FIXME old stuff py2
Requierements
=============
- [python 3.6](http://www.python.org)
- [Numpy 1.6.2](http://sourceforge.net/project/showfiles.php?group_id=1369&package_id=175103) or higher
- [PIL 1.1.7](http://www.pythonware.com/products/pil/) or higher
- [pywin32 218](http://sourceforge.net/projects/pywin32/) or higher
- [wxPython 2.9.4](http://www.wxpython.org/download.php#unstable) or higher


Running in Docker
=================

```
export XSOCK=/tmp/.X11-unix
export XAUTH=/tmp/.docker.xauth
xauth nlist ${DISPLAY} | sed -e 's/^..../ffff/' | xauth -f $XAUTH nmerge -
docker run -ti -v $XSOCK:$XSOCK -v $XAUTH:$XAUTH -e XAUTHORITY=$XAUTH sc4_mapper

pip3 install -e Modules/qfs
pip3 install -e Modules/tools3D
pip3 install -e .

```

clean stdout from gtk errors via
```
SC4App 2>&1 | grep -v "Gtk-WARNING\|dconf-WARNING\|^$"
```

Contributors
============
- Wouanagaine
- JoeST
