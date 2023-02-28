import collections

import dask
import faulthandler
import glob
import logging
import numpy as np
import os
import rasterio
import rioxarray
import warnings
import xarray
import xml.etree.ElementTree as ET

from collections import namedtuple
from pathlib import Path
from timeit import default_timer as timer

faulthandler.enable()
logging.basicConfig(level=logging.INFO)

Product = namedtuple('Product', ['name', 'file', 'datetime'])
ProductStats = namedtuple('ProductStats', ['samples', 'mean', 'min', 'max', 'stddev'])


def pooled_standard_deviation(samples, stddevs, band_mean):
    a = 0
    b = 0
    c = (np.sum(samples) * np.float_power(band_mean, 2))

    for i in range(0, len(samples)):
        a += samples[i] - 1
        b += (np.float_power(stddevs[i], 2) * (samples[i] - 1)) + (np.float_power(band_mean, 2) * samples[i])

    return np.sqrt(np.divide(1, a) * (b - c))


def main():
    ###################
    # Step parameters #
    ###################

    mask_band = os.getenv('MASK_BAND', 'SCL')
    compute_bands = [int(i) for i in
                     os.getenv('BAND_NUMBERS', '0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18').split()]

    ######################
    # Inputs and outputs #
    ######################

    in_dir = Path('/in/INPUT')
    out_dir = Path('/out/IMAGES_STATISTICS')
    work_dir = Path('/out/.work')

    out_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    product_files = glob.glob("%s/*.tif" % in_dir)
    assert len(product_files) >= 1, \
        "Expected at least one .tif file in /in/INPUT, but got %s" % len(product_files)

    products = []
    stack_bands = []
    stack_dtype = ""

    logging.info("Loading and verifying bands and dtypes for %s images", len(product_files))

    # Check that we can read each product, and verify that they have the same bands
    bands_check = None
    dtype_check = None

    for product_file in product_files:
        logging.debug("Loading file %s", product_file)
        with rasterio.open(product_file, driver='GTiff') as dataset:
            stack_bands.clear()
            for i in range(0, dataset.count):
                if 'BANDNAME' in dataset.tags(i + 1):
                    stack_bands.append(dataset.tags(i + 1)['BANDNAME'])
                else:
                    stack_bands.append("BAND_%s" % (i + 1))
            if bands_check:
                assert bands_check == stack_bands, f"Bands of file {product_file} ({stack_bands}) are different from " \
                                                   f"other files ({bands_check}) "
            else:
                bands_check = stack_bands

            stack_dtype = dataset.dtypes[0]
            if dtype_check:
                assert dtype_check == stack_dtype, f"dtypes of file {product_file} ({stack_dtype}) is different from " \
                                                   f"other files ({dtype_check}) "
            else:
                dtype_check = stack_dtype

            products.append(Product(name=dataset.tags()['TIFFTAG_DOCUMENTNAME'],
                                    file=product_file,
                                    datetime=np.datetime64(dataset.tags()['TIFFTAG_DATETIME'])))

    logging.info("Computing statistics for %s images, which have bands: %s", len(products), stack_bands)
    logging.info("Statistics will be computed for bands: %s", compute_bands)

    mask = dict(band=(stack_bands.index(mask_band)))

    # Calculate statistics per-product & per-band, and we'll merge after
    product_band_statistics = collections.defaultdict(list)

    stats_start = timer()
    for product in products:
        product_start = timer()
        img: xarray.DataArray = rioxarray.open_rasterio(product.file,
                                                        lock=False,
                                                        cache=False,
                                                        chunks={'band': 1,  # computing statistics per band
                                                                'x': 'auto',
                                                                'y': 'auto'})
        img = img.where(img[mask] != 0)

        samples = img.isel(band=stack_bands.index(mask_band)).count().compute().item()
        band_img = img.isel(band=compute_bands, drop=True)

        # Some chunks may be all-NaN, so just suppress the warning
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=RuntimeWarning, message='All-NaN slice encountered')

            band_mean = band_img.mean(dim=['x', 'y']).compute().data
            band_min = band_img.min(dim=['x', 'y']).compute().data
            band_max = band_img.max(dim=['x', 'y']).compute().data
            band_stddev = band_img.std(dim=['x', 'y']).compute().data

        for idx, band_num in enumerate(compute_bands):
            band_name = stack_bands[band_num]
            stats = ProductStats(
                samples=samples,
                mean=band_mean[idx],
                min=band_min[idx],
                max=band_max[idx],
                stddev=band_stddev[idx]
            )
            logging.info("Product %s band %s stats: %s", product.name, band_name, stats)
            product_band_statistics[band_name].append(stats)

        product_end = timer()
        logging.info("Product %s stats calculated in %s seconds", product.name, (product_end - product_start))

    stats_end = timer()

    logging.info("Calculated statistics for %s bands in %s products in %s seconds", len(product_band_statistics.keys()),
                 len(products), (stats_end - stats_start))

    # Prepare XML document
    feature_statistics = ET.Element('FeatureStatistics')

    mean_el = ET.SubElement(feature_statistics, 'Statistic', {'name': 'mean'})
    min_el = ET.SubElement(feature_statistics, 'Statistic', {'name': 'min'})
    max_el = ET.SubElement(feature_statistics, 'Statistic', {'name': 'max'})
    stddev_el = ET.SubElement(feature_statistics, 'Statistic', {'name': 'stddev'})

    total_start = timer()
    for band_num in compute_bands:
        band_name = stack_bands[band_num]
        logging.info("Calculating full-stack statistics for band %s", band_name)

        band_stats = product_band_statistics[band_name]

        samples = [s.samples for s in band_stats]
        means = [s.mean for s in band_stats]
        mins = [s.min for s in band_stats]
        maxs = [s.max for s in band_stats]
        stddevs = [s.stddev for s in band_stats]

        band_mean = np.average(a=means, weights=samples).item()
        band_min = np.min(mins).item()
        band_max = np.max(maxs).item()
        band_stddev = pooled_standard_deviation(samples, stddevs, band_mean).item()

        mean_el.append(ET.Element('StatisticVector', {'value': str(band_mean)}))
        min_el.append(ET.Element('StatisticVector', {'value': str(band_min)}))
        max_el.append(ET.Element('StatisticVector', {'value': str(band_max)}))
        stddev_el.append(ET.Element('StatisticVector', {'value': str(band_stddev)}))

    total_end = timer()
    logging.info("Computed all image statistics in %s seconds", (total_end - total_start))

    if len(products) == 1:
        output_filename = Path(products[0].file).name.replace('.tif', '_statistics.xml')
        # Emit the sample count so we can merge with others later
        feature_statistics.set('samples', str(next(iter(product_band_statistics.items()))[1][0].samples))
    else:
        output_filename = "images_statistics.xml"
    ET.ElementTree(feature_statistics).write("%s/%s" % (out_dir, output_filename))


if __name__ == "__main__":
    main()
