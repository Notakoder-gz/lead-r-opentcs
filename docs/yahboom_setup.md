# Yahboom MicroROS-Pi5: OpenTCS Direct Integration Guide

This document outlines the necessary steps and caveats for configuring Yahboom MicroROS-Pi5 robots (which utilize Raspberry Pi 5 and ESP32 for micro-ROS) to operate directly within the OpenTCS integration stack, completely bypassing Open-RMF.

## 1. Hardware Overview
The Yahboom MicroROS-Pi5 robot stack typically involves:
*   **Raspberry Pi 5**: Runs ROS 2 (Humble/Jazzy) and handles high-level control, LiDAR processing, and the primary ROS 2 agent.
*   **ESP32**: Serves as the motor/hardware controller and runs micro-ROS to communicate with the Raspberry Pi.

## 2. Software Configuration & Critical Issues

### The Multicast Network Storm Problem
By default, ROS 2 relies on DDS (specifically eProsima FastDDS or CycloneDDS) which uses **multicast UDP** for participant discovery. When connecting multiple robots to a shared network (e.g., your office Wi-Fi), the multicast traffic is broadcast to all devices on the network.

**The Issue**: The ESP32 micro-ROS node is highly sensitive to network flooding. A high volume of multicast ROS 2 discovery packets on the shared network will overwhelm the ESP32's network stack, causing the micro-ROS connection to drop, which results in the robot disconnecting or freezing.

### The Solution: Unicast FastDDS Configuration
To prevent the ESP32 from crashing, you **must disable multicast** on all ROS 2 nodes in the fleet, including the Raspberry Pi's on the robots.

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
    export ROS_DOMAIN_ID=20
    ```
    *(Note: Ensure this is added to `~/.bashrc` on the Raspberry Pi).*

## 3. OpenTCS Direct Adapter Configuration
The `yahboom_opentcs` adapter handles the direct communication between ROS 2 topics and the OpenTCS Web API.

1. Edit `adapters/yahboom_opentcs/robots_config.yaml` to define your robots.
2. Add or remove robots from the `robots` dictionary. Ensure the `ros_topic_prefix` matches the namespace of the ROS 2 topics published by each robot.
3. The OpenTCS Plant Overview client must have vehicles created whose exact names match the names defined in the `robots` dictionary (e.g., `yahboom_01`).

## 4. Simplified Adapter Notes
For this initial Direct OpenTCS approach, the `yahboom_opentcs` adapter implements a **simplified bridge**.

* It successfully connects to ROS 2 topics to read telemetry (odom/battery) and forwards it to OpenTCS.
* It successfully connects to the OpenTCS Web API and polls for incoming Transport Orders.
* **Important:** To physically drive the Yahboom robots, the `process_order` function inside `adapters/yahboom_opentcs/adapter.py` must be hooked up to your ROS 2 Navigation Stack (Nav2). OpenTCS sends logical points (e.g., "Point-0005"), which the adapter must translate to physical `(x, y)` coordinates and send as a `NavigateToPose` Action Goal to the robot's Nav2 server. Currently, this function acts as a hook/logger to verify the integration is working before deep Nav2 configuration.

## 5. Workflow Check
1. Start the Yahboom robots. Confirm their internal micro-ROS agent is running.
2. Confirm the ROS 2 network on the Raspberry Pi is successfully publishing `tf`, `odom`, and `scan` without crashing the ESP32.
3. Start the OpenTCS stack and the adapter using `docker compose up -d --build`.
4. Create the corresponding vehicles in the OpenTCS Plant Overview Model Editor.
5. Verify in OpenTCS that the robots become available and start receiving coordinates and routing orders.
