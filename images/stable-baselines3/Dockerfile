ARG on
FROM python:${on}

RUN apt-get -qy update && \
    apt-get -qy install libgl1 && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get -qy clean

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8

# Copy arena to tmp since bind-mount is read-only and pip doesn't support
# out-of-tree builds.
RUN --mount=target=/usr/src/arena,type=bind,source=. \
    cp -r /usr/src/arena /tmp/arena && \
    pip install /tmp/arena[stable-baselines3] && \
    rm -rf /tmp/arena
