FROM python:3.8-slim-buster
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8
ENV LANGUAGE=fa_IR.UTF-8
ENV LC_ALL=fa_IR.UTF-8
ENV LANG=fa_IR.UTF-8
WORKDIR /app
RUN apt-get update && \
    apt-get install -y locales && \
    locale-gen fa_IR.UTF-8 && \
    apt-get install -y ffmpeg build-essential gcc
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
COPY ./core /app