FROM ghcr.io/astral-sh/uv:alpine3.23

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./

RUN uv sync --frozen --no-install-project

COPY . .

CMD ["uv", "run", "parser"]