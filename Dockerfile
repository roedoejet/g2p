# Base Image
FROM debian:buster-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN mkdir /gi2pi
RUN mkdir /gi2pi/gi2pi
COPY gi2pi /gi2pi/gi2pi
COPY requirements.txt /gi2pi
COPY setup.py /gi2pi

# Get Dependencies
RUN apt-get update -y && apt-get install -y apt-transport-https
RUN apt-get install -y python3 python3-pip python3-dev build-essential nano
RUN pip3 install -r /gi2pi/requirements.txt
RUN pip3 install gunicorn
RUN pip3 install -e /gi2pi

CMD gunicorn gi2pi:APP --bind 0.0.0.0:5000