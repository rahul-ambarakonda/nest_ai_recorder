FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md requirements.txt ./
COPY src ./src

RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir .

VOLUME ["/config", "/media"]

ENV NEST_AI_RECORDER_CONFIG=/config/config.yaml

CMD ["nest-ai-recorder", "run"]

