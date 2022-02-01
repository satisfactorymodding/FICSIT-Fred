FROM python:3.10

RUN apt-get update -y
RUN apt-get install -y apt-utils
RUN apt-get install -y tesseract-ocr

RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/usr/local python3 -

VOLUME /config
WORKDIR /app

COPY pyproject.toml .
COPY fred ./fred

RUN poetry config virtualenvs.create false
RUN poetry install -n
CMD python3 -m fred