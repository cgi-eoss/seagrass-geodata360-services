#!/bin/bash

set -eux

###################
# Step parameters #
###################

BATHY_RESAMPLING=${BATHY_RESAMPLING:-bilinear}

COMPRESS=${COMPRESS:-DEFLATE}

######################
# Inputs and outputs #
######################

in_dir="/in/S2_PRODUCT"
out_dir="/out/BATHY"
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
out_name="BATHY_${in_name}"

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

echo "Collocating and interpolating bathymetry"
bathy_orig="/home/gaiascope/GEBCO_Bathymetric_UK_positive_01.tif"
bathy_collocated="${work_dir}/${out_name}.tif"
time /conda/bin/gdalwarp \
  -of COG -co COMPRESS=DEFLATE -co BIGTIFF="YES" \
  -t_srs "${product_epsg}" -te ${product_extents} -tr 10 10 \
  -r "${BATHY_RESAMPLING}" \
  -of COG -co COMPRESS=DEFLATE -ot UInt16 \
  "${bathy_orig}" "${bathy_collocated}"

mv "${bathy_collocated}" "${out_dir}/"
