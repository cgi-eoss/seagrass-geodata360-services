#!/bin/bash

set -eux

###################
# Step parameters #
###################

HSM_RESAMPLING=${HSM_RESAMPLING:-bilinear}
HSM_FILL_DISTANCE=${HSM_FILL_DISTANCE:-200}

COMPRESS=${COMPRESS:-DEFLATE}

######################
# Inputs and outputs #
######################

in_dir="/in/S2_PRODUCT"
out_dir="/out/HSM"
work_dir="/out/.work"
mkdir -p ${out_dir} ${work_dir}

if ! [ "$(ls -A ${in_dir})" ]; then
  echo "No files in ${in_dir}"
  exit 1
fi

# Derived parameters

in_file=$(find ${in_dir}/* -maxdepth 1 -type f | head -1)
# Remove the parent directories
in_name=${in_file##*/}
# Remove the file extension
in_name=${in_name%%.*}
out_name="HSM_${in_name}"

##################
# Implementation #
##################

# Activate conda environment
set +ux
source /conda/bin/activate
set -ux

product_epsg=$(/conda/bin/python /home/gaiascope/s2ProductZones.py "${in_file}")
echo "Detected product SRS: ${product_epsg}"

product_extents=$(/conda/bin/python /home/gaiascope/s2Extents.py "${in_file}")
echo "Detected product extents: ${product_extents}"

echo "Collocating and interpolating seagrass habitat suitability model"
hsm_orig="/home/gaiascope/hsm.tif"
hsm_collocated="/home/gaiascope/hsm_collocated.tif"
hsm_filled="/home/gaiascope/${out_name}_filled.tif"
hsm_scaled="/home/gaiascope/${out_name}.tif"
time /conda/bin/gdalwarp \
  -of COG -co COMPRESS=DEFLATE -co BIGTIFF="YES" \
  -t_srs "${product_epsg}" -te ${product_extents} -tr 10 10 \
  -r "${HSM_RESAMPLING}" \
  "${hsm_orig}" "${hsm_collocated}"
time /conda/bin/gdal_fillnodata.py \
  -co COMPRESS=DEFLATE \
  -md "${HSM_FILL_DISTANCE}" \
  "${hsm_collocated}" "${hsm_filled}"

# Convert to UInt16 to match type of other bands in normalisation step and scale to convert the values to integers.
time /conda/bin/gdal_translate \
  -of COG -co COMPRESS=DEFLATE -scale 0 1 0 65536 -ot UInt16 \
  "${hsm_filled}" "${hsm_scaled}"

mv "${hsm_scaled}" "${out_dir}/"


