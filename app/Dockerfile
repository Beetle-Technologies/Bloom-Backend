FROM python:3.13.3-slim

WORKDIR /app/

RUN apt-get update && apt-get install -y \
    curl \
    bash \
    gcc \
    build-essential \
    gettext \
    musl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#installing-uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Compile bytecode
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#compiling-bytecode
ENV UV_COMPILE_BYTECODE=1

RUN uv venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH=/app/
ENV PYTHONUNBUFFERED=1

# uv Cache
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#caching
ENV UV_LINK_MODE=copy

# Install dependencies using uv
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --active

COPY ./pyproject.toml /app/
COPY ./uv.lock /app/
COPY ./scripts/ /app/scripts/

RUN chmod +x /app/scripts/*.sh

COPY ./alembic /app/alembic/
COPY ./static /app/static/
COPY ./templates /app/templates/
COPY ./alembic.ini /app/
COPY ./tests /app/tests/
COPY ./src /app/src/

# Sync the project
# Ref: https://docs.astral.sh/uv/guides/integration/docker/#intermediate-layers
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

RUN chown -R nobody:nogroup /app

RUN chmod -R 755 /app
