FROM ghcr.io/astral-sh/uv:alpine3.23

RUN addgroup -S appgroup && \
    adduser -S -G appgroup -h /app uvnonroot

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY alertmanager_tg_sender_adapter ./alertmanager_tg_sender_adapter

RUN chown -R uvnonroot:appgroup /app
USER uvnonroot:appgroup

RUN uv sync --frozen

ENTRYPOINT ["/app/.venv/bin/alertmanager_tg_sender_adapter"]