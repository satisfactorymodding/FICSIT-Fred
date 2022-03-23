FROM python:3.10-slim

RUN apt-get update -y && apt-get install -y apt-utils tesseract-ocr curl

RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/usr/local python3 -

VOLUME /config
WORKDIR /app

COPY pyproject.toml *.env ./
RUN poetry config virtualenvs.create false
RUN poetry install -n

COPY fred ./fred
RUN poetry install -n
CMD python3 -m fred