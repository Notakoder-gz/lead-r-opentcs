FROM ros:jazzy-ros-base

RUN apt-get update && apt-get install -y python3-pip && rm -rf /var/lib/apt/lists/*
RUN pip3 install --no-cache-dir --break-system-packages pyyaml requests

WORKDIR /app

COPY . /app/

CMD ["bash", "-c", "source /opt/ros/jazzy/setup.bash && python3 -u adapter.py"]
