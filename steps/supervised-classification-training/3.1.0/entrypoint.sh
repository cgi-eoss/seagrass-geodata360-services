#!/bin/bash

set -eux

###################
# Step parameters #
###################

TRAINING_SHAPEFILE_ATTR=${TRAINING_SHAPEFILE_ATTR}
TRAINING_FEATURES=${TRAINING_FEATURES:-"0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17"}

MAX_VAL=${MAX_VAL:-1000}
MAX_TRAIN=${MAX_TRAIN:-1000}
TRAIN_VAL_RATIO=${TRAIN_VAL_RATIO:-0.5}
MAX_DEPTH=${MAX_DEPTH:-5}
MIN_SAMPLES=${MIN_SAMPLES:-10}
REGRESSION_ACCURACY=${REGRESSION_ACCURACY:-0}
CATEGORICAL_CLUSTERS=${CATEGORICAL_CLUSTERS:-10}
SUBSET_SIZE=${SUBSET_SIZE:-0}
MAX_TREES=${MAX_TREES:-100}
SUFFICIENT_ACCURACY=${SUFFICIENT_ACCURACY:-0.01}
RANDOM_SEED=${RANDOM_SEED:-}

######################
# Inputs and outputs #
######################

in_dir="/in/INPUT"
mask_dir="/in/MASK"
statistics_dir="/in/STATISTICS"
GT_SF="/in/GROUND_TRUTH_SHAPEFILE"
out_dir_model="/out/MODEL"
out_dir_cm="/out/CONFUSION_MATRIX"
out_dir_aux="/out/AUX_FILE"
work_dir="/out/.work"
temp_sh="${work_dir}/shapefile"
temp_input="${work_dir}/input"
mkdir -p ${out_dir_model} ${out_dir_cm} ${out_dir_aux} ${temp_sh} ${temp_input}

if ! [ "$(ls -A ${in_dir})" ]; then
  echo "No files in ${in_dir}"
  exit 1
fi

TIMESTAMP=$(date --utc +%Y%m%d_%H%M%SZ)
TRAINING_OUTPUT_CLASSIFICATION_MODEL="${out_dir_model}/${TIMESTAMP}_training_model.txt"
TRAINING_OUTPUT_CONFUSION_MATRIX_CSV="${out_dir_cm}/${TIMESTAMP}_confusion_matrix.csv"
AUX_FILE="${out_dir_aux}/${TIMESTAMP}_inputs.txt"

##################
# Implementation #
##################

for shapefile_zip in "${GT_SF}/"*.zip; do
  shapefile_name=${shapefile_zip##*/}
  shapefile_name=${shapefile_name%.*}
  unzip -o "${shapefile_zip}" -d "${temp_sh}/"
done

TRAINING_SHAPEFILE="${temp_sh}/$(ls -1 ${temp_sh})"
ls -o "${TRAINING_SHAPEFILE}"

# This gets easier if we use (1-based) indexes to match up files, so we
# set up links to the inputs.
declare -i max=0
for f in "${in_dir}"/*.tif; do
  max+=1

  # Link the normalised S-2 geotiff
  ln -snf "$f" ${temp_input}/in_$max.tif

  # Link the corresponding mask file
  product=$(basename "$f")
  mask=${product/%.tif/_mask.tif}
  ln -snf "${mask_dir}/${mask}" ${temp_input}/mask_$max.tif
done

# Compute class statistics over pixels where the input images intersect with
# the training shapefile.
for ((i = 1; i <= max; i++)); do
  otbcli_PolygonClassStatistics -ram 2048 \
    -in "${temp_input}/in_${i}.tif" -mask "${temp_input}/mask_${i}.tif" \
    -vec "$TRAINING_SHAPEFILE" -field "$TRAINING_SHAPEFILE_ATTR" \
    -out ${work_dir}/"classes_${i}.xml"
done

# Compute pixel sampling rate across all input images.
# Use find|sort to ensure correct ordering for the rates_X.csv outputs.
readarray -t classes_files < <(find $work_dir -maxdepth 1 -name 'classes_*.xml' | sort -V)
otbcli_MultiImageSamplingRate \
  -il "${classes_files[@]}" \
  -out ${work_dir}/rates.csv # automatically names outputs rates_1.csv, rates_2.csv, etc.

# If a fixed random seed is defined, use it for applications which take it
rand_arg=""
if [ -n "$RANDOM_SEED" ]; then
  rand_arg=("-rand" "$RANDOM_SEED")
fi

# Select sample pixels from each input according to the sample rate.
for ((i = 1; i <= max; i++)); do
  otbcli_SampleSelection -ram 2048 \
    -in "${temp_input}/in_${i}.tif" -mask "${temp_input}/mask_${i}.tif" \
    -vec "$TRAINING_SHAPEFILE" -field "$TRAINING_SHAPEFILE_ATTR" \
    -instats "${work_dir}/classes_${i}.xml" \
    -strategy byclass -strategy.byclass.in "${work_dir}/rates_${i}.csv" \
    -out "${work_dir}/samples_${i}.sqlite" \
    "${rand_arg[@]}"
done

# Measure values of each sample pixel - updates in-place samples_N.sqlite.
# We lowercase the TRAINING_SHAPEFILE_ATTR to match the sqlite column name.
#
# If no training samples exist (i.e. no non-masked data covering the training
# areas) we remove the sample database file or else TrainVectorClassifier
# will segfault.
sqlite_attr_column="${TRAINING_SHAPEFILE_ATTR,,}"
sqlite_band_column_prefix="band_"

for ((i = 1; i <= max; i++)); do
  otbcli_SampleExtraction -ram 2048 \
    -in "${temp_input}/in_${i}.tif" \
    -vec "${work_dir}/samples_${i}.sqlite" \
    -outfield prefix -outfield.prefix.name "$sqlite_band_column_prefix" \
    -field "$sqlite_attr_column" ||
    (echo "No sample pixels in in_${i}.tif, removing samples_${i}.sqlite" && rm "${work_dir}/samples_${i}.sqlite")
done

# If overall image statistics are available, use them to assist the training
# algorithm with scaling etc.
statistics_arg=""
if [ "$(ls -A ${statistics_dir})" ]; then
  statistics_arg=("-io.stats" "$(ls -1 ${statistics_dir}/*.xml)")
fi

# For each band integer in TRAINING_FEATURES, add it to the params as "$prefix$band"
IFS=" " read -r -a feat_params <<<"$TRAINING_FEATURES"

# Finally, train the model on the sampled files
/usr/bin/time -v otbcli_TrainVectorClassifier \
  -io.vd ${work_dir}/samples_*.sqlite \
  -cfield "$sqlite_attr_column" \
  -feat "${feat_params[@]/#/$sqlite_band_column_prefix}" \
  "${statistics_arg[@]}" \
  -classifier rf \
  -classifier.rf.max "$MAX_DEPTH" \
  -classifier.rf.min "$MIN_SAMPLES" \
  -classifier.rf.ra "$REGRESSION_ACCURACY" \
  -classifier.rf.cat "$CATEGORICAL_CLUSTERS" \
  -classifier.rf.var "$SUBSET_SIZE" \
  -classifier.rf.nbtrees "$MAX_TREES" \
  -classifier.rf.acc "$SUFFICIENT_ACCURACY" \
  -io.out "$TRAINING_OUTPUT_CLASSIFICATION_MODEL" \
  -io.confmatout "$TRAINING_OUTPUT_CONFUSION_MATRIX_CSV" \
  "${rand_arg[@]}"

# TODO Extract validation samples and add parameters to TrainVectorClassifier:
# (WARNING) TrainVectorClassifier: The validation set is empty. The performance estimation is done using the input training set in this case.

# Create auxiliary file to keep track of parameters and training inputs
cat <<EOF >"$AUX_FILE"
PARAMETERS FOR MODEL ${TIMESTAMP}_training_model.txt:

MAX_DEPTH = ${MAX_DEPTH}
MIN_SAMPLES = ${MIN_SAMPLES}
SUBSET_SIZE = ${SUBSET_SIZE}
MAX_TREES = ${MAX_TREES}
RANDOM_SEED = ${RANDOM_SEED:-<random>}

TRAINING_FEATURES: ${TRAINING_FEATURES}

TRAINING/VALIDATION INPUT FILES:

$(ls -1 "${in_dir}"/*.tif)
EOF
