import faulthandler
import glob
import os
import xml.etree.ElementTree as ET
from collections import namedtuple
from pathlib import Path
from timeit import default_timer as timer

from osgeo import gdal

gdal.UseExceptions()
faulthandler.enable()

# Ordered list of S-2 L2A product bands
L2A_BANDS = [
    'B1', 'B2', 'B3', 'B4',
    'B5', 'B6', 'B7', 'B8',
    'B8A', 'B9', 'B11', 'B12',
    'AOT', 'CLD', 'SCL', 'SNW', 'WVP',
]

HSM_BANDS = [
    'HSM'
]

BATHY_BANDS = [
    'BATHY'
]

OUTPUT_BANDS = L2A_BANDS + HSM_BANDS + BATHY_BANDS

DatasetBand = namedtuple('DatasetBand', ['num', 'name', 'mean_viewing_zenith_angle', 'mean_viewing_azimuth_angle'])


def main():
    ###################
    # Step parameters #
    ###################

    compress = os.getenv('COMPRESS', 'DEFLATE')
    unscale = os.getenv('UNSCALE', 'true')

    ######################
    # Inputs and outputs #
    ######################

    in_l2a_dir = Path('/in/S2_L2A')
    in_hsm_dir = Path('/in/HSM')
    in_bathy_dir = Path('/in/BATHY')
    out_dir = Path('/out/S2_GEOTIFF')
    work_dir = Path('/out/.work')

    out_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    s2a_contents = list(in_l2a_dir.iterdir())
    assert len(s2a_contents) == 1, \
        "Expected a single directory or zip file in /in/S2_L2A, but got %s elements" % len(s2a_contents)
    s2_l2a = s2a_contents[0]

    hsm_tif_contents = glob.glob("%s/*.tif" % in_hsm_dir)
    assert len(hsm_tif_contents) == 1, \
        "Expected a single .tif /in/HSM, but got %s elements" % len(hsm_tif_contents)
    hsm = hsm_tif_contents[0]

    bathy_tif_contents = glob.glob("%s/*.tif" % in_bathy_dir)
    assert len(bathy_tif_contents) == 1, \
        "Expected a single .tif /in/BATHY, but got %s elements" % len(bathy_tif_contents)
    bathy = bathy_tif_contents[0]

    translate_options = gdal.TranslateOptions(format='VRT')
    s2_l2a_vrt_path = "%s/s2_l2a.vrt" % work_dir
    gdal.Translate(s2_l2a_vrt_path, str(s2_l2a), options=translate_options)
    hsm_vrt_path = "%s/hsm.vrt" % work_dir
    gdal.Translate(hsm_vrt_path, str(hsm), options=translate_options)
    bathy_vrt_path = "%s/bathy.vrt" % work_dir
    gdal.Translate(bathy_vrt_path, str(bathy), options=translate_options)

    product_name = s2_l2a.name.removesuffix('.tif')
    output_vrt = "%s/%s.vrt" % (work_dir, product_name)
    output_tif = "%s/%s.tif" % (out_dir, product_name)
    output_band_els = {}

    # Load the main product tif VRT to build the primary details
    s2_l2a_vrt = ET.parse(s2_l2a_vrt_path)
    vrt_dataset_el = ET.Element(s2_l2a_vrt.getroot().tag, s2_l2a_vrt.getroot().attrib)
    for el in s2_l2a_vrt.findall('./*'):
        if el.tag == 'VRTRasterBand':
            output_band_els[L2A_BANDS[int(el.find('./SimpleSource/SourceBand').text) - 1]] = el
        elif el.tag != 'OverviewList':
            vrt_dataset_el.append(el)

    # Add the hsm band, but clean it up for consistency with the others
    hsm_vrt = ET.parse(hsm_vrt_path)
    for el in hsm_vrt.findall('./*'):
        if el.tag == 'VRTRasterBand':
            # TODO Reconsider adding the extra attributes and provide an .aux.xml sidecar file
            el.remove(el.find('ColorInterp'))
            el.remove(el.find('NoDataValue'))
            el.append(ET.Element('Metadata'))
            band_name_el = ET.Element('MDI', {'key': 'BANDNAME'})
            band_name_el.text = 'HSM'
            el.find('Metadata').append(band_name_el)
            el.set('dataType', 'UInt16')
            output_band_els[HSM_BANDS[int(el.find('./SimpleSource/SourceBand').text) - 1]] = el
        else:
            # TODO Check other VRT elements against the s2_l2a_vrt? We'll just trust that they're identical...
            pass

    # Add the bathy band, and clean it up for consistency with the others
    bathy_vrt = ET.parse(bathy_vrt_path)
    for el in bathy_vrt.findall('./*'):
        if el.tag == 'VRTRasterBand':
            # TODO Reconsider adding the extra attributes and provide an .aux.xml sidecar file
            el.remove(el.find('ColorInterp'))
            el.remove(el.find('NoDataValue'))
            el.append(ET.Element('Metadata'))
            band_name_el = ET.Element('MDI', {'key': 'BANDNAME'})
            band_name_el.text = 'BATHY'
            el.find('Metadata').append(band_name_el)
            el.set('dataType', 'UInt16')
            output_band_els[BATHY_BANDS[int(el.find('./SimpleSource/SourceBand').text) - 1]] = el
        else:
            # TODO Check other VRT elements against the s2_l2a_vrt? We'll just trust that they're identical...
            pass

    # Add bands in the correct order
    for idx, band in enumerate(OUTPUT_BANDS):
        pos = idx + 1
        # Deep-copy (via to/from string) the VRTRasterBand element,
        # and update its band number for the output product
        vrt_raster_band_el = ET.fromstring(ET.tostring(output_band_els[band]))
        vrt_raster_band_el.set('band', str(pos))
        vrt_dataset_el.append(vrt_raster_band_el)

    ET.ElementTree(vrt_dataset_el).write(output_vrt)

    print("Writing normalised Sentinel-2 GeoTIFF product: %s" % output_tif)
    start = timer()
    gdal.Translate(
        output_tif,
        gdal.Open(output_vrt),
        format='COG',
        creationOptions=[
            "BIGTIFF=YES",
            "COMPRESS=%s" % compress,
            "NUM_THREADS=ALL_CPUS",
        ],
        unscale=True if unscale == "true" else False
    )
    end = timer()
    print("Completed writing normalised Sentinel-2 GeoTIFF product in %s seconds" % (end - start))


if __name__ == "__main__":
    main()
