import os
import sys
import yaml
import time
import requests
import threading
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from sensor_msgs.msg import BatteryState

def load_config(config_path):
    if not os.path.exists(config_path):
        print(f"?? WARNING: Config {config_path} missing.")
        return {'opentcs': {'host': 'http://localhost:55200'}, 'robots': {}}
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

class YahboomRobot(Node):
    def __init__(self, name, config, opentcs_url):
        super().__init__(f'yahboom_opentcs_adapter_{name}')
        self.robot_name = name
        self.config = config
        self.opentcs_url = opentcs_url

        self.odom_sub = self.create_subscription(
            Odometry,
            self.config.get('ros_odom_topic', f'/{name}/odom'),
            self.odom_callback,
            10
        )
        self.battery_sub = self.create_subscription(
            BatteryState,
            self.config.get('ros_battery_topic', f'/{name}/battery'),
            self.battery_callback,
            10
        )
        self.cmd_pub = self.create_publisher(
            Twist,
            self.config.get('ros_cmd_vel_topic', f'/{name}/cmd_vel'),
            10
        )

        # Internal state
        self.current_position = "Point-0000"
        self.battery_level = 100
        self._last_reported_position = ""
        self._last_reported_battery = -1

        # Background polling thread for OpenTCS orders
        self.poll_rate = self.config.get('poll_rate_hz', 1.0)
        self.thread = threading.Thread(target=self.opentcs_loop, daemon=True)
        self.thread.start()

    def odom_callback(self, msg):
        # SIMPLIFIED: In a real implementation, you would use Nav2 and map (x,y) coordinates
        # to OpenTCS Plant Overview logical Point names.
        self.current_position = f"Point-{int(msg.pose.pose.position.x):04d}"

    def battery_callback(self, msg):
        self.battery_level = int(msg.percentage * 100)

    def update_opentcs_state(self):
        url = f"{self.opentcs_url}/v1/vehicles/{self.robot_name}"
        data = {
            "currentPosition": self.current_position,
            "energyLevel": self.battery_level,
            "state": "IDLE"
        }
        try:
            # We execute the network call to update OpenTCS
            requests.put(url, json=data, timeout=1.0)
        except Exception as e:
            # We mute connection refused errors to avoid log spam if OpenTCS is restarting
            pass

    def opentcs_loop(self):
        while rclpy.ok():
            # 1. Update OpenTCS with our state (Throttled here in the loop instead of slamming it in odom callback)
            if self.current_position != self._last_reported_position or self.battery_level != self._last_reported_battery:
                self.update_opentcs_state()
                self._last_reported_position = self.current_position
                self._last_reported_battery = self.battery_level

            # 2. Poll for new orders
            url = f"{self.opentcs_url}/v1/vehicles/{self.robot_name}"
            try:
                res = requests.get(url, timeout=1.0)
                if res.status_code == 200:
                   self.process_order(res.json())
            except Exception as e:
                pass

            time.sleep(1.0 / self.poll_rate)

    def process_order(self, data):
        # SIMPLIFIED APPROACH:
        # We successfully receive the order from OpenTCS (e.g., destinations).
        # To actually move the Yahboom robot, you must connect this logic to ROS 2 Nav2.
        # This function serves as the hook where you will parse `data['destinations']`
        # and send a NavigateToPose Action goal to the Raspberry Pi.

        # For now, we just print the received order to prove the bridge is working.
        if 'transportOrder' in data and data['transportOrder']:
             self.get_logger().info(f"Received Order from OpenTCS: {data['transportOrder']}")

def main():
    rclpy.init(args=sys.argv)

    config_path = os.environ.get('ROBOTS_CONFIG_PATH', 'robots_config.yaml')
    config = load_config(config_path)

    opentcs_url = config.get('opentcs', {}).get('host', 'http://localhost:55200')
    if 'OPENTCS_URL' in os.environ:
        opentcs_url = os.environ['OPENTCS_URL']

    robots = config.get('robots', {})
    if not robots:
        print("❌ No robots defined in config.")
        sys.exit(1)

    print("?? Starting Yahboom OpenTCS Direct ROS 2 Adapter.")
    nodes = []
    executors = rclpy.executors.MultiThreadedExecutor()

    for r_name, r_conf in robots.items():
        node = YahboomRobot(r_name, r_conf, opentcs_url)
        nodes.append(node)
        executors.add_node(node)

    try:
        executors.spin()
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        for node in nodes:
            node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
