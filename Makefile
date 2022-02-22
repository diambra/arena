VERSION         ?= $(shell git rev-parse --short HEAD)
IMAGE_REGISTRY  ?= docker.io
IMAGE_REPO      ?= $(IMAGE_REGISTRY)/diambra
NVIDIA_REGISTRY ?= $(IMAGE_REGISTRY)
UBUNTU_REGISTRY ?= $(IMAGE_REGISTRY)
DOCKER          ?= docker
CUDA_VERSION    ?= 11.5.0
UBUNTU_VERSION  ?= 20.04

# Only used in info ouput
ROM_PATH        ?= ../diambraArena-roms/


# Images to build base image from
UBUNTU_BASE_IMAGE := $(UBUNTU_REGISTRY)/library/ubuntu:$(UBUNTU_VERSION)
CUDA_BASE_IMAGE   := $(NVIDIA_REGISTRY)/nvidia/cuda:$(CUDA_VERSION)-runtime-ubuntu$(UBUNTU_VERSION)

# Base image names
BASE_IMAGE      := $(IMAGE_REPO)/base:$(VERSION)
BASE_IMAGE_CUDA := $(IMAGE_REPO)/base-cuda:$(VERSION)

# Final image names
IMAGE      := $(IMAGE_REPO)/arena:$(VERSION)
IMAGE_CUDA := $(IMAGE_REPO)/arena-cuda:$(VERSION)


DIAMBRA_CRED_PATH := ${HOME}/.diambraCred
CONTAINER_ARGS := \
  -v $(ROM_PATH):/roms:ro \\\n\
	-v ${HOME}/.diambraCred:/root/.diambraCred \\\n

CONTAINER_ARGS_X := $(CONTAINER_ARGS) \
	-v /tmp/.X11-unix:/tmp/.X11-unix \\\n \
	-h $(shell hostname) -e DISPLAY=${DISPLAY} \\\n


define INFO
Available images:

# CPU only
## Headless
$(DOCKER) run $(CONTAINER_ARGS) $(IMAGE) python examples/diambraArenaGist.py

## with X
$(DOCKER) run $(CONTAINER_ARGS_X) $(IMAGE) python examples/diambraArenaGist.py

# NVIDIA CUDA
## Headless
$(DOCKER) run $(CONTAINER_ARGS) $(IMAGE_CUDA) python examples/diambraArenaGist.py

## Cuda
$(DOCKER) run $(CONTAINER_ARGS_X) $(IMAGE_CUDA) python examples/diambraArenaGist.py

endef

define build_image
$(DOCKER) build -f $(1) -t $(2) --build-arg BASE_IMAGE=$(3) .
endef

.PHONY: all
all: info

export INFO
info:
	@echo "$$INFO"

.PHONY: options
options:
	grep '^[A-Z_ ]*?' $(lastword $(MAKEFILE_LIST))

.PHONY: images
images: image image-cuda

.PHONY: push-images
push-images: images
	$(DOCKER) push $(BASE_IMAGE)
	$(DOCKER) push $(BASE_IMAGE_CUDA)
	$(DOCKER) push $(IMAGE)
	$(DOCKER) push $(IMAGE_CUDA)

# Base Images
.PHONY: image-base
image-base:
	$(call build_image,docker/Dockerfile.base,$(BASE_IMAGE),$(UBUNTU_BASE_IMAGE))

.PHONY: image-base-cuda
image-base-cuda: image-base
	$(call build_image,docker/Dockerfile.base,$(BASE_IMAGE_CUDA),$(CUDA_BASE_IMAGE))

# Final Images
.PHONY: image
image: image-base
	$(call build_image,docker/Dockerfile,$(IMAGE),$(BASE_IMAGE))

.PHONY: image-cuda
image-cuda: image-base-cuda
	$(call build_image,docker/Dockerfile,$(IMAGE_CUDA),$(BASE_IMAGE_CUDA))
