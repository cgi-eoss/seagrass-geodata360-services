#!/bin/bash

##################
# Implementation #
##################

# Activate conda environment
set +ux
source /conda/bin/activate
set -ux

/usr/bin/time -v /conda/bin/python -u /compute_images_statistics.py