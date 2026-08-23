.PHONY: help format format-check modules clean-modules clean install install-dev uninstall build build-test test lint-local test-local sync restart-app

help: ## show this help
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

format: ## ruff format + clang-format C sources (docker)
	docker run --rm -e RUFF_COLOR=always -v $(shell pwd):/app --entrypoint ruff sc4mapper-test:latest format .
	docker run --rm -e RUFF_COLOR=always -v $(shell pwd):/app --entrypoint ruff sc4mapper-test:latest check --fix .
	docker run --rm -v $(shell pwd):/app --entrypoint clang-format sc4mapper-test:latest -i Modules/qfs/qfs.c Modules/tools3D/tools3D.cpp

format-check: ## ruff format --check only (CI gate, no mutation)
	uv sync --group dev --no-install-package wxpython
	uv run --no-sync ruff format --check .

modules: ## build QFS.so / tools3D.so into Modules/
	$(MAKE) -C Modules

clean-modules: ## remove built C extensions
	$(MAKE) -C Modules clean

clean: clean-modules ## remove local build/test artifacts (keeps .venv)
	rm -rf .pytest_cache .ruff_cache .coverage \
	       SC4Mapper_2013.egg-info sc4_mapper.egg-info
	find . -name "__pycache__" -type d -prune -exec rm -rf {} +
	find . -name "*.pyc" -delete
	rm -f sc4_mapper/*.so sc4_mapper/*.pyd

install: ## bare-metal install: C extensions + package via pip3
	pip3 install Modules/qfs
	pip3 install Modules/tools3D
	pip3 install .

install-dev: ## editable install for local dev
	pip3 install -e Modules/qfs
	pip3 install -e Modules/tools3D
	pip3 install -e .

uninstall: ## remove installed packages
	pip3 uninstall -y QFS tools3D SC4Mapper-2013

# CI sets this for buildx GHA layer caching (--load required: container-driver builder)
BUILD_CACHE ?=

build: ## build runtime (sc4mapper) + tag builder stage (sc4mapper-build, prune-safe)
	docker build --target runtime -t sc4mapper:latest $(BUILD_CACHE) .
	docker build --target build -t sc4mapper-build:latest $(BUILD_CACHE) .

build-test: build ## add test tools on top -> sc4mapper-test:latest
	docker build $(BUILD_CACHE) -t sc4mapper-test:latest -f Dockerfile.test .

test: ## all tests incl. UI, needs region_tests/ fixtures
	docker run --rm \
		-v $(shell pwd)/tests:/app/tests \
		-v $(shell pwd)/region_tests:/app/region_tests \
		-v $(shell pwd)/sc4_mapper:/app/sc4_mapper \
		sc4mapper-test:latest

restart-app: ## restart GUI container
	docker compose down -t0
	docker compose up

lint-local: ## fast ruff via uv (no docker)
	uv sync --group dev --no-install-package wxpython
	uv run --no-sync ruff check .

# venv interpreter — recursive so it resolves after uv sync has run
VENV_PYTHON = $(shell uv run --no-sync python -c 'import sys; print(sys.executable)')

# CI overrides for coverage reporting; local default stays quiet/fast
PYTEST_ARGS ?= --no-cov -q

test-local: ## fast pytest via uv — core tests only, UI auto-skipped
	uv sync --group dev --no-install-package wxpython
	$(MAKE) -C Modules PYTHON=$(VENV_PYTHON)
	PYTHONPATH=$(shell pwd)/Modules uv run --no-sync pytest tests $(PYTEST_ARGS)

sync: ## upgrade deps, re-lock, refresh venv
	uv lock --upgrade
	uv sync --group dev --no-install-package wxpython
