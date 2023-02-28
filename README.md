# Seagrass GeoData360 services

This repository contains CGI's open-source GeoData360 processing services for
Project Seagrass.

## Overview

The Project Seagrass services are designed to support identification,
monitoring, and measurement of seagrass in UK coastal waters.

This repository currently describes a supervised classification workflow,
including pre-processing of input data, training of a machine learning model
given some ground truth data, and use of the model to produce a map of seagrass.

The services are intended to be run as workflows on the [CGI GeoData360
platform](https://www.cgi.com/uk/en-gb/geodata360), but individual steps can be
developed and tested independently.

These services are still in development, and are regularly evolving. The steps
are implemented with a variety of tools, including [gdal](https://gdal.org/) and
[Orfeo Toolbox](https://www.orfeo-toolbox.org/). New tools, patterns, and
implementations are welcomed for integration.

## Input data &amp; acknowledgements

The training and classification steps require standardised inputs. These
currently include:

* Satellite imagery
    * Sentinel-2 L2A products
      ([sen2cor](https://step.esa.int/main/snap-supported-plugins/sen2cor/) is
      invoked if required)
    * Provided by the Copernicus programme
    * Reference: [https://sentinels.copernicus.eu/web/sentinel/missions/sentinel-2](https://sentinels.copernicus.eu/web/sentinel/missions/sentinel-2)
* Bathymetry data
    * GEBCO_2022 Grid
    * Reference: [https://www.gebco.net/data_and_products/gridded_bathymetry_data/](https://www.gebco.net/data_and_products/gridded_bathymetry_data/)
* Seagrass habitat suitability model
    * Provided by Project Seagrass and Swansea University
    * Reference: [https://www.frontiersin.org/articles/10.3389/fmars.2022.997831/full](https://www.frontiersin.org/articles/10.3389/fmars.2022.997831/full)
