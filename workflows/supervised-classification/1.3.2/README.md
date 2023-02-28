# Supervised Classification

A workflow to apply a pre-trained supervised classification model to an input
Sentinel-2 image.

Sentinel-2 L1C or L2A are used as inputs and atmospherically corrected using
Sen2Cor if required.

Input images are transformed to multi-band GeoTIFFs before applying the
provided model to produce a classified output GeoTIFF.

##### The input products are:

- Single Sentinel-2 L1C or L2A tile
- Pre-trained supervised classification model

##### The output products are:

- `CLASSIFIED`: Single band scene classified into values corresponding to the
  classifications of the training data used in generation of the model
- `CONFIDENCE`:  Single band TIFF displaying classification confidence
    (proportion of votes for the majority class).
- `SINGLE_CLASS_CONFIDENCE`: Single band TIFF displaying confidence of a single class defined by CLASS_ID. Low
  classification confidence pixels filtered out, according to value of CONF_MASK_THRESHOLD.

## Steps and Parameters

- `s2-seagrass-normalisation:2.0.4`
  - `sen2cor:2.0.1`
  - `habitat-suitability-model:1.0.0`
  - `bathymetry:1.0.1`
  - `s2-l2a-geotiff:1.1.0`
  - `s2-seagrass-normalisation:4.0.2`
- `supervised-classification:1.2.3`
- `confidence-masking:2.0.1`

 