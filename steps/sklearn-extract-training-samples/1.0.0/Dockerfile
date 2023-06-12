FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Use miniconda to manage dependencies, but remove it from the final image
#   1. Use miniconda to install the locked conda environment
#   2. Export and unpoack the environment (conda-pack)
#   3. Remove miniconda
COPY conda-lock.yml /tmp/conda-lock.yml
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    time \
    unzip \
    && apt-get clean && rm -rf /var/lib/apt/lists/* \
    && curl -sLo /miniconda.sh https://repo.anaconda.com/miniconda/Miniconda3-py39_23.1.0-1-Linux-x86_64.sh \
    && bash /miniconda.sh -bfp /miniconda.tmp \
    && rm /miniconda.sh  \
    && bash -c '\
        source /miniconda.tmp/bin/activate \
        && conda install -n base -c conda-forge conda-lock conda-pack \
        && conda-lock install -n tempenv /tmp/conda-lock.yml \
        && conda-pack -n tempenv -o /tmp/tempenv.tar' \
    && mkdir /conda  \
    && tar xf /tmp/tempenv.tar -C /conda \
    && bash -c 'source /conda/bin/activate && /conda/bin/conda-unpack' \
    && rm -rf /miniconda.tmp /tmp/tempenv.tar /tmp/conda-lock.yml

RUN addgroup --system --gid 361 gaiascope \
    && adduser --system --uid 361 --gid 361 gaiascope
USER gaiascope
WORKDIR /home/gaiascope

COPY entrypoint.sh extract_training_samples.py /
ENTRYPOINT ["/bin/bash","/entrypoint.sh"]
