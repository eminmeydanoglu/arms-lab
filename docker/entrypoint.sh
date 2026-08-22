#!/usr/bin/env bash
set -euo pipefail

source /opt/ros/jazzy/setup.bash

if [[ -f /opt/arms-lab/ros_ws/install/setup.bash ]]; then
  source /opt/arms-lab/ros_ws/install/setup.bash
fi

exec "$@"
