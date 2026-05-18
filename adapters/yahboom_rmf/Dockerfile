FROM ghcr.io/open-rmf/rmf/rmf_demos:jazzy-rmf-latest

# Install pip3 and any Python dependencies needed for the bridge
# Ubuntu 24.04 (Jazzy) enforces PEP-668, so --break-system-packages is required for global Docker installs
RUN apt-get update && apt-get install -y python3-pip && rm -rf /var/lib/apt/lists/*
RUN pip3 install --no-cache-dir --break-system-packages eclipse-zenoh pyyaml requests

WORKDIR /app
COPY . /app/

# By default, start the adapter
CMD ["bash", "-c", "source /opt/ros/jazzy/setup.bash && python3 yahboom_adapter.py"]