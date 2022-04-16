#
# Base
#
FROM python:3.9-slim AS base

RUN apt-get update && apt-get install -y curl

ENV PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_VIRTUALENVS_IN-PROJECT=false \
    POETRY_HOME=/usr/local/src/poetry
ENV PATH="${POETRY_HOME}/bin:$PATH"

COPY pyproject.toml poetry.lock ./

RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
RUN poetry install --no-interaction --no-ansi

#
# App
#
FROM base
WORKDIR /app

COPY . .

ENTRYPOINT [ "python", "app.py"]
