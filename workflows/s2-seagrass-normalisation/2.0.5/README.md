# Sentinel-2 Seagrass Normalisation

A workflow taking a Sentinel-2 L1C SAFE product, applying a standard set of
normalisation techniques, and producing analysis-ready data.

The output is provided in Cloud-Optimised GeoTIFF format at 10m resolution.

##### The input products are:

- L2A atmospheric correction and scene classification (sen2cor)
- Habitat suitability model band (HSM)

##### The output products are:

- `S2_GEOTIFF`: Normalised Sentinel-2 product in Cloud-Optimised GeoTIFF format.
- `MASK`: Corresponding cloud mask.

## Parameters

- `NODATA_MASK_BAND`: (OPTIONAL) A band name from the INPUT images in which 0
  values indicate nodata for all bands in the image, i.e. a mask. This should
  reference a named band from the normalised images.

  Default: SCL

- `MASK_EXPRESSION`: (MANDATORY) C Custom bandmaths to be applied to the output
  product to generate a mask product. This argument is provided to gdal_calc.py,
  and bands are selected A..Z based on their index in the product.

  For example, to use the SCL band (`O`) to select only water pixels less
  than 10 metres deep (bathymetry band `S`), where the CLD band (`N`) with a
  threshold:
    ```
    (O==6) & (S<10) & (N<5)
    ```

## Steps

- `sen2cor:2.0.1`
- `habitat-suitability-model:1.0.0`
- `bathymetry:1.0.1`
- `s2-l2a-geotiff:1.1.0`
- `s2-seagrass-normalisation:4.0.2`
