FROM python:3.10

# install tesseract, for Fred's OCR capabilities
RUN apt-get update -y
RUN apt-get install -y tesseract-ocr

# folders for image
VOLUME /config
WORKDIR /app

# install pdm, the python package manager we use
RUN pip install -U pip setuptools wheel
RUN curl -sSL https://raw.githubusercontent.com/pdm-project/pdm/main/install-pdm.py | python3 - -p /usr/local # adds bin fsr

COPY pyproject.toml *.lock *.env README* ./
RUN pdm sync

COPY fred /app/fred
RUN pdm install -v --prod --no-editable

# start the application
ENV PYTHONPATH=/app/__pypackages__/3.10/lib
CMD python3 -m fred