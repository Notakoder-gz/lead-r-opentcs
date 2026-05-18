FROM ghcr.io/open-rmf/rmf-web/api-server:latest

# Switch to root to ensure we can copy and set permissions
USER root

# Copy the FastDDS profile directly into the image to avoid volume mount permission errors
COPY fastdds_profiles.xml /fastdds_profiles.xml
RUN chmod 644 /fastdds_profiles.xml

# Revert to the default non-root user (usually 'ubuntu' in these Jazzy base images) for security
USER ubuntu

# The original image CMD or ENTRYPOINT will still handle the startup
