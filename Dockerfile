FROM python:3.10

RUN apt-get update -y
RUN apt-get install -y tesseract-ocr
RUN pip install pipx
RUN pipx install pdm
RUN pipx inject pdm pdm-venv

VOLUME /config
WORKDIR /app

RUN pdm venv create 3.10
RUN pdm config python.use_venv true

COPY pyproject.toml *.env ./
RUN pdm install -no-s --no-i

COPY fred ./fred
RUN pdm install -no-i
CMD python3 -m freddoc