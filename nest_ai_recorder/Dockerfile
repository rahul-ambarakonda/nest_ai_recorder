ARG BUILD_FROM
FROM $BUILD_FROM

ARG REPO_URL=https://github.com/rahul-ambarakonda/nest_ai_recorder.git
ARG REPO_REF=main

RUN apk add --no-cache ffmpeg python3 py3-pip git \
    && pip3 install --break-system-packages --no-cache-dir \
        "nest-ai-recorder[mqtt,ai] @ git+${REPO_URL}@${REPO_REF}"

COPY run.sh /run.sh
RUN chmod a+x /run.sh

CMD ["/run.sh"]
