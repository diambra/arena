ARG on
FROM python:${on}

RUN apt-get -qy update && \
    apt-get -qy install libgl1 && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get -qy clean

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

RUN pip install huggingface_hub

RUN pip install huggingface_hub

# Copy arena to tmp since bind-mount is read-only and pip doesn't support
# out-of-tree builds.
RUN --mount=target=/usr/src/arena,type=bind,source=. \
    cp -r /usr/src/arena /tmp/arena && \
    pip install /tmp/arena && \
    rm -rf /tmp/arena

ENV HF_HOME=/tmp
