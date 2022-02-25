ARG BASE_IMAGE=diambra/base:latest
FROM $BASE_IMAGE

RUN apt-get -qy update && \
    apt-get -qy install python3-tk
