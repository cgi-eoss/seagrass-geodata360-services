# Supervised Classification Training step

Trains a random forest model to be used for supervised classification.

## Inputs

- `INPUT`: Multiband GeoTIFF images to be used in training of the model
- `MASK`: Good/bad pixel masks, corresponding one-to-one with `INPUT`
- `STATISTICS`: (OPTIONAL) Band statistics for bands in all `INPUT` images. If
  given, entries must correspond with `TRAINING_FEATURES` parameter.
- `GROUND_TRUTH_SHAPEFILE`: A ground truth shapefile consisting of polygons
  with discrete classifications of attribute "MC_ID" .

## Outputs

- `MODEL`: Trained random forest model to be used for supervised classification.

- `CONFUSION_MATRIX`: Output file containing the confusion matrix or
  contingency table.

- `AUX_FILE`: An auxiliary file to track the inputs and parameters used in
  generation of the model.

## Parameters

- `TRAINING_SHAPEFILE_ATTR`: The attribute in the training data shapefile
  containing the classes to be detected and matched in the `INPUT` images.

  Default: "MC_ID"

- `TRAINING_FEATURES`: (OPTIONAL) Space-separated list of band numbers (
  0-indexed) to be used when training the classifier. This set should reference
  some or all bands available in the `INPUT` images and must have the same
  number of elements as the entries in the `STATISTICS` XML file (if provided).

  Default: All bands of the s2-seagrass-normalisation:4.0.0 step.

- `MAX_DEPTH`: (OPTIONAL) The depth of the tree. A low value will likely
  underfit and conversely a high value will likely overfit. The optimal value
  can be obtained using cross validation or other suitable methods.

  Default: 5

- `MIN_SAMPLES`: (OPTIONAL) If the number of samples in a node is smaller than
  this parameter, then the node will not be split. A reasonable value is a small
  percentage of the total data e.g. 1 percent.

  Default: 10

- `REGRESSION_ACCURACY`: If all absolute differences between an estimated value
  in a node and the values of the train samples in this node are smaller than
  this regression accuracy parameter, then the node will not be split.

  Default: 0

- `CATEGORICAL_CLUSTERS`: Cluster possible values of a categorical variable into
  K <= cat clusters to find a suboptimal split.

  Default: 10

- `SUBSET_SIZE`: (OPTIONAL) The size of the subset of features, randomly
  selected at each tree node, that are used to find the best split(s). If you
  set it to 0, then the size will be set to the square root of the total number
  of features.

  Default: 0

- `MAX_TREES`: (OPTIONAL) The maximum number of trees in the forest. Typically,
  the more trees you have, the better the accuracy. However, the improvement in
  accuracy generally diminishes and reaches an asymptote for a certain number of
  trees. Also to keep in mind, increasing the number of trees increases the
  prediction time linearly.

  Default: 100

- `SUFFICIENT_ACCURACY`: Sufficient accuracy (OOB error).

  Default: 0.01

- `RANDOM_SEED`: (OPTIONAL) A seed for random number generation. Used in the OTB
  applications SampleSelection and TrainVectorClassifier. If set, the same seed
  is used in both applications. If not set, each seed is chosen randomly.

  Default: <none>
