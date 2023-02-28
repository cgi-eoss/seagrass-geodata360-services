# Sentinel-2 normalisation step

Merges the input data for seagrass processing in a predictable way, i.e. with
deterministic GeoTIFF band order. Adds HSM as additional band to the input
Sentinel-2 scene.

Builds a custom mask product to distinguish 'interesting' pixels from clouds,
cloud shadows, and other unwanted pixels.

## Inputs

- `S2_L2A`: Full Sentinel-2 product in GeoTIFF format.
- `HSM`: Interpolated Habitat Suitability Model in GeoTIFF format.

## Outputs

- `S2_GEOTIFF`: Normalised Sentinel-2 product in Cloud-Optimised GeoTIFF format.
- `MASK`: Corresponding cloud mask.

## Parameters

- `MASK_EXPRESSION`: (MANDATORY) Custom bandmaths to be applied to the output
  product to generate a mask product. This argument is provided to gdal_calc.py,
  and available bands are accessible as A..Z based on their index in the
  product.

  For example, to use the SCL band (`O`) to select only water pixels and the
  CLD band (`N`) with a threshold:
    ```
    (O==6) & (N<5)
    ```

- `COMPRESS`: (OPTIONAL) The desired compression for the data in the GeoTIFF
  product. See https://gdal.org/drivers/raster/cog.html for the available
  options. Default: DEFLATE

- `UNSCALE`: (OPTIONAL) If true, the output GeoTIFF will be 'unscaled' - any
  configured data offset or scale will be applied to the data values directly in
  the output. Negative values will be clipped to 0.

  Default: true
