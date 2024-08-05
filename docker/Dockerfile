FROM python:3.12-slim AS runtime

ENV DEBIAN_FRONTEND=noninteractive
VOLUME /config
WORKDIR /app

COPY docker/runtime-deps.sh .
RUN bash runtime-deps.sh 1> /dev/null && rm runtime-deps.sh

FROM python:3.12-slim AS build

WORKDIR /app

RUN apt-get -qq update && apt-get -qq install curl libpq-dev gcc 1> /dev/null

RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/usr/local python3 -

COPY pyproject.toml .
RUN poetry install -nvvv --only main && mv $(poetry env info --path) /app/venv

FROM runtime

COPY --from=build /app/venv /app/venv
COPY fred *.env ./fred/

CMD ./venv/bin/python3 -m fred