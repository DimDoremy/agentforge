# agentforge agent service image — multi-stage (dev / prod).
#
# Python 3.12 is the safe LangGraph target (3.14 is too new for some wheels).
# uv manages deps; prod uses --frozen for reproducibility, dev adds the dev
# extras and relies on a source bind-mount for hot reload.

ARG PYTHON_VERSION=3.12

# ---------------------------------------------------------------------------
# base: install uv
# ---------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim AS base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH=/app/.venv/bin:$PATH
WORKDIR /app
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential libpq-dev curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:0.11.28 /uv /usr/local/bin/uv

# ---------------------------------------------------------------------------
# prod: locked deps, no dev extras, no source mount
# ---------------------------------------------------------------------------
FROM base AS prod
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev --no-install-project
COPY src ./src
COPY langgraph.json ./
COPY docker ./docker
ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["langgraph", "up", "--host", "0.0.0.0", "--port", "8000"]

# ---------------------------------------------------------------------------
# dev: full deps incl. dev extras; source is bind-mounted at runtime
# ---------------------------------------------------------------------------
FROM base AS dev
COPY pyproject.toml uv.lock* ./
RUN uv sync --all-extras --no-install-project
ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["uv", "run", "langgraph", "dev", "--host", "0.0.0.0", "--port", "8000", "--no-browser"]
