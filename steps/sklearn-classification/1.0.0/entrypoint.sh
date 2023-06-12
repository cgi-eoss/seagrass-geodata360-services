#!/bin/bash

set -eux

###################
# Step parameters #
###################

TRAINING_FEATURES=${TRAINING_FEATURES:-"0 1 2 3 4 5 6 7 8 9 10 11 17"}

# !! IMPORTANT !!
# Other parameter env vars are processed in classify.py, where we can use more
# logic.

######################
# Inputs and outputs #
######################

classifier_dir="/in/CLASSIFIER"
product_dir="/in/PRODUCT"
mask_dir="/in/MASK"
classified_dir="/out/CLASSIFIED"
proba_dir="/out/CLASS_PROBABILITY"
work_dir="/out/.work"
mkdir -p $classified_dir $proba_dir $work_dir

# One file expected for each input - GD360 enforces this, but to be defensive...

classifier_files=("${classifier_dir}"/*)
[ "${#classifier_files[@]}" -ge 2 ] && exit 1
if [ -e "${classifier_files[0]}" ]; then
  classifier_path="${classifier_files[0]}"
else
  exit 1
fi

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
  if [ "${USE_MASK:-true}" == "true" ]; then
    echo "USE_MASK is true, but no input was found in ${mask_dir}"
    exit 1
  fi
  mask_path=""
fi

##################
# Implementation #
##################

# Activate conda environment
set +ux
source /conda/bin/activate
set -ux

exec /usr/bin/time -v /conda/bin/python -u /classify.py "$TRAINING_FEATURES" "$classifier_path" "$product_path" "$mask_path" "$classified_dir" "$proba_dir"
