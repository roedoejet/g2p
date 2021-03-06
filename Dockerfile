# Base Image
FROM debian:buster-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN mkdir /g2p
RUN mkdir /g2p/g2p
COPY g2p /g2p/g2p
COPY requirements.txt /g2p
COPY setup.py /g2p
COPY README.md /g2p

# Get Dependencies
RUN apt-get update -y && apt-get install -y apt-transport-https
RUN apt-get install -y python3 python3-pip python3-dev build-essential nano
RUN pip3 install -r /g2p/requirements.txt
RUN pip3 install gunicorn eventlet
RUN pip3 install -e /g2p

# Runs the app on $PORT. 
# Comment this out if you just want to install g2p in the container without running the studio.
CMD gunicorn --worker-class eventlet -w 1 g2p:APP