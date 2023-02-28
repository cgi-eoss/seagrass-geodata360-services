# Habitat Suitability Model

Collocation with a Sentinel-2 product of a previously calculated seagrass
habitat suitability model.

The low-resolution raster is clipped and reprojected to the CRS of the input
Sentinel-2 tile, filled and interpolated to a higher resolution to
ensure full coverage of the coastline, and converted to UInt64 by scaling 0-1 to
0-65536.

The habitat suitability model is sourced from [Bertelli, C. M., Bennett, W.,
Bull, J. C., Karunarathna, H., Reeve, D. E., & Unsworth, R. K. "Habitat
Suitability modelling for informing Zostera marina restoration in Wales"](https://www.projectseagrass.org/wp-content/uploads/2022/05/Habitat-Suitability-modelling-for-informing-Zostera-marina-restoration-in-Wales_WWF_Report-FINAL.pdf).
