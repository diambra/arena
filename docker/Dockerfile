ARG BASE_IMAGE=diambra/base-x:latest
FROM $BASE_IMAGE

WORKDIR /opt/diambraArena/
COPY .  /opt/diambraArena
RUN pip install .

ENV DIAMBRAROMSPATH="/roms/"
