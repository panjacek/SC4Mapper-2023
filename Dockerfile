FROM debian:trixie-slim

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies via apt
# Note: python3-pip is now strictly managed (PEP 668). 
# Using --break-system-packages may be needed for pip installs later.
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
    libgl1 \
    libglu1-mesa \
    libsdl2-2.0-0 \
    libnotify4 \
    libxtst6 \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -m -u 1000 sc4user

WORKDIR /app
RUN chown sc4user:sc4user /app

# Copy source
COPY --chown=sc4user:sc4user . .

# Build C extensions (QFS and tools3D)
RUN mkdir -p /opt/libs && chown sc4user:sc4user /opt/libs
RUN make -C Modules && \
    cp Modules/*.so /opt/libs/

# Set environment
ENV PYTHONPATH=/app:/opt/libs
ENV DISPLAY=:0

USER sc4user

# Default command to run the app
ENTRYPOINT ["python3", "-m", "sc4_mapper.SC4MapApp"]
