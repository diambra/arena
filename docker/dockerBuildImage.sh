#!/bin/bash

docker build -f docker/diambra-arena-base_Dockerfile -t diambra:diambra-arena-base .
docker build -f docker/diambra-arena-gpu-cuda10.0_Dockerfile -t diambra:diambra-arena-gpu-cuda10.0 .
