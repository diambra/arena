FROM python:buster
RUN apt-get -qy update && \
    apt-get -qy install libgl1

ARG REF=main
RUN pip install git+https://github.com/diambra/arena.git@${REF}

COPY . /app
WORKDIR /app

ENTRYPOINT [ "python", "/app/diambra_arena_gist.py" ]
