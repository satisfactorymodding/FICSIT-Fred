FROM python:3.12-alpine AS runtime
#FROM python:3.12-slim AS runtime

VOLUME /config
WORKDIR /app

RUN apk update; apk add --no-cache tesseract-ocr-data-eng re2
#ENV DEBIAN_FRONTEND=noninteractive APT="apt-get -qq"
#RUN $APT update;  \
#    $APT install tesseract-ocr;  \
#    $APT clean; \
#    rm -rf /var/lib/apt/lists/*

FROM python:3.12-alpine AS build
#FROM python:3.12-slim AS build

WORKDIR /deps

RUN pip --no-cache-dir install --progress-bar=off "poetry==1.8"
RUN apk update; apk add g++ git re2-dev
COPY pyproject.toml .
COPY poetry.lock .
RUN poetry install -nvvv --only main --no-root
RUN mv $(poetry env info --path) ./venv

FROM runtime

COPY --from=build /deps/venv ./venv
COPY fred ./fred/
COPY *.env .

CMD ./venv/bin/python3 -m fred
