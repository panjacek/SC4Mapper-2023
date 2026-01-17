FROM python:3.13-slim AS wx_base

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

ARG WXPYTHON_WHEEL_NAME=wxPython-4.2.2-cp313-cp313-linux_x86_64.whl
ARG WXPYTHON_WHEEL_URL=https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-24.04/${WXPYTHON_WHEEL_NAME}


RUN apt update \
    && apt install -y --no-install-recommends \
        make \
        wget \
    && wget ${WXPYTHON_WHEEL_URL} \
    && pip install --user --no-cache-dir ${WXPYTHON_WHEEL_NAME} \
    && rm -rf ${WXPYTHON_WHEEL_NAME} \
    && apt clean \
    && rm -rf /var/lib/apt/lists/*


FROM python:3.13-slim AS app
COPY --from=wx_base /root/.local /root/.local
COPY --from=wx_base /usr/bin/make /usr/bin/make

WORKDIR /app

ADD ./requirements.txt /app

RUN pip install -r requirements.txt --no-cache-dir

CMD /bin/bash
