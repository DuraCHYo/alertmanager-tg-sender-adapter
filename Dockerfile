FROM ghcr.io/astral-sh/uv:alpine3.23

RUN addgroup -S appgroup && \
    adduser -S -G appgroup -h /app uvnonroot

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./

RUN chown -R uvnonroot:appgroup /app

USER uvnonroot:appgroup

RUN uv sync --frozen --no-install-project

COPY --chown=uvnonroot:appgroup . .

ENTRYPOINT ["uv", "run", "alertmanager_tg_sender_adapter"]