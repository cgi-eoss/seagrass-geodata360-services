#!/bin/bash

set -eux

######################
# Inputs and outputs #
######################

in_dir="/in/INPUT"
in_dir_mask="/in/MASK"
in_dir_model="/in/MODEL"
out_dir="/out/CLASSIFIED"
conf_out_dir="/out/CONFIDENCE"
work_dir="/out/.work"
mkdir -p ${out_dir} ${work_dir} ${conf_out_dir}

if ! [ "$(ls -A ${in_dir})" ]; then
  echo "No files in ${in_dir}"
  exit 1
fi

##################
# Implementation #
##################

src_product=$(ls -1 ${in_dir})
INPUT="${in_dir}/${src_product}"

CLASSIFICATION_MODEL=$(find ${in_dir_model} -maxdepth 1 -name '*.txt')
TEMP_OUTPUT_FILE="${work_dir}/${src_product%.*}_classified.tif"
OUTPUT_FILE="${out_dir}/${src_product%.*}_classified.tif"
TEMP_CONF_OUTPUT="${work_dir}/${src_product%.*}_confidence.tif"
CONF_OUTPUT="${conf_out_dir}/${src_product%.*}_confidence.tif"

# Calculate input image stats for normalisation
/usr/bin/time otbcli_ComputeImagesStatistics \
  -ram 2048 \
  -il "${INPUT}" \
  -out.xml "${work_dir}/stats.xml"

# Use the image mask if supplied
if [ "$(ls -A "${in_dir_mask}/${src_product%.*}_mask.tif")" ]; then
  mask_arg=("-mask" "$(ls -1 "${in_dir_mask}/${src_product%.*}_mask.tif")")
fi

# Calculation using trained model
/usr/bin/time otbcli_ImageClassifier \
  -ram 2048 \
  -in "${INPUT}" \
  -imstat "${work_dir}/stats.xml" \
  -model "${CLASSIFICATION_MODEL}" \
  "${mask_arg[@]}" \
  -confmap "${TEMP_CONF_OUTPUT}" \
  -out "${TEMP_OUTPUT_FILE}"

/usr/bin/time gdal_translate \
  -of COG -co COMPRESS=DEFLATE -co NUM_THREADS=ALL_CPUS \
  "${TEMP_OUTPUT_FILE}" "${OUTPUT_FILE}"

/usr/bin/time gdal_translate \
  -of COG -co COMPRESS=DEFLATE -co NUM_THREADS=ALL_CPUS \
  "${TEMP_CONF_OUTPUT}" "${CONF_OUTPUT}"
