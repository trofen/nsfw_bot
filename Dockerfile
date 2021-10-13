FROM debian:10.6-slim

MAINTAINER Trofen <nikita53ne@yandex.ru>

ENV TZ=Europe/Moscow

RUN apt-get update && \
    apt-get install --no-install-recommends -y caffe-cpu python3-pip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install -U pip

RUN python3 -m pip install -U setuptools

RUN pip3 install --no-cache-dir nsfw==0.3.2 pytelegrambotapi==4.1.1 av==8.0.3

COPY ./main.py ./main.py

CMD [ "python3", "./main.py" ]
