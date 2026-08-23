# Interpreter whose ABI the extensions are built for. Override to match a
# venv (e.g. make PYTHON=/path/to/venv/bin/python) or extensions won't import.
# Includes come from the interpreter itself (no *-config dependency), and we
# deliberately do NOT link -lpython: extensions resolve Py* symbols from the
# importing interpreter, so they run against any matching-ABI python.
PYTHON ?= python3
INCLUDE = $(shell $(PYTHON) -c "import sysconfig; print('-I' + sysconfig.get_paths()['include'])")
CC = gcc
CXX = g++
CFLAGS = -Wall -O2 -fPIC -shared
LIBS =

# On Linux, shared objects should have .so extension
EXT = .so

all: QFS tools3D

.PHONY: QFS tools3D
QFS:
	$(CC) $(CFLAGS) $(INCLUDE) -o QFS$(EXT) qfs/qfs.c $(LIBS)

tools3D:
	$(CXX) $(CFLAGS) $(INCLUDE) -o tools3D$(EXT) tools3D/tools3D.cpp $(LIBS)
	
install: QFS tools3D
	cp tools3D$(EXT) ../sc4_mapper/
	cp QFS$(EXT) ../sc4_mapper/

clean:
	rm -f *$(EXT) *.pyd
