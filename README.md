# lead-r-opentcs
My first git project of opentcs deployment

## Monorepo Architecture
This repository now functions as a unified deployment source.
The custom fleet adapters (`yahboom_rmf` and `opentcs_bridge`) are stored in the `adapters/` directory.
When deploying via `docker compose up -d`, Portainer or your local Docker engine will automatically build these images from the source if they do not exist, ensuring maximum reliability and ease of updates.

## Configuration
Before running the stack, you must set up your environment variables:
1. Copy `.env.example` to `.env`
2. Adjust the absolute paths to point to your server directories (e.g., `/home/amy/...`)

## Micro-ROS & FastDDS Networking Note
By default, ROS 2 FastDDS utilizes multicast UDP for node discovery. This can lead to severe network flooding over Wi-Fi, which often crashes lightweight microcontrollers like the ESP32 running micro-ROS due to buffer overflows.

To mitigate this, a custom `fastdds_profiles.xml` is included and applied to all relevant ROS 2 containers via the `FASTDDS_DEFAULT_PROFILES_FILE` environment variable. This profile restricts maximum message sizes and prevents built-in multicast storms, safeguarding the hardware on the local network.

## Virtual Robots not appearing in Open-RMF
If virtual robots from OpenTCS do not appear in the Open-RMF dashboard:
1. Ensure the names of the robots in OpenTCS (e.g. `yahboom_01`) exactly match the names defined in the configuration files (`adapters/opentcs_bridge/fleet_config.yaml` and `adapters/yahboom_rmf/yahboom_adapter.py`).
2. Verify that the Zenoh namespaces match across both the publisher in the OpenTCS bridge and the subscriber in the Yahboom adapter.