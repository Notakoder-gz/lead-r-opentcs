# OpenTCS Deployment Stack

This repository contains a unified deployment stack exclusively for **OpenTCS**. It provides the core OpenTCS Kernel, a lightweight Web Dashboard, and a browser-based VNC interface for the official Java clients.

## Architecture

1. **`opentcs_kernel`**: The core OpenTCS server running without a GUI. Exposes the Web API on port `55200` and RMI on `1099`.
2. **`opentcs_web`**: A custom Node.js/Express web frontend running on port `3000`. Connects to the Kernel's Web API to display real-time statuses of vehicles and transport orders.
3. **`opentcs_client_vnc`**: A Debian-based container running an X11 VNC server and noVNC (port `8080`). It contains the official OpenTCS Java clients (Plant Overview / Model Editor and Operations Desk). You can access these tools directly in your browser to edit the map or manage the fleet.

## Setup

1. Copy `.env.example` to `.env`.
2. Edit `.env` and set `HOST_IP` to your server's actual IP address.
3. Ensure the directories for `OPENTCS_CONFIG_DIR` and `OPENTCS_DATA_DIR` exist on your host.

## Running

Start the entire stack with Docker Compose:

```bash
docker compose up -d --build
```

## Access Points

* **Custom Web Dashboard:** `http://<HOST_IP>:3000`
* **Official OpenTCS Clients (noVNC):** `http://<HOST_IP>:8080/vnc.html`
  * Password for VNC: `opentcs`
  * Once inside, open a terminal and run `/home/opentcs/opentcs/startPlantOverview.sh` to edit the map.
* **OpenTCS Web API:** `http://<HOST_IP>:55200/v1/...`
