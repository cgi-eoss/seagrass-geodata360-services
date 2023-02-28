# Sen2Cor

Takes a Sentinel-2 L1C product and uses the Sen2Cor algorithm to perform
atmospheric, terrain and cirrus correction to generate a Sentinel-2 L2A product.

This version uses either
[Sen2Cor 2.11.00](https://step.esa.int/main/snap-supported-plugins/sen2cor/sen2cor-v2-11/)
or [Sen2Cor 2.5.5](https://step.esa.int/main/snap-supported-plugins/sen2cor/sen2cor_v2-5-5/)
depending on the input product baseline. CCI land cover data is baked in to the
image.

## Inputs

- `S2_PRODUCT`: Sentinel-2 Level 1C or 2A product directory or zip archive.

## Outputs

- `S2_L2A`: Sentinel-2 Level 2A product directory, or zip archive if
  `ENABLE_ZIP_OUTPUT` is true.

## Parameters

- `ENABLE_QI_DATA_FALLBACK`: (OPTIONAL) Enables the creation of blank directory
  to allow certain old data to be processed. Default: true.

- `ENABLE_ZIP_OUTPUT`: (OPTIONAL) Enables the output product to be zipped.
  Default: true.
