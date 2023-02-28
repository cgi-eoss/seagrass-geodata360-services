import re
import sys
import xml.etree.ElementTree as ET
import zipfile

S2_ZIP = sys.argv[1]

with zipfile.ZipFile(S2_ZIP, 'r') as zip:
    GRANULE_XML_FILES = [f for f in zip.namelist() if re.compile('.*GRANULE/[^/]+/MTD_TL.xml$').match(f)]
    epsgs = set(
        [ET.fromstring(zip.read(GRANULE)).find('.//HORIZONTAL_CS_CODE').text for GRANULE in GRANULE_XML_FILES])

print(' '.join(epsgs))
