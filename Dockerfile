# syntax=docker/dockerfile:1

# Shared ancestor: distro + env only.
FROM debian:trixie-slim AS base
ENV DEBIAN_FRONTEND=noninteractive

# ---- Runtime dependency set: downloaded exactly ONCE, inherited below ----
FROM base AS deps
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-wxgtk4.0 \
    libgtk-3-0 \
    libgl1 \
    libglu1-mesa \
    libsdl2-2.0-0 \
    libnotify4 \
    libxtst6 \
    ca-certificates

# ---- Toolchain: deps + compilers, discarded after .so extraction ----
FROM deps AS build
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
    python3-dev \
    build-essential \
    make

WORKDIR /build
COPY Modules/ ./Modules/
RUN make -C Modules

# ---- Slim runtime: deps only (no compilers), .so copied from build ----
FROM deps AS runtime

RUN useradd -m -u 1000 sc4user

WORKDIR /app
RUN chown sc4user:sc4user /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Deps from uv.lock — identical versions to local dev. wxPython is the lone
# exception (no Linux wheels) and comes from apt above.
COPY pyproject.toml uv.lock .python-version ./
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
# System python must stay in lockstep with python3-dev in the build stage
# (extension ABI). Bump both together.
ENV UV_PYTHON=/usr/bin/python3
RUN --mount=type=cache,target=/root/.cache/uv,sharing=locked \
    uv sync --frozen --no-dev --no-install-package wxpython --no-editable

COPY --from=build /build/Modules/*.so /opt/libs/
COPY --chown=sc4user:sc4user . .

ENV PATH=/opt/venv/bin:/usr/local/bin:/usr/bin:/bin
# venv is isolated -> apt wx lives in dist-packages; QFS/tools3D in /opt/libs
ENV PYTHONPATH=/usr/lib/python3/dist-packages:/app:/opt/libs
ENV DISPLAY=:0

USER sc4user

ENTRYPOINT ["python3", "-m", "sc4_mapper.SC4MapApp"]
