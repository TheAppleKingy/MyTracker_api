FROM python:3.13-alpine3.22

RUN apk add --no-cache curl netcat-openbsd

WORKDIR /app

COPY poetry.lock pyproject.toml ./

RUN pip install poetry
ENV PATH="/root/.local/bin:$PATH"

RUN poetry config virtualenvs.create false && \
    poetry install --no-root --no-interaction --no-ansi

COPY ./src ./src
