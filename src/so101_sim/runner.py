from __future__ import annotations

import importlib.util

from so101_sim.config import load_config
from so101_sim.ros.contracts import arm_topics
from so101_sim.simulation.geometry import scene_geometry


def _dependency_status(module: str) -> str:
    return "ok" if importlib.util.find_spec(module) is not None else "missing"


def main() -> None:
    config = load_config()
    geometry = scene_geometry(config)

    print("arms-lab scaffold check")
    print(f"  genesis: {_dependency_status('genesis')}")
    print(f"  rclpy:   {_dependency_status('rclpy')}")
    print(f"  torch:   {_dependency_status('torch')}")
    print(f"  physics: {config['simulation']['physics_hz']} Hz")
    print(f"  servo:   {config['simulation']['servo_hz']} Hz")
    print(f"  device:  {config['simulation']['device']}")
    print(
        "  arm bases: "
        f"left=({geometry.left_arm.x:.3f}, {geometry.left_arm.y:.3f}) m, "
        f"right=({geometry.right_arm.x:.3f}, {geometry.right_arm.y:.3f}) m"
    )
    print(f"  left measured topic: {arm_topics('left_arm').measured_state}")
    print(f"  left ground truth:   {arm_topics('left_arm').ground_truth_state}")
    print("next implementation step: vendor pinned SO-101 assets and build the Genesis scene")


if __name__ == "__main__":
    main()
