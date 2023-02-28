import re
import sys
import xml.etree.ElementTree as ET
import zipfile

S2_ZIP = sys.argv[1]

min_x, min_y, max_x, max_y = None, None, None, None

with zipfile.ZipFile(S2_ZIP, 'r') as zip:
    GRANULE_XML_FILES = [f for f in zip.namelist() if re.compile('.*GRANULE/[^/]+/MTD_TL.xml$').match(f)]
    for GRANULE in GRANULE_XML_FILES:
        et = ET.fromstring(zip.read(GRANULE))

        # Find the number of pixels in this granule
        size_x = 10 * int(et.find('.//Tile_Geocoding/Size[@resolution="10"]/NROWS').text)
        size_y = 10 * int(et.find('.//Tile_Geocoding/Size[@resolution="10"]/NCOLS').text)

        # Find the upper-left corner of this granule
        ul_x = int(et.find('.//Tile_Geocoding/Geoposition[@resolution="10"]/ULX').text)
        ul_y = int(et.find('.//Tile_Geocoding/Geoposition[@resolution="10"]/ULY').text)

        # Find the bounding corners of the granule
        min_x = min([min_x, ul_x]) if min_x is not None else ul_x
        min_y = min([min_y, ul_y - size_y]) if min_y is not None else ul_y - size_y
        max_x = max([max_x, ul_x + size_x]) if max_x is not None else ul_x + size_x
        max_y = max([max_y, ul_y]) if max_y is not None else ul_y

print("%i %i %i %i" % (min_x, min_y, max_x, max_y))
