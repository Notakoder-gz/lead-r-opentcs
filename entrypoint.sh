#!/bin/bash
set -e

# Copy default config and data if mounted directories are empty
if [ -z "$(ls -A /opt/opentcs/config)" ]; then
    echo "Config directory is empty. Copying defaults..."
    cp -r /opt/opentcs/default_config/. /opt/opentcs/config/
fi

if [ -z "$(ls -A /opt/opentcs/data)" ]; then
    echo "Data directory is empty. Copying defaults..."
    cp -r /opt/opentcs/default_data/. /opt/opentcs/data/
fi

# Pass the execution to the original startKernel.sh
exec ./startKernel.sh
