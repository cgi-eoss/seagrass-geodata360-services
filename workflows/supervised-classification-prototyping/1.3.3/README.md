# Supervised Classification

A workflow to apply a pre-trained supervised classification model to a
 normalised multi-band GeoTIFF.

##### The input products are:

- A multi-band GeoTIFF image to be classified.
- A corresponding pixel mask for INPUT (e.g. cloud).
- A pre-trained supervised classification model.

##### The output products are:

- CLASSIFIED: Single band scene classified into values corresponding to the
 classifications of the training data used in generation of the model. 
- CONFIDENCE:  Single band TIFF displaying classification confidence 
(proportion of votes for the majority class).
- SINGLE_CLASS_CONFIDENCE: Single band TIFF displaying confidence of a single class defined by CLASS_ID. Low
  classification confidence pixels filtered out, according to value of CONF_MASK_THRESHOLD.
## Steps and Parameters

- supervised-classification - 1.2.3
- confidence-masking - 2.0.1
 