ARG BUILD_FROM
FROM $BUILD_FROM

RUN apk add --no-cache \
    ffmpeg \
    python3 \
    py3-pip \
    py3-numpy \
    py3-opencv \
    py3-pillow

WORKDIR /tmp/app
COPY app /tmp/app

RUN pip3 install --break-system-packages --no-cache-dir ".[mqtt]"

COPY run.sh /run.sh
RUN chmod a+x /run.sh

CMD ["/run.sh"]
