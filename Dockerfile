FROM python:3.8.3

COPY . /app

WORKDIR /app/Scripts
RUN apt-get update -y
RUN apt-get install -y tesseract-ocr

RUN pip install -r requirements.txt

VOLUME /app/Scripts/config/

CMD python ./Main.py