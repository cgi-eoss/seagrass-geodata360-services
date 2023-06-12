#!/bin/bash

set -eux

###################
# Step parameters #
###################

GRID_SEARCH_CROSS_VALIDATION=${GRID_SEARCH_CROSS_VALIDATION:-true}

cv_arg="no_cv"
if [ "${GRID_SEARCH_CROSS_VALIDATION,,}" == "true" ]; then
  cv_arg="grid_cv"
fi

TRAINING_FEATURES=${TRAINING_FEATURES:-"0 1 2 3 4 5 6 7 8 9 10 11 17"}

# !! IMPORTANT !!
# Other classifier-specific parameter env vars are processed in
# train_classifier.py, where we can use more logic.

######################
# Inputs and outputs #
######################

samples_dir="/in/SAMPLES"
model_dir="/out/MODEL"
aux_dir="/out/AUX_FILE"
work_dir="/out/.work"
mkdir -p $model_dir $aux_dir $work_dir

samples_files=("${samples_dir}"/*)

##################
# Implementation #
##################

# Activate conda environment
set +ux
source /conda/bin/activate
set -ux

exec /usr/bin/time -v /conda/bin/python -u /train_classifier.py "$TRAINING_FEATURES" "$cv_arg" "$model_dir" "$aux_dir" "${samples_files[@]}"
