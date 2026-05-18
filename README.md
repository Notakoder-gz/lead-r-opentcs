# OpenTCS Deployment Stack

This repository contains a unified deployment stack exclusively for **OpenTCS**. It provides the core OpenTCS Kernel and a lightweight Web Dashboard.

## Architecture

1. **`opentcs_kernel`**: The core OpenTCS server running without a GUI. Exposes the Web API on port `55200` and RMI on `1099`.
2. **`opentcs_web`**: A custom Node.js/Express web frontend running on port `3000`. Connects to the Kernel's Web API to display real-time statuses of vehicles and transport orders.

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
* **OpenTCS Web API:** `http://<HOST_IP>:55200/v1/...`
* **Desktop Clients:** Use the official OpenTCS Client on your personal computer and connect to the Kernel via RMI (`<HOST_IP>:1099`).
