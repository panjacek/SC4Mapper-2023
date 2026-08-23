# AGENTS.md

Guidance for coding agents working in this repo.

**NEVER import inside a method/function — all imports go at module top.**
(Exception: the two legacy lazy `wx` imports in `core/rgnReader.py`; do not
add new ones.)

## Project

SC4Mapper — SimCity 4 region import/export tool. Python 3.11+ port of legacy
Python 2 app. wxPython GUI, two C extensions (QFS compression, tools3D).

## Commands

Fast local loop via uv (no docker, no wx — runs `core/` tests only):

```bash
make lint-local    # ruff check via uv
make test-local    # uv venv + pytest (core modules; UI tests auto-skipped)
```

Requires `uv` and `gcc` (`test-local` rebuilds QFS/tools3D against the venv python).
**Coverage caveat:** `test-local` runs the wx-free core only (~half the suite);
UI modules need real wx and are skipped with a warning. Full suite = `make test`
in Docker — run it before pushing.
Docker images install deps from `uv.lock` via uv too (only wxPython comes from
apt; it has no Linux wheels), so docker and local always run identical library
versions:

```bash
make build        # build sc4mapper:latest image
make build-test   # build test image (implies build)
make lint         # ruff check
make format       # ruff format + clang-format C sources
make test         # pytest inside Docker
make modules      # build QFS.so / tools3D.so locally
```

`make test` requires untracked fixture data in `region_tests/`
(e.g. `San Francisco/`, `Jakarta.SC4M`). Without it, region tests skip silently.

## Structure

```
sc4_mapper/
├── SC4MapApp.py     # entry point: python3 -m sc4_mapper.SC4MapApp (or `sc4mapper`)
├── splash_screen.py
├── core/            # format lib + utilities — NO wx imports allowed
│   ├── rgnReader.py       # DBPF/SC4 region format read/write
│   ├── zipUtils.py, utils.py, helpers.py, gradient_reader.py
└── ui/              # all wx code
    ├── overview.py (main window), canvas.py (rendering)
    ├── about.py, QuestionDialog.py
    └── region_from_file.py, region_handler.py
```

Note: `region_handler.py` and `region_from_file.py` live under `ui/` because
they are wx-coupled end-to-end. `core/rgnReader.py` contains two legacy
`wx.MessageDialog` calls flagged with FIXMEs ("move to ui module") — known
debt, do not add new ones.

Rules:
- New format/parsing code goes in `core/`, must not import wx.
- All UI code goes in `ui/`.
- Keep filenames stable; upstream project is frozen, we diverge deliberately.

## Conventions

- Line length 150 (ruff), double quotes.
- Tests mirror modules by name in top-level `tests/`.
- Legacy CamelCase APIs (e.g. `SaveBmp`, `ExportAsPNG`) are kept as-is.
