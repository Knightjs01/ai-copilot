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
RUN poetry install --no-root --only main

COPY . .

EXPOSE 8000

CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
