ARG BUILD_FROM
FROM $BUILD_FROM

RUN apk add --no-cache ffmpeg python3 py3-pip

WORKDIR /app

COPY pyproject.toml README.md requirements.txt ./
COPY src ./src
RUN pip3 install --break-system-packages --no-cache-dir -r requirements.txt \
    && pip3 install --break-system-packages --no-cache-dir .

COPY addon/run.sh /run.sh
RUN chmod a+x /run.sh

CMD ["/run.sh"]

