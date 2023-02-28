# Confidence Masking Step

Merges single band Classification layer and single band Confidence layer to remove all but target class and pixels
below the defined confidence threshold are masked out.

## Inputs

- `CLASSIFIED`: Single band TIFF classified into values corresponding to shapefile classes used in model training.
- `CONFIDENCE`: Single band TIFF displaying classification confidence (proportion of votes for the majority class).

## Outputs

- `SINGLE_CLASS_CONFIDENCE`: Single band TIFF displaying confidence of a single class defined by CLASS_ID. Low
  classification confidence pixels filtered out, according to value of CONF_MASK_THRESHOLD.

## Parameters

- `CONF_MASK_THRESHOLD`: Value between 0 and 1 defining threshold classification confidence (proportion of votes for the majority class)
  for a given pixel below which will be filtered out from the classification image.

  Default: 0.1

- `CLASS_ID`: Integer value identifying the desired class to be displayed in the confidence map. Value should match one of those
  defined by the input model.

  Default: 1
