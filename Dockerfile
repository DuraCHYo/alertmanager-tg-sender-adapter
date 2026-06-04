FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY alertmanager_tg_sender_adapter ./alertmanager_tg_sender_adapter

RUN uv sync --frozen && \
    .venv/bin/playwright install-deps chromium

RUN groupadd --system appgroup && \
    useradd --system --gid appgroup --home-dir /app --create-home uvnonroot

RUN chown -R uvnonroot:appgroup /app

USER uvnonroot:appgroup

RUN .venv/bin/playwright install chromium

ENTRYPOINT ["/app/.venv/bin/alertmanager-tg-sender-adapter"]