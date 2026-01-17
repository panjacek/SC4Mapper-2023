# Clean Dockerfile for SC4Mapper-2013 using Debian system packages
FROM debian:bookworm-slim

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies via apt for stability
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-wxgtk4.0 \
    python3-numpy \
    python3-pil \
    build-essential \
    python3-dev \
    make \
    libgtk-3-0 \
    libgl1-mesa-glx \
    libglu1-mesa \
    libsdl2-2.0-0 \
    libnotify4 \
    libxtst6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy source
COPY . .

# Build C extensions (QFS and tools3D)
RUN make -C Modules && \
    mkdir -p /opt/libs && \
    cp Modules/*.so /opt/libs/

# Set environment
ENV PYTHONPATH=/app:/opt/libs
ENV DISPLAY=:0

# Default command to run the app
ENTRYPOINT ["python3", "-m", "sc4_mapper.SC4MapApp"]
