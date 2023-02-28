#!/bin/bash

set -eux

##################
# Implementation #
##################

# Activate conda environment
set +ux
source /conda/bin/activate
set -ux


/usr/bin/time -v /conda/bin/python -u /s2_normalisation.py

normalised=$(find /out/S2_GEOTIFF -maxdepth 1 -name '*.tif')
mask=$(find /out/S2_GEOTIFF -maxdepth 1 -name '*.tif' -print0 | xargs -0 basename | sed 's/\.tif/_mask.tif/')

mkdir -p /out/MASK

declare -a band_args
for b in {1..19}; do
  # convert number to octal then to ascii (offset to uppercase A=65)
  letter=$(printf '%b' "\\$(printf '%03o' "$((b + 64))")")
  band_args+=("-${letter}=${normalised}" "--${letter}_band=${b}")
  printf "Band number %d has gdal_calc.py letter %s\n" $b "$letter"
done

/usr/bin/time -v /conda/bin/gdal_calc.py --hideNoData "${band_args[@]}" \
  --calc "${MASK_EXPRESSION}" \
  --type=Byte --NoDataValue=0 \
  --format=GTiff --co=BIGTIFF=YES --co=NUM_THREADS=ALL_CPUS --co=COMPRESS="${COMPRESS:-DEFLATE}" \
  --overwrite --outfile /out/MASK/"$mask"
