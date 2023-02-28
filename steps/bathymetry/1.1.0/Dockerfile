FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

# Use miniconda to manage dependencies, but remove it from the final image
#   1. Use miniconda to install the conda-env.yml environment
#   2. Export and unpoack the environment (conda-pack)
#   3. Remove miniconda
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && apt-get clean && rm -rf /var/lib/apt/lists/* \
    && curl -sLo /miniconda.sh https://repo.anaconda.com/miniconda/Miniconda3-py39_4.10.3-Linux-x86_64.sh \
    && bash /miniconda.sh -bfp /miniconda.tmp \
    && rm /miniconda.sh  \
    && bash -c '\
        source /miniconda.tmp/bin/activate \
        && conda install -c conda-forge conda-pack \
        && conda create -n tempenv -c conda-forge \
            python=3.10 \
            gdal=3.5.0 \
        && conda-pack -n tempenv -o /tmp/tempenv.tar' \
    && mkdir /conda  \
    && tar xf /tmp/tempenv.tar -C /conda \
    && bash -c 'source /conda/bin/activate && /conda/bin/conda-unpack' \
    && rm -rf /miniconda.tmp /tmp/tempenv.tar

RUN addgroup --system --gid 361 gaiascope \
    && adduser --system --uid 361 --gid 361 gaiascope
USER gaiascope
WORKDIR /home/gaiascope


RUN curl -sL -o /home/gaiascope/GEBCO_Bathymetric_UK_positive_01.tif https://nextcloud.observing.earth/s/LN52mjsiiiQ2iHP/download
COPY s2Extents.py s2ProductZones.py  /home/gaiascope/
COPY entrypoint.sh /

ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]