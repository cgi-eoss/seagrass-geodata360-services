#!/bin/bash

###################
# Step parameters #
###################

CLASS_ID=${CLASS_ID:-1}
CONF_MASK_THRESHOLD=${CONF_MASK_THRESHOLD:-0.1}

######################
# Inputs and outputs #
######################

classified_in="/in/CLASSIFIED"
confidence_in="/in/CONFIDENCE"
out_dir="/out/SINGLE_CLASS_CONFIDENCE"
temp_mask_1="/out/.tmp/CLASS_1_MASK"
temp_mask_2="/out/.tmp/CONF_MASK"
temp_output="/out/.tmp/MASKED"
mkdir -p ${out_dir} ${temp_mask_1} ${temp_mask_2} ${temp_output}

if ! [ "$(ls -A ${classified_in})" ]; then
  echo "No files in ${classified_in}"
  exit 1
fi

if ! [ "$(ls -A ${confidence_in})" ]; then
  echo "No files in ${confidence_in}"
  exit 1
fi

##################
# Implementation #
##################

# Activate conda environment
set +ux
source /conda/bin/activate
set -ux

src_product=$(ls -1 ${classified_in})
classified_file=$(find ${classified_in}/* -maxdepth 1 -type f | head -1)
confidence_file=$(find ${confidence_in}/* -maxdepth 1 -type f | head -1)
output="${out_dir}/${src_product%.*}_single_class_confidence.tif"

# Create mask for a single class
/usr/bin/time -v /conda/bin/gdal_calc.py -A ${classified_file} \
  --calc "A==${CLASS_ID}" \
  --type=Byte --NoDataValue=0 \
  --format=GTiff --co=BIGTIFF=YES --co=NUM_THREADS=ALL_CPUS --co=COMPRESS=DEFLATE \
  --overwrite --outfile "${temp_mask_1}/single_class.tif"

# Create mask from confidence layer
/usr/bin/time -v /conda/bin/gdal_calc.py -A ${confidence_file} \
  --calc "A>=${CONF_MASK_THRESHOLD}" \
  --type=Byte --NoDataValue=0 \
  --format=GTiff --co=BIGTIFF=YES --co=NUM_THREADS=ALL_CPUS --co=COMPRESS=DEFLATE \
  --overwrite --outfile "${temp_mask_2}/conf_mask.tif"

# Apply masks to confidence layer
/usr/bin/time -v /conda/bin/gdal_calc.py \
  -A ${confidence_file} \
  -B "${temp_mask_1}/single_class.tif" \
  -C "${temp_mask_2}/conf_mask.tif" \
  --outfile="${temp_output}/single_class_confidence.tif" --calc="A*B*C"

# Compress the output
# TODO Investigate why COG seems to break here
/usr/bin/time gdal_translate \
  -of GTIFF -co COMPRESS=DEFLATE -co NUM_THREADS=ALL_CPUS \
  "${temp_output}/single_class_confidence.tif" "${output}"
