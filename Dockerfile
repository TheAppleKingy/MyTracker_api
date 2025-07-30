FROM python:3.13.5-alpine3.22

RUN apk add --no-cache curl

COPY src /app/src
COPY pyproject.toml poetry.lock /app/

WORKDIR /app

RUN curl -sSL https://install.python-poetry.org | python3 -

ENV PATH="/root/.local/bin:$PATH"

RUN poetry config virtualenvs.create false && \
    poetry install --no-root --no-interaction --no-ansi

WORKDIR /app/src

EXPOSE 8000
