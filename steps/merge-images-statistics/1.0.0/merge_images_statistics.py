import collections
import faulthandler
import glob
import logging
import xml.etree.ElementTree as ET
from collections import namedtuple
from pathlib import Path
from timeit import default_timer as timer

import numpy as np

faulthandler.enable()
logging.basicConfig(level=logging.INFO)

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

    ######################
    # Inputs and outputs #
    ######################

    in_dir = Path('/in/INPUT')
    out_dir = Path('/out/IMAGES_STATISTICS')
    work_dir = Path('/out/.work')

    out_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    input_files = glob.glob("%s/*.xml*" % in_dir)
    assert len(input_files) >= 1, \
        "Expected at least one .xml file in /in/INPUT, but got %s" % len(input_files)

    logging.info("Merging statistics from %s files", len(input_files))

    product_band_statistics = collections.defaultdict(list)

    for f in input_files:
        logging.info("Reading statistics from %s", f)

        stats = ET.parse(f).getroot()

        samples = stats.get('samples', None)
        assert samples is not None, \
            "Input statistics file %s must contain a 'samples' attribute to support merging" % f

        mean_els = stats.findall("./Statistic[@name='mean']/StatisticVector")
        min_els = stats.findall("./Statistic[@name='min']/StatisticVector")
        max_els = stats.findall("./Statistic[@name='max']/StatisticVector")
        stddev_els = stats.findall("./Statistic[@name='stddev']/StatisticVector")

        statistic_lengths = {len(i) for i in [mean_els, min_els, max_els, stddev_els]}
        assert len(statistic_lengths) == 1, \
            "Expected all Statistic elements in file %s to have same length, but got %s" % (
                f, [len(i) for i in [mean_els, min_els, max_els, stddev_els]])

        # TODO Validate band counts across files

        for i in range(0, next(iter(statistic_lengths))):
            product_band_statistics[i].append(ProductStats(
                samples=int(samples),
                mean=float(mean_els[i].get('value')),
                min=float(min_els[i].get('value')),
                max=float(max_els[i].get('value')),
                stddev=float(stddev_els[i].get('value')),
            ))

    # Prepare output XML document
    feature_statistics = ET.Element('FeatureStatistics')

    # If these statistics were calculated for a single product, keep the sample count so we can merge with others later
    if len(input_files) == 1:
        feature_statistics.set('samples', str(next(iter(product_band_statistics.items()))[1][0].samples))

    mean_el = ET.SubElement(feature_statistics, 'Statistic', {'name': 'mean'})
    min_el = ET.SubElement(feature_statistics, 'Statistic', {'name': 'min'})
    max_el = ET.SubElement(feature_statistics, 'Statistic', {'name': 'max'})
    stddev_el = ET.SubElement(feature_statistics, 'Statistic', {'name': 'stddev'})

    total_start = timer()
    for band_idx, band_stats in product_band_statistics.items():
        logging.info("Calculating full-stack statistics for band %s", band_idx)

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
    logging.info("Merged all statistics in %s seconds", (total_end - total_start))

    ET.ElementTree(feature_statistics).write("%s/images_statistics.xml" % out_dir)


if __name__ == "__main__":
    main()
