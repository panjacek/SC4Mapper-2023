PYTHON_INCLUDE_DIR = $(shell python3-config --includes)
PYTHON_LIBS = $(shell python3-config --libs --embed)
CC = gcc
CXX = g++
CFLAGS = -Wall -O2 -fPIC -shared
INCLUDE = $(PYTHON_INCLUDE_DIR)
LIBS = $(PYTHON_LIBS)

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
