.PHONY: format modules install install-dev uninstall build build-test test

lint:
	docker run --rm -t -e RUFF_COLOR=always -v $(shell pwd):/app --entrypoint ruff sc4mapper-test:latest check .

format:
	docker run --rm -t -e RUFF_COLOR=always -v $(shell pwd):/app --entrypoint ruff sc4mapper-test:latest format .
	docker run --rm -t -e RUFF_COLOR=always -v $(shell pwd):/app --entrypoint ruff sc4mapper-test:latest check --fix .
	docker run --rm -t -v $(shell pwd):/app --entrypoint clang-format sc4mapper-test:latest -i Modules/qfs/qfs.c Modules/tools3D/tools3D.cpp

modules:
	$(MAKE) -C Modules

clean-modules:
	$(MAKE) -C Modules clean

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
	docker run --rm -t \
		-v $(shell pwd)/tests:/app/tests \
		-v $(shell pwd)/region_tests:/app/region_tests \
		-v $(shell pwd)/sc4_mapper:/app/sc4_mapper \
		sc4mapper-test:latest

restart-app:
	docker compose down -t0
	docker compose up