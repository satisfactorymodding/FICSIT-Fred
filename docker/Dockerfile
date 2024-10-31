FROM alpine AS runtime
#FROM python:3.12-slim AS runtime

VOLUME /config
WORKDIR /app

RUN apk update; apk add --no-cache python3 tesseract-ocr-data-eng re2-dev
#ENV DEBIAN_FRONTEND=noninteractive APT="apt-get -qq"
#RUN $APT update;  \
#    $APT install tesseract-ocr;  \
#    $APT clean; \
#    rm -rf /var/lib/apt/lists/*

FROM alpine AS build
#FROM python:3.12-slim AS build

WORKDIR /deps

#RUN pip --no-cache-dir install --progress-bar=off "poetry==1.8"
RUN apk update; apk add --no-cache g++ git re2-dev poetry python3-dev

COPY pyproject.toml poetry.lock poetry.toml ./
RUN poetry env use $(which python)
RUN poetry install -nvvv --no-root --compile --only main

COPY fred ./fred/
RUN poetry install -nvvv --only-root --compile

FROM runtime

COPY --from=build /deps/.venv ./venv
COPY fred ./fred/
COPY *.env .

CMD ["./venv/bin/python", "-m", "fred"]
