FROM python:3.10-slim as runtime

VOLUME /config
WORKDIR /app

COPY runtime-deps.sh .
RUN bash runtime-deps.sh 1> /dev/null && rm runtime-deps.sh

FROM python:3.10-slim as build

WORKDIR /app

RUN apt-get -qq update && apt-get -qq install curl libpq-dev gcc 1> /dev/null

RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/usr/local python3 -

COPY pyproject.toml .
RUN poetry install -nvvv --no-dev && mv $(poetry env info --path) /app/venv

FROM runtime

COPY --from=build /app/venv /app/venv
COPY fred *.env ./fred/

CMD ./venv/bin/python3 -m fred