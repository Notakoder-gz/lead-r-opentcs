FROM ghcr.io/open-rmf/rmf/rmf_demos:jazzy-rmf-latest

# Install Zenoh and any Python dependencies needed for the bridge
RUN pip3 install --no-cache-dir eclipse-zenoh pyyaml requests

WORKDIR /app
COPY . /app/

# By default, start the adapter
CMD ["bash", "-c", "source /opt/ros/jazzy/setup.bash && python3 yahboom_adapter.py"]