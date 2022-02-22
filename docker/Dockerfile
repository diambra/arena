ARG BASE_IMAGE=diambra/base:latest
FROM $BASE_IMAGE

WORKDIR /opt/diambraArena/
COPY .  /opt/diambraArena/repo/
RUN pip install repo/

ENV DIAMBRAROMSPATH="/opt/diambraArena/roms/"
ENV DOCKER_EXEC=1
