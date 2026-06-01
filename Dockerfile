FROM ghcr.io/astral-sh/uv:0.11.17-python3.13-trixie

RUN groupadd --system appgroup && \
    useradd --system --gid appgroup --home-dir /app --create-home uvnonroot

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY alertmanager_tg_sender_adapter ./alertmanager_tg_sender_adapter

RUN chown -R uvnonroot:appgroup /app
USER uvnonroot:appgroup

RUN uv sync --frozen

ENTRYPOINT ["/app/.venv/bin/alertmanager_tg_sender_adapter"]
