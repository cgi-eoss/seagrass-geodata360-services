from collections import defaultdict
from collections import namedtuple

import faulthandler
import glob
import os
import xml.etree.ElementTree as ET
from osgeo import gdal
from pathlib import Path
from timeit import default_timer as timer
from zipfile import ZipFile

gdal.UseExceptions()
faulthandler.enable()

# Ordered list of S-2 L2A product bands
BANDS = [
    'B1', 'B2', 'B3', 'B4',
    'B5', 'B6', 'B7', 'B8',
    'B8A', 'B9', 'B11', 'B12',
    'AOT', 'CLD', 'SCL', 'SNW', 'WVP',
]

DatasetBand = namedtuple('DatasetBand', ['num', 'name', 'offset'])


def main():
    ###################
    # Step parameters #
    ###################

    compress = os.getenv('COMPRESS', 'DEFLATE')
    apply_offset = os.getenv('APPLY_OFFSET', 'true')

    ######################
    # Inputs and outputs #
    ######################

    in_dir = Path('/in/INPUT')
    out_dir = Path('/out/S2_GEOTIFF')
    work_dir = Path('/out/.work')

    out_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    in_contents = list(in_dir.iterdir())
    assert len(in_contents) == 1, \
        "Expected a single directory or zip file in /in/INPUT, but got %s elements" % len(in_contents)

    src_product = in_contents[0]

    if src_product.suffix == '.zip' or src_product.suffix == '.ZIP':
        with ZipFile(src_product, 'r') as s2_zip:
            print("Unzipping Sentinel-2 product: %s" % src_product)
            s2_zip.extractall("%s/s2_product/" % work_dir)
            s2_dataset = glob.glob("%s/s2_product/*MTD_*.xml" % work_dir)[0]
    else:
        s2_dataset = glob.glob("%s/*MTD_*.xml" % src_product)[0]

    print("Reading data from Sentinel-2 dataset: %s" % s2_dataset)

    product_ds = gdal.Open(s2_dataset)

    src_product_name = str(product_ds.GetMetadata().get('PRODUCT_URI',
                                                        product_ds.GetMetadata().get('PRODUCT_URI_2A', None))
                           ).removesuffix('.SAFE')
    src_product_datetime = str(product_ds.GetMetadata()['PRODUCT_START_TIME'])

    print(src_product_name, src_product_datetime)

    # Look up BOA_ADD_OFFSET values for each band, for product baseline >= 04.00
    src_product_metadata_xml = str(product_ds.GetMetadata('xml:SENTINEL2')[0])
    src_product_metadata_et = ET.fromstring(src_product_metadata_xml)

    boa_offset_values = {}
    boa_offset_els = src_product_metadata_et.findall(
        './{*}General_Info/{*}Product_Image_Characteristics/{*}BOA_ADD_OFFSET_VALUES_LIST/{*}BOA_ADD_OFFSET')
    if len(boa_offset_els) > 0:
        for boa_offset_el in boa_offset_els:
            spectral_info_el = src_product_metadata_et.find(
                "./{*}General_Info/{*}Product_Image_Characteristics/""{*}Spectral_Information_List"
                "/{*}Spectral_Information[@bandId='%s']" % boa_offset_el.get('band_id'))
            band_name = spectral_info_el.get('physicalBand')
            offset = boa_offset_el.text
            boa_offset_values[band_name] = offset

    utms = defaultdict(dict)
    vrt_options = gdal.BuildVRTOptions(xRes=10, yRes=10)

    for subdataset, subds_description in product_ds.GetSubDatasets():
        product_level, path, subds_name, subds_utm = subdataset.split(':')
        assert (product_level == 'SENTINEL2_L2A'), \
            "Unable to process data with level %s from path %s" % (product_level, path)

        # don't process the preview dataset bands
        if subds_name == 'TCI' or subds_name == 'PREVIEW':
            continue

        print("Loading bands from S-2 subdataset: %s" % subdataset)

        bands = []
        subds = gdal.Open(subdataset)
        for i in range(1, subds.RasterCount + 1):
            band = subds.GetRasterBand(i)
            bandname = band.GetMetadata()['BANDNAME']

            # The band in the S-2 product - correcting for the fact that L2A products don't have B10
            s2_band_index = BANDS.index(bandname) if BANDS.index(bandname) <= 9 else BANDS.index(bandname) + 1

            bands.append(DatasetBand(i, bandname, boa_offset_values.get(bandname, None)))
        del subds

        vrt = gdal.BuildVRT("%s/%s_%s.vrt" % (work_dir, subds_utm, subds_name), subdataset, options=vrt_options)
        utms[subds_utm][vrt.GetDescription()] = bands
        del vrt
    del product_ds

    for utm, vrts in utms.items():
        assert (
                len(vrts.keys()) % 3 == 0
        ), "Expected 3 resolution datasets per UTM zone in Sentinel-2 L2A product, but found %s. " \
           "Is this a multi-granule product?" % len(vrts.keys())

        utm_vrt = "%s/%s_main.vrt" % (work_dir, utm)
        print("Merging VRTs and ordering bands to %s" % utm_vrt)
        merge_vrts(vrts, utm_vrt, apply_offset)

        utm_geotiff = "%s/%s_%s.tif" % (out_dir, src_product_name, utm)
        print("Writing Sentinel-2 GeoTIFF product: %s" % utm_geotiff)
        start = timer()
        gdal.Translate(
            utm_geotiff,
            utm_vrt,
            format='COG',
            creationOptions=[
                "BIGTIFF=YES",
                "COMPRESS=%s" % compress,
                "NUM_THREADS=ALL_CPUS",
            ],
            metadataOptions=[
                "TIFFTAG_DOCUMENTNAME=%s" % src_product_name,
                "TIFFTAG_DATETIME=%s" % src_product_datetime,
            ],
        )
        end = timer()
        print("Completed writing Sentinel-2 GeoTIFF product in %s seconds" % (end - start))


def merge_vrts(vrts, dst, apply_offset):
    vrt_dataset_el = None
    vrt_raster_band_els = {}
    for vrt in sorted(vrts.keys()):
        tree = ET.parse(vrt)
        if vrt_dataset_el is None:
            # Copy common VRT properties from the first (10m) dataset
            vrt_dataset_el = ET.Element('VRTDataset', {
                'rasterXSize': tree.getroot().attrib['rasterXSize'],
                'rasterYSize': tree.getroot().attrib['rasterYSize']
            })
            vrt_dataset_el.append(tree.find('./SRS'))
            vrt_dataset_el.append(tree.find('./GeoTransform'))

        for band in vrts[vrt]:
            if band.name in vrt_raster_band_els.keys():
                continue

            pos = BANDS.index(band.name) + 1
            print("Indexing band %s (dataset band %s) from VRT %s" % (band.name, band.num, vrt))

            # Deep-copy (via to/from string) the VRTRasterBand element,
            # and update its band number for the output product
            vrt_raster_band_el = ET.fromstring(ET.tostring(tree.find("./VRTRasterBand[@band='%s']" % band.num)))
            vrt_raster_band_el.set('band', str(pos))

            band_metadata_el = ET.Element('Metadata')
            band_name_el = ET.Element('MDI', {'key': 'BANDNAME'})
            band_name_el.text = band.name
            band_metadata_el.append(band_name_el)
            if band.offset:
                band_offset_el = ET.Element('MDI', {'key': 'BOA_ADD_OFFSET'})
                band_offset_el.text = band.offset
                band_metadata_el.append(band_offset_el)

                if apply_offset == 'true':
                    print("Adding offset of %s to %s" % (band.offset, band.name))
                    offset_el = ET.Element('Offset')
                    offset_el.text = band.offset
                    vrt_raster_band_el.append(offset_el)

            vrt_raster_band_el.append(band_metadata_el)
            vrt_raster_band_els[band.name] = vrt_raster_band_el

    # Add the ordered band VRTRasterBand elements to the XML product
    for idx, band in enumerate(BANDS):
        print("Adding band %s as band %s" % (band, idx + 1))
        vrt_dataset_el.append(vrt_raster_band_els[band])

    ET.ElementTree(vrt_dataset_el).write(dst)


if __name__ == "__main__":
    main()
