FROM python:3.10.1

RUN apt-get update -y
RUN apt-get install -y tesseract-ocr

VOLUME /app/config
WORKDIR /app/bot

COPY ./requirements.txt /app

RUN pip install --upgrade pip wheel setuptools
RUN pip install -r ../requirements.txt

COPY . /app

CMD python ./bot.py