FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV UV_NO_CACHE=1
ENV PYTHONPATH=/app

WORKDIR /app

COPY pyproject.toml .
RUN uv sync --no-dev

COPY bot/ ./bot/

CMD ["uv", "run", "python", "-m", "bot.main"]