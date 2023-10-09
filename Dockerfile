FROM python:3.11-slim as build_temp

WORKDIR /app

ADD ./requirements.txt /app

RUN apt update \
    && apt install -y --no-install-recommends \
        build-essential\
        libgtk-3-dev\
    && pip install -r requirements.txt --no-cache-dir \
    && apt purge -y \
        build-essential\
        libgtk-3-dev\
    && apt clean all \
    && rm -rf /var/lib/apt/lists/*

CMD /bin/bash
