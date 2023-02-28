# We depend on the official OTB image as it handles some complex environment configuration
FROM docker.io/orfeotoolbox/otb:8.0.1

# Additional dependencies
RUN apt-get update && apt-get install -y --no-install-recommends\
 time \
 zip\
 unzip\
 && apt-get clean && rm -rf /var/lib/apt/lists/*

#######################
# Configure environment
RUN addgroup --system --gid 361 gaiascope \
    && adduser --system --uid 361 --gid 361 gaiascope
USER gaiascope
WORKDIR /home/gaiascope

COPY entrypoint.sh /home/worker/processor/
ENTRYPOINT ["bash","/home/worker/processor/entrypoint.sh"]
