FROM alpine AS runtime

VOLUME /config
WORKDIR /app

RUN apk update; apk add --no-cache python3=~3.12 tesseract-ocr-data-eng re2-dev

FROM alpine AS build

WORKDIR /deps

RUN apk update; apk add --no-cache g++ git re2-dev poetry python3-dev=~3.12

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
