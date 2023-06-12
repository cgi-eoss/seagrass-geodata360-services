import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import rioxarray
from geocube.api.core import make_geocube


def extract_training_samples(product_path, mask_path, ground_truth, ground_truth_attr, out_dir):
    print("Extracting training samples from %s" % product_path)
    print("Masking input product with %s" % mask_path)
    print("Correlating with ground truth data %s" % ground_truth)

    # Load ground truth
    gt_vector = gpd.read_file(ground_truth)

    print("Opened ground truth vector file with %s shapes" % (len(gt_vector)))

    # Load product and mask to verify shape (if not coordinates)
    src = rioxarray.open_rasterio(product_path, chunks={'x': 500, 'y': 500})
    mask = rioxarray.open_rasterio(mask_path, chunks={'x': 500, 'y': 500})

    assert (src.shape[1] == mask.shape[1]) and (src.shape[2] == mask.shape[2]) and (src.rio.crs == mask.rio.crs)

    print("Opened source image with %s bands (%s x %s pixels)" % (src.shape[0], src.shape[1], src.shape[2]))

    print("Rasterising the vector data, and reshaping to the source product")
    gt_raster = make_geocube(gt_vector, measurements=[ground_truth_attr], like=mask)

    print("Stacking data arrays (flattening x,y)")
    gt_stacked = gt_raster.stack(z=('x', 'y'))[ground_truth_attr]
    src_stacked = src.stack(z=('x', 'y')).transpose()
    mask_stacked = mask.isel(band=0, drop=True).stack(z=('x', 'y')).transpose()

    print("Computing overlap of source product mask and ground truth")
    indexer = ((gt_stacked >= 0) & (mask_stacked == 1)).compute()
    X = src_stacked[indexer]
    y = gt_stacked[indexer]

    print("Our X matrix is sized: " + str(X.shape))
    print("Our y array is sized: " + str(y.shape))

    product_name = Path(product_path).name.removesuffix('.tif')
    samples_file = Path(out_dir).joinpath("%s_samples.npz" % product_name)

    print("Writing samples and aligned ground_truth to %s" % samples_file)
    np.savez_compressed(samples_file, samples=X, ground_truth=y)


if __name__ == '__main__':
    extract_training_samples(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
