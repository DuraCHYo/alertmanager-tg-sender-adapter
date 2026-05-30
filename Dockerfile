FROM ghcr.io/astral-sh/uv:alpine3.23

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --no-install-project

COPY . .

RUN uv lock

CMD ["uv", "run", "parser"]