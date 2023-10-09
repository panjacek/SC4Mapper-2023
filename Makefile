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
