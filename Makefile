VERSION           ?= $(shell git rev-parse --short HEAD)
IMAGE_REGISTRY    ?= docker.io
IMAGE_REPO        ?= $(IMAGE_REGISTRY)/diambra
NVIDIA_REGISTRY   ?= $(IMAGE_REGISTRY)
UBUNTU_REGISTRY   ?= $(IMAGE_REGISTRY)
CONTAINER_RUNTIME ?= docker
CUDA_10_BASE_TAG  ?= 10.0-cudnn7-runtime-ubuntu18.04
CUDA_11_BASE_TAG  ?= 11.0.3-cudnn8-runtime-ubuntu20.04
UBUNTU_BASE_TAG   ?= 20.04

# Only used in info ouput
ROM_PATH        ?= ../diambraArena-roms/


# Images to build base image from
UBUNTU_BASE_IMAGE  := $(UBUNTU_REGISTRY)/library/ubuntu:$(UBUNTU_BASE_TAG)
CUDA_10_BASE_IMAGE := $(NVIDIA_REGISTRY)/nvidia/cuda:$(CUDA_10_BASE_TAG)
CUDA_11_BASE_IMAGE := $(NVIDIA_REGISTRY)/nvidia/cuda:$(CUDA_11_BASE_TAG)

# Base image names
BASE_IMAGE         := $(IMAGE_REPO)/base:$(VERSION)
BASE_IMAGE_CUDA_10 := $(IMAGE_REPO)/base-cuda10:$(VERSION)
BASE_IMAGE_CUDA_11 := $(IMAGE_REPO)/base-cuda11:$(VERSION)

# Final image names
IMAGE         := $(IMAGE_REPO)/diambra-arena:$(VERSION)
IMAGE_CUDA_10 := $(IMAGE_REPO)/diambra-arena-cuda10:$(VERSION)
IMAGE_CUDA_11 := $(IMAGE_REPO)/diambra-arena-cuda11:$(VERSION)


DIAMBRA_CRED_PATH := ${HOME}/.diambraCred
CONTAINER_ARGS := \
  -v $(ROM_PATH):/opt/diambraArena/roms:ro \\\n\
	-v ${HOME}/.diambraCred:/root/.diambraCred \\\n

CONTAINER_ARGS_X := $(CONTAINER_ARGS) \
	-v /tmp/.X11-unix:/tmp/.X11-unix \\\n \
	-h $(shell hostname) -e DISPLAY=${DISPLAY} \\\n


define INFO
Available images:

# CPU only
## Headless
$(CONTAINER_RUNTIME) run $(CONTAINER_ARGS) $(IMAGE) python examples/diambraArenaGist.py

## with X
$(CONTAINER_RUNTIME) run $(CONTAINER_ARGS_X) $(IMAGE) python examples/diambraArenaGist.py

# NVIDIA CUDA
## Headless
$(CONTAINER_RUNTIME) run $(CONTAINER_ARGS) $(IMAGE_CUDA_11) python examples/diambraArenaGist.py

## Cuda
$(CONTAINER_RUNTIME) run $(CONTAINER_ARGS_X) $(IMAGE_CUDA_11) python examples/diambraArenaGist.py

endef

define build_image
$(CONTAINER_RUNTIME) build -f $(1) -t $(2) --build-arg BASE_IMAGE=$(3) $(4) .
endef

.PHONY: all
all: images

export INFO
info:
	@echo "$$INFO"

.PHONY: options
options:
	grep '^[A-Z_ ]*?' $(lastword $(MAKEFILE_LIST))

.PHONY: images
images: image image-cuda-10 image-cuda-11

.PHONY: push-images
push-images: images
	$(CONTAINER_RUNTIME) push $(BASE_IMAGE)
	$(CONTAINER_RUNTIME) push $(BASE_IMAGE_CUDA_10)
	$(CONTAINER_RUNTIME) push $(BASE_IMAGE_CUDA_11)
	$(CONTAINER_RUNTIME) push $(IMAGE)
	$(CONTAINER_RUNTIME) push $(IMAGE_CUDA_10)
	$(CONTAINER_RUNTIME) push $(IMAGE_CUDA_11)

# Base Images
.PHONY: image-base
image-base:
	$(call build_image,docker/Dockerfile.base,$(BASE_IMAGE),$(UBUNTU_BASE_IMAGE))

.PHONY: image-base-cuda-10
image-base-cuda-10: image-base
	$(call build_image,docker/Dockerfile.base,$(BASE_IMAGE_CUDA_10),$(CUDA_10_BASE_IMAGE),--build-arg BOOST_VERSION=1.65)

.PHONY: image-base-cuda-11
image-base-cuda-11: image-base
	$(call build_image,docker/Dockerfile.base,$(BASE_IMAGE_CUDA_11),$(CUDA_11_BASE_IMAGE))

# Final Images
.PHONY: image
image: image-base
	$(call build_image,docker/Dockerfile,$(IMAGE),$(BASE_IMAGE))

.PHONY: image-cuda-10
image-cuda-10: image-base-cuda-10
	$(call build_image,docker/Dockerfile,$(IMAGE_CUDA_10),$(BASE_IMAGE_CUDA_10))

.PHONY: image-cuda-11
image-cuda-11: image-base-cuda-11
	$(call build_image,docker/Dockerfile,$(IMAGE_CUDA_11),$(BASE_IMAGE_CUDA_11))
