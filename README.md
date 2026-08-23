# SC4Mapper-2013 (remix)

Remix of the original [SC4Mapper-2013](https://github.com/wouanagaine/SC4Mapper-2013).

SimCity 4 region import/export tool. Goals of this fork:

- **Python 3.11+** port of the original Python 2 codebase
- **Dockerized**: consistent, containerized environment for GUI + CI
- **Fast local test loop** via [uv](https://docs.astral.sh/uv/) (no docker, no wx)

[![CI](https://github.com/panjacek/SC4Mapper-2023/actions/workflows/ci.yml/badge.svg)](https://github.com/panjacek/SC4Mapper-2023/actions/workflows/ci.yml)

## Quick start

```bash
make build          # build sc4mapper:latest image
docker compose up   # run the app
```

Run `make help` for all targets. `make sync` upgrades dependencies, re-locks
and refreshes the venv.

## Development

### Fast local loop (uv)

Runs `core/` tests only — no docker, no wx needed. UI tests auto-skip.

```bash
make lint-local    # ruff check via uv
make test-local    # uv venv + pytest (~5s; rebuilds QFS/tools3D against venv python)
```

Requires `uv` and `gcc`.

### Full loop (Docker)

```bash
make build         # slim runtime image (sc4mapper:latest, multi-stage)
make build-test    # test image on top (implies make build)
make lint          # ruff check
make format        # ruff format + clang-format C sources
make format-check  # CI gate: format check only
make test          # all tests incl. UI, inside Docker
```

> [!NOTE]
> Region tests require fixture data in `region_tests/` (untracked):
> e.g. `San Francisco/`, `Jakarta.SC4M`. Without it those cases skip silently.

## Structure

```
sc4_mapper/
├── SC4MapApp.py     # entry: python3 -m sc4_mapper.SC4MapApp (or `sc4mapper`)
├── splash_screen.py
├── core/            # format lib + utilities — no wx imports
│   ├── rgnReader.py       # DBPF/SC4 region read/write
│   └── zipUtils.py, utils.py, helpers.py, gradient_reader.py
└── ui/              # all wxPython code
    ├── overview.py        # main window
    ├── canvas.py          # rendering
    ├── region_handler.py  # save/export orchestration
    ├── region_from_file.py# .SC4M / image import handlers
    └── about.py, QuestionDialog.py
```

C extensions live in `Modules/` (`QFS.so` compression, `tools3D.so`) —
built by `make modules`, loaded at runtime.

## Requirements

- Runtime (GUI): Python 3.11+, numpy, Pillow, wxPython — all provided by the Docker image
- Local testing: [uv](https://docs.astral.sh/uv/), gcc

## Legacy bare-metal usage notes and packaging scripts were removed from the repo
(still reachable in git history).

## Contributors

- Wouanagaine
- JoeST
- panjacek
