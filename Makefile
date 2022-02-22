VERSION := $(shell git rev-parse --short HEAD)
IMAGE_REGISTRY ?= docker.io/diambra

DOCKER ?= podman
BASE_IMAGE      := $(IMAGE_REGISTRY)/base:$(VERSION)
BASE_IMAGE_X    := $(IMAGE_REGISTRY)/base-x:$(VERSION)
BASE_IMAGE_CUDA := $(IMAGE_REGISTRY)/base-cuda:$(VERSION)

IMAGE               := $(IMAGE_REGISTRY)/arena:$(VERSION)
IMAGE_HEADLESS      := $(IMAGE_REGISTRY)/arena-headless:$(VERSION)
IMAGE_HEADLESS_CUDA := $(IMAGE_REGISTRY)/arena-headless-cuda:$(VERSION)

define INFO
Image $(IMAGE) ready, to use it:

$(DOCKER) run -ti \
	-v /path/to/roms:/roms \
	-v /tmp/.X11-unix:/tmp/.X11-unix \
	-v ${HOME}/.diambraCred:/root/.diambraCred \
	-h $(shell hostname) -e DISPLAY=${DISPLAY} $(IMAGE) bash

endef

define build_image
$(DOCKER) build -f $(1) -t $(2) $(3) .
endef

all: info

export INFO
info:
	@echo "$$INFO"

images: image-headless image-headless-cuda image-base-x

# Base Images
.PHONY: image-base
image-base:
	$(call build_image,docker/Dockerfile.base,$(BASE_IMAGE))

.PHONY: image-base-cuda
image-base-cuda: image-base
	$(call build_image,docker/Dockerfile.base.cuda,$(BASE_IMAGE_CUDA),--build-arg BASE_IMAGE="$(BASE_IMAGE)")

.PHONY: image-base-x
image-base-x: image-base
	$(call build_image,docker/Dockerfile.base.x,$(BASE_IMAGE_X),--build-arg BASE_IMAGE="$(BASE_IMAGE)")


# Final Images
.PHONY: image-headless
image-headless: image-base
	$(call build_image,docker/Dockerfile,$(IMAGE_HEADLESS),--build-arg BASE_IMAGE="$(BASE_IMAGE)")

.PHONY: image-headless-cuda
image-headless-cuda: image-base-cuda
	$(call build_image,docker/Dockerfile,$(IMAGE_HEADLESS_CUDA),--build-arg BASE_IMAGE="$(BASE_IMAGE_CUDA)")

.PHONY: image
image: image-base-x
	$(call build_image,docker/Dockerfile,$(IMAGE),--build-arg BASE_IMAGE="$(BASE_IMAGE_X)")
