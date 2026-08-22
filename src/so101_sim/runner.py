from __future__ import annotations

import os
from pathlib import Path

import yaml


def load_config() -> dict:
    path = Path(os.getenv("ARMS_LAB_CONFIG", "config/default.yaml"))
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def main() -> None:
    config = load_config()
    if os.getenv("ARMS_LAB_HEADLESS"):
        config["simulation"]["headless"] = True
    if os.getenv("ARMS_LAB_DEVICE"):
        config["simulation"]["device"] = os.environ["ARMS_LAB_DEVICE"]

    print("arms-lab scaffold is ready")
    print(f"physics_hz={config['simulation']['physics_hz']}")
    print(f"device={config['simulation']['device']}")
    print("next: load SO-101 assets, build Genesis scene, then attach ROS 2 adapter")


if __name__ == "__main__":
    main()
