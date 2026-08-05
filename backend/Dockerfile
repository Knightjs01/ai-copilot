# syntax=docker/dockerfile:1

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_HOME=/opt/poetry

RUN pip install --no-cache-dir poetry==1.8.4
ENV PATH="/opt/poetry/bin:$PATH"

WORKDIR /app

COPY pyproject.toml poetry.lock* ./

FROM base AS dev
# Includes dev deps (pytest, ruff, ...) — this stage is what local docker-compose dev uses.
RUN poetry install --no-root
COPY . .
EXPOSE 8000
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base AS production
# Deployed image: no pytest/ruff/mypy/etc, main dependencies only.
RUN poetry install --no-root --only main
COPY . .
EXPOSE 8000
# Runs the migration on every container start before serving — correct and simple for a
# single-instance deployment (a startup migration race only matters with concurrent instances,
# which this deployment doesn't have). Binds to Railway's dynamic $PORT, falling back to 8000
# for any other environment that doesn't set it.
CMD poetry run alembic upgrade head && poetry run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
