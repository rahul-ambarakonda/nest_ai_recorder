ARG BUILD_FROM
FROM $BUILD_FROM

ARG REPO_URL=https://github.com/rahul-ambarakonda/nest_ai_recorder.git
ARG REPO_REF=main

# YOLO/Ultralytics does not build reliably on Alpine aarch64 (Raspberry Pi).
# Install OpenCV from Alpine packages and use motion-based detection instead.
RUN apk add --no-cache \
    ffmpeg \
    python3 \
    py3-pip \
    git \
    py3-numpy \
    py3-opencv \
    py3-pillow

WORKDIR /tmp/build
RUN git clone --depth 1 --branch "${REPO_REF}" "${REPO_URL}" . \
    && pip3 install --break-system-packages --no-cache-dir ".[mqtt]" \
    && cd / \
    && rm -rf /tmp/build

COPY run.sh /run.sh
RUN chmod a+x /run.sh

CMD ["/run.sh"]
