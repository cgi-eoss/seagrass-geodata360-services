import os
import sys
from pathlib import Path

import dask
import joblib
import numpy
import rioxarray
import xarray

use_mask = True if os.getenv("USE_MASK", "true") == "true" else False
output_proba = True if os.getenv("OUTPUT_PROBA", "true") == "true" else False


def load_source(product_file, training_features, mask_file):
    src = rioxarray.open_rasterio(product_file, chunks={'x': 500, 'y': 500})

    original_band_count = src.shape[0]
    src = src.isel(band=training_features)
    print("Opened source image with %s bands, %s selected (%s x %s pixels)" % (original_band_count, src.shape[0],
                                                                               src.shape[1], src.shape[2]))

    src_stacked = src.stack(z=['x', 'y']).transpose('z', ...)

    if use_mask:
        print("Loading mask: %s" % mask_file)
        mask = rioxarray.open_rasterio(mask_file, chunks={'x': 500, 'y': 500})
        mask_stacked = mask.isel(band=0, drop=True).stack(z=['x', 'y']).transpose('z', ...)
        src_pixels = src_stacked[(mask_stacked == 1).compute()]
    else:
        src_pixels = src_stacked

    return src.coords, src_pixels


def do_class_prediction(src_coords, src_pixels, clf, classified_file):
    class_prediction = xarray.apply_ufunc(lambda data, classifier: classifier.predict(data),
                                          src_pixels,
                                          kwargs={'classifier': clf},
                                          input_core_dims=[['band']],
                                          output_dtypes=['uint8'],
                                          dask='parallelized')

    class_prediction_full = xarray.DataArray(0,
                                             coords={'y': src_coords['y'], 'x': src_coords['x']},
                                             dims=['y', 'x'])

    print("Expanding classification result to output product coordinates")
    result = class_prediction.unstack('z').combine_first(class_prediction_full).astype('uint8').transpose('y', 'x')

    print("Writing class prediction output product: %s" % classified_file)
    result.rio.write_nodata(0, encoded=True, inplace=True)
    result.rio.to_raster(classified_file, compress='DEFLATE')


def do_class_probabilities(src_coords, src_pixels, clf, class_proba_file):
    class_proba = xarray.apply_ufunc(lambda data, classifier: classifier.predict_proba(data),
                                     src_pixels,
                                     kwargs={'classifier': clf},
                                     input_core_dims=[['band']],
                                     output_core_dims=[['class_proba']],
                                     output_dtypes=['float32'],
                                     dask_gufunc_kwargs={'output_sizes': {'class_proba': 4}},
                                     dask='parallelized')

    class_proba_full = xarray.DataArray(numpy.nan,
                                        coords={'band': [1, 2, 3, 4], 'y': src_coords['y'],
                                                'x': src_coords['x']},
                                        dims=['band', 'y', 'x']).astype('float32')

    print("Expanding class probabilities result to output product coordinates")
    proba_result = class_proba.unstack('z').rename({'class_proba': 'band'}).assign_coords(
        band=('band', [1, 2, 3, 4])).combine_first(class_proba_full).transpose('band', 'y', 'x')

    print("Writing class probabilities output product: %s" % class_proba_file)
    proba_result.rio.write_nodata(numpy.nan, encoded=True, inplace=True)
    proba_result.rio.to_raster(class_proba_file, compress='DEFLATE')


def classify(training_feature_idxs, classifier_file, product_file, mask_file, classified_dir, class_probability_dir):
    training_features = list(map(int, training_feature_idxs.split(' ')))

    # Load pickled classifier instance
    clf = joblib.load(classifier_file)
    print("Loaded trained classifier of type: " + type(clf).__name__)
    print(clf)

    with dask.config.set(**{'array.slicing.split_large_chunks': True}):
        product_name = Path(product_file).name.removesuffix('.tif')
        classified_file = Path(classified_dir).joinpath("%s_classified.tif" % product_name)
        class_proba_file = Path(class_probability_dir).joinpath("%s_class_probability.tif" % product_name)

        print("Loading input product: %s" % product_file)
        src_coords, src_pixels = load_source(product_file, training_features, mask_file)

        print("Classifying product pixels: %s" % product_file)
        do_class_prediction(src_coords, src_pixels, clf, classified_file)

        if output_proba:
            print("Calculating class probabilities: %s" % product_file)
            do_class_probabilities(src_coords, src_pixels, clf, class_proba_file)


if __name__ == '__main__':
    classify(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6])
