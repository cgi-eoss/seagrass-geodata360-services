#!/bin/bash

##################
# Implementation #
##################

# Activate conda environment
set +ux
source /conda/bin/activate
set -ux

/usr/bin/time -v /conda/bin/python -u /s2_geotiff.py