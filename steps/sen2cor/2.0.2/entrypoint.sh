#!/bin/bash

set -eux

###################
# Step parameters #
###################

ENABLE_QI_DATA_FALLBACK=${ENABLE_QI_DATA_FALLBACK:-true}
ENABLE_ZIP_OUTPUT=${ENABLE_ZIP_OUTPUT:-false}

######################
# Inputs and outputs #
######################

source=/in/S2_PRODUCT
target=/out/S2_L2A
mkdir -p ${target}

if ! [ "$(ls -A ${source})" ]; then
  echo "No files in ${source}"
  exit 1
fi

##################
# Implementation #
##################

cd "$HOME"

src_product=$(ls -1 ${source})

temp_input=/out/.temp_input
mkdir -p ${temp_input}

# If src_product is zip, then unzip; otherwise move anyway
# Create an empty aux_data folder in case it has been stripped, to work around sen2cor issue
# See: https://forum.step.esa.int/t/sen2cor-2-8-fails-on-product-from-early-2016-bool-object-has-no-attribute-spacecraft-name/16046/3
if [ "${src_product##*.}" == "zip" ] || [ "${src_product##*.}" == "ZIP" ]; then
  src_product_name=${src_product%.*}
  [[ $src_product_name == *.SAFE ]] || src_product_name+=".SAFE"
  mkdir -p "${temp_input}/${src_product_name}"
  unzip -o "${source}/${src_product}" -d "${temp_input}/${src_product_name}"
  # some data providers package the product within a folder...
  if [ "$(find ${temp_input}/${src_product_name} -maxdepth 1 -printf %y)" == "dd" ]; then
    d=$(find ${temp_input}/${src_product_name} -mindepth 1 -maxdepth 1 -type d)
    mv $d/* "${temp_input}/${src_product_name}"
    rmdir $d
  fi
  mkdir -p "${temp_input}/${src_product_name}/AUX_DATA"
else
  src_product_name=${src_product}
  [[ $src_product_name == *.SAFE ]] || src_product_name+=".SAFE"
  cp -r "${source}/${src_product}" "${temp_input}/${src_product_name}"
  mkdir -p "${temp_input}/${src_product_name}/AUX_DATA"
fi

# Depending on the product version, different versions of sen2cor should be used.
sen2cor_product() {
  # enable fallback
  if [ "true" == "${ENABLE_QI_DATA_FALLBACK:-true}" ]; then
    for datastrip_dir in "${temp_input}/${src_product_name}/DATASTRIP"/*; do
      mkdir -p "${datastrip_dir}/QI_DATA"
    done
  fi
  aux_data=$HOME/lib/python2.7/site-packages/sen2cor/aux_data

  processing_baseline=$(grep PROCESSING_BASELINE "$1"/*.xml | sed 's#.*<PROCESSING_BASELINE>\([^<]*\)</.*#\1#')

  # sen2cor 2.11.0 can process PSD >= 14.2 (processing_baseline>=02.05) but for
  # anything older we have to use sen2cor 2.5.5
  # https://sentinels.copernicus.eu/web/sentinel/user-guides/sentinel-2-msi/data-formats/xsd

  # shellcheck disable=SC2072
  if [[ "$processing_baseline" < "02.05" ]]; then
    sh /installer-2.5.5.run --target "$HOME"
    ln -snf /CCI-DATA-2.5.5/* "${aux_data}"

    # sen2cor-2.5.5 doesn't take an output_dir argument, so splice it into L2A_GIPP.xml
    sed "s#\(.*<Target_Directory>\)[^<]*\(</.*\)#\1${2}\2#" </L2A_GIPP-2.5.5.xml >/tmp/L2A_GIPP-2.5.5.xml

    sen2cor_args=(--GIP_L2A /tmp/L2A_GIPP-2.5.5.xml)
  else
    sh /installer-2.11.00.run --target "$HOME"
    ln -snf /CCI-DATA-2.11.00/* "${aux_data}"

    sen2cor_args=(--GIP_L2A /L2A_GIPP-2.11.00.xml --output_dir "$2")
  fi

  time "${HOME}/bin/L2A_Process" "${sen2cor_args[@]}" "${1}"
}

case "${src_product_name}" in
*_MSIL1C_*)
  sen2cor_product "${temp_input}/${src_product_name}" "${target}/"
  ;;
*_MSIL2A_*)
  echo "Detected L2A product, skipping sen2cor processing"
  mv "${temp_input}/${src_product_name}" "${target}/"
  ;;
*)
  echo "Unexpected product name did not match L1C or L2A, exiting"
  exit 1
  ;;
esac

# enable zip output
if [ "true" == "${ENABLE_ZIP_OUTPUT:-true}" ]; then
  dst_product=$(ls -1 ${target})
  cd "${target}/${dst_product}"
  zip -r "${target}/${dst_product}.zip" .
  cd ${target}
  # have two goes at deleting this - the first time occasionally is incomplete
  # though that may be a windows/docker only thing
  set +e
  rm -rf "${dst_product}"
  rm -rf "${dst_product}"
fi
