FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# 1) Сначала только зависимости — этот слой кэшируется, пока не меняется uv.lock
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --locked --no-dev --no-install-project

# 2) Потом код — меняется часто, пересобирается только этот слой
COPY src ./src
COPY migrations ./migrations
COPY README.md ./
RUN uv sync --locked --no-dev

# Версия образа: CI передаёт сюда git-тег (v1.2.3) или sha коммита
ARG APP_VERSION=dev
ENV APP_VERSION=${APP_VERSION}

RUN useradd --create-home app
USER app

EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

CMD ["uvicorn", "guestbook.main:app", "--host", "0.0.0.0", "--port", "8000"]
