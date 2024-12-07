FROM python:3.12-alpine

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN apk add -u gcc libffi-dev musl-dev & \
    pip3 install --no-cache-dir poetry==1.8.5 && \
    poetry config virtualenvs.create false

RUN poetry install --no-root --no-interaction

COPY service/ .
