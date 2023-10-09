SC4Mapper-2023
==============

This is a remix of the original [SC4Mapper-2013](https://github.com/wouanagaine/SC4Mapper-2013).

The goals of this fork are:
- **Dockerization**: Run SC4Mapper in a consistent, containerized environment.
- **Python 3 Compatibility**: Port the original Python 2 codebase to modern Python 3.11+.

SC4 Region import/export tool.
```bash
make build
docker compose up
```

Requirements
============
- Python 3.11+
- [Numpy](https://numpy.org/) 2.4.1
- [Pillow](https://python-pillow.org/) 12.1.0
- [wxPython](https://www.wxpython.org/) 4.2.0 (from Debian bookworm)

Development
===========

Developing with Docker is the recommended approach.

### Build and Run
```bash
# This section is now redundant as the build/run instructions are at the top.
# make build
# docker compose up
```

### Testing and Quality Control
```bash
# Rebuild test environment
make build-test

# Run linting (Ruff)
make lint

# Run all tests
make test

# Format code
make format
```

> [!NOTE]
> Running tests requires existing SC4 sample regions and/or `.SC4M` files in the `region_tests/` directory (e.g., `San Francisco`, `Jakarta.SC4M`).

### Manual Usage (Legacy)
```bash
# clean stdout from gtk errors via
SC4App 2>&1 | grep -v "Gtk-WARNING\|dconf-WARNING\|^$"
```

Contributors
============
- Wouanagaine
- JoeST
- panjacek