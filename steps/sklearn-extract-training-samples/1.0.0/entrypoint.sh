#!/bin/bash

set -eux

###################
# Step parameters #
###################

TRAINING_SHAPEFILE_ATTR=${TRAINING_SHAPEFILE_ATTR:-MC_ID}

######################
# Inputs and outputs #
######################

product_dir="/in/PRODUCT"
mask_dir="/in/MASK"
ground_truth_dir="/in/GROUND_TRUTH"
out_dir="/out/SAMPLES"
work_dir="/out/.work"
mkdir -p $out_dir $work_dir

# One file expected for each input - GD360 enforces this, but to be defensive...

product_files=("${product_dir}"/*)
[ "${#product_files[@]}" -ge 2 ] && exit 1
if [ -e "${product_files[0]}" ]; then
  product_path="${product_files[0]}"
else
  exit 1
fi

mask_files=("${mask_dir}"/*)
[ "${#mask_files[@]}" -ge 2 ] && exit 1
if [ -e "${mask_files[0]}" ]; then
  mask_path="${mask_files[0]}"
else
  exit 1
fi

ground_truth_files=("${ground_truth_dir}"/*)
[ "${#ground_truth_files[@]}" -ge 2 ] && exit 1
if [ -e "${ground_truth_files[0]}" ]; then
  ground_truth_path="${ground_truth_files[0]}"
else
  exit 1
fi

##################
# Implementation #
##################

# Activate conda environment
set +ux
source /conda/bin/activate
set -ux

exec /usr/bin/time -v /conda/bin/python -u /extract_training_samples.py "$product_path" "$mask_path" "$ground_truth_path" "$TRAINING_SHAPEFILE_ATTR" "$out_dir"
