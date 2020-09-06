FROM python:3.8.3

COPY . /app

WORKDIR /app/bot
RUN apt-get update -y
RUN apt-get install -y tesseract-ocr

RUN pip install -r ../requirements.txt

VOLUME /app/config

CMD python ./bot.py