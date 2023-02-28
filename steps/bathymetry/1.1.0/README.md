# Bathymetry

Collocation with a Sentinel-2 product of UK bathymetry data.

An adjusted version of the GEBCO bathymetry layer is included. Positive values
have been removed, and negative values have been converted to positive values.

This modified bathymetry raster is clipped and reprojected to the CRS of the
input Sentinel-2 tile, and resampled to 10m pixels.
