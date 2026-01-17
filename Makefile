.PHONY: format modules install install-dev uninstall build build-test test

format:
	isort .
	black .

modules:
	$(MAKE) -C Modules

install:
	pip3 install Modules/qfs
	pip3 install Modules/tools3D
	pip3 install .

install-dev:
	pip3 install -e Modules/qfs
	pip3 install -e Modules/tools3D
	pip3 install -e .

uninstall:
	pip3 uninstall -y QFS tools3D SC4Mapper-2013

build:
	docker build -t sc4mapper:latest .

build-test: build
	docker build -t sc4mapper-test:latest -f Dockerfile.test .

test:
	docker run --rm -t sc4mapper-test:latest
