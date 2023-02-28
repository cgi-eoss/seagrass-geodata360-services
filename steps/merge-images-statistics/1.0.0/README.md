# Merge image statistics XMLs

Merge previously-computed band statistics from a stack of images.

Takes one or more outputs of the compute-images-statistics Step, and computes
the per-band mean, min, max, and standard deviation.

Output is in XML format, equivalent to the OTB ComputeImageStatistics
application.

## Inputs

- `INPUT`: One or more outputs from the compute-images-statistics Step, to be
  merged to provide aggregate statistics for a large dataset.

## Outputs

- `IMAGES_STATISTICS`: XML file containing feature statistics for each band:
  mean, min, max and standard deviation.
