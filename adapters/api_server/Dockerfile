FROM ghcr.io/open-rmf/rmf-web/api-server:latest

# Switch to root to install packages
USER root

# Install the Zenoh RMW implementation for ROS 2 Jazzy
RUN apt-get update && apt-get install -y ros-jazzy-rmw-zenoh-cpp && rm -rf /var/lib/apt/lists/*

# The original image CMD or ENTRYPOINT will still handle the startup
