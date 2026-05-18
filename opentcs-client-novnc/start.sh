#!/bin/bash

export USER=opentcs
export HOME=/home/opentcs

# Remove old VNC locks
rm -f /tmp/.X1-lock /tmp/.X11-unix/X1

# Start VNC Server
vncserver :1 -geometry 1280x800 -depth 24 -localhost no -SecurityTypes VncAuth

# Wait for X to start
sleep 2

# Start Openbox window manager
DISPLAY=:1 openbox-session &

# Start noVNC
websockify --web /usr/share/novnc 8080 localhost:5901
