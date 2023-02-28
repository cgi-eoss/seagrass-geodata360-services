# Supervised Classification Model Generator

A workflow to train a supervised classification model on Sentinel-2 images
and ground truth data provided as a shapefile.

Sentinel-2 L1C or L2A are used as inputs and atmospherically corrected using
Sen2Cor if required.

Input images are transformed to multi-band GeoTIFFs for training and used to
generate a model suitable for implementation in other classification workflows.

##### The input products are:

- Single or multiple Sentinel-2 L1C or L2A tiles
- Optional CCI land cover data
- Ground truth shapefile containing polygons with classification attribute

##### The output products are:

- MODEL
- CONFUSION MATRIX
- AUX_FILE

## Parameters

- `TRAINING_SHAPEFILE_ATTR`: (OPTIONAL) The attribute in the training data
  shapefile containing the classes to be detected and matched in the `S2_L1C`
  images.

  Default: "MC_ID"

## Steps

- `s2-seagrass-normalisation:2.0.5`
  - `sen2cor:2.0.2`
  - `habitat-suitability-model:1.1.0`
  - `bathymetry:1.1.0`
  - `s2-l2a-geotiff:1.1.0`
  - `s2-seagrass-normalisation:4.0.2`
- `compute-images-statistics:1.1.0`
- `merge-images-statistics:1.0.0`
- `supervised-classification-training:3.1.0`
