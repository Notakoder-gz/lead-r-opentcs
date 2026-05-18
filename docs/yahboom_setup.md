# Yahboom MicroROS-Pi5: Open-RMF Integration Guide

This document outlines the necessary steps and caveats for configuring Yahboom MicroROS-Pi5 robots (which utilize Raspberry Pi 5 and ESP32 for micro-ROS) to operate effectively within the OpenTCS + Open-RMF integration stack.

## 1. Hardware Overview
The Yahboom MicroROS-Pi5 robot stack typically involves:
*   **Raspberry Pi 5**: Runs ROS 2 (Humble/Jazzy depending on your image) and handles high-level control, LiDAR processing, and the primary ROS 2 agent.
*   **ESP32**: Serves as the motor/hardware controller and runs micro-ROS to communicate with the Raspberry Pi.

## 2. Software Configuration & Critical Issues

### The Multicast Network Storm Problem
By default, ROS 2 relies on DDS (specifically eProsima FastDDS or CycloneDDS) which uses **multicast UDP** for participant discovery. When connecting multiple robots to a shared network (e.g., your office Wi-Fi), the multicast traffic is broadcast to all devices on the network.

**The Issue**: The ESP32 micro-ROS node is highly sensitive to network flooding. A high volume of multicast ROS 2 discovery packets on the shared network will overwhelm the ESP32's network stack, causing the micro-ROS connection to drop, which results in the robot disconnecting or freezing.

### The Solution: Unicast FastDDS Configuration
To prevent the ESP32 from crashing, you **must disable multicast** on all ROS 2 nodes in the fleet, including the Open-RMF containers and the Raspberry Pi's on the robots.

You need to enforce a **Unicast-only** FastDDS profile on the robots.

#### Step-by-step for the Raspberry Pi on the Robot:
1.  Create a `fastdds_profiles.xml` file on the Raspberry Pi:
    ```xml
    <?xml version="1.0" encoding="UTF-8" ?>
    <profiles xmlns="http://www.eprosima.com/XMLSchemas/fastrtps_profiles">
        <participant profile_name="unicast_profile" is_default_profile="true">
            <rtps>
                <useBuiltinTransports>false</useBuiltinTransports>
                <userTransports>
                    <transport_id>udp_transport</transport_id>
                </userTransports>
            </rtps>
        </participant>
        <transport_descriptors>
            <transport_descriptor>
                <transport_id>udp_transport</transport_id>
                <type>UDPv4</type>
            </transport_descriptor>
        </transport_descriptors>
    </profiles>
    ```
2.  Set the environment variable before running your ROS 2 launch files on the robot:
    ```bash
    export FASTDDS_DEFAULT_PROFILES_FILE=/path/to/your/fastdds_profiles.xml
    export ROS_DOMAIN_ID=20 # Make sure this matches your .env in the server
    ```
    *(Note: Ensure this is added to `~/.bashrc` on the Raspberry Pi).*

## 3. Fleet Configuration
The `yahboom_rmf` adapter handles the registration of the robots in Open-RMF.

1. Edit `adapters/yahboom_rmf/robots_config.yaml` to define your fleet.
2. The `profile` section handles physical limitations (radius `0.3m`, max velocity `1.0m/s`). Adjust these if your exact Yahboom model has a different physical footprint.
3. Add or remove robots from the `robots` dictionary. Ensure the `name` (e.g., `yahboom_01`) exactly matches the name the robot broadcasts via Zenoh/ROS 2.

## 4. Workflow Check
1. Start the Yahboom robots. Confirm their internal micro-ROS agent is running.
2. Confirm the ROS 2 network on the Raspberry Pi is successfully publishing `tf`, `odom`, and `scan` without crashing the ESP32.
3. Start the Open-RMF + OpenTCS stack using `docker-compose up -d --build`.
4. Verify in the RMF Dashboard that both robots (e.g., `yahboom_01`, `yahboom_02`) appear online and are initialized at their respective waypoints.
