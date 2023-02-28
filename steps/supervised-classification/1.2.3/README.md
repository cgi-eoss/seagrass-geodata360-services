# Supervised Classification step

Apply a pre-trained supervised classification model to a multi-band GeoTIFF.

## Inputs

- `INPUT`: A multi-band GeoTIFF image to be classified.
- `MASK`: Corresponding pixel mask for INPUT (e.g. cloud).
- `MODEL`: A pre-trained supervised classification model.

## Outputs

- `CLASSIFIED`: Single band GeoTIFF classified into values corresponding to
 shapefile classes used in model training.
- `CONFIDENCE`: Single band TIFF displaying classification confidence 
(proportion of votes for the majority class).
