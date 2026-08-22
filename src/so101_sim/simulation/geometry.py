from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ArmBasePose:
    x: float
    y: float
    z: float = 0.0
    yaw: float = 0.0


@dataclass(frozen=True)
class SceneGeometry:
    left_arm: ArmBasePose
    right_arm: ArmBasePose
    spawn_zone: tuple[float, float, float, float]


def scene_geometry(config: dict[str, Any]) -> SceneGeometry:
    table = config["scene"]["table"]
    arms = config["scene"]["arms"]
    zone = config["scene"]["bimanual_spawn_zone"]

    # World origin is the table-surface center. +X points toward the front edge,
    # +Y points to the left, and +Z points upward.
    base_x = -(float(table["depth_m"]) / 2.0) + float(arms["rear_offset_m"])
    half_separation = float(arms["separation_m"]) / 2.0

    return SceneGeometry(
        left_arm=ArmBasePose(x=base_x, y=half_separation),
        right_arm=ArmBasePose(x=base_x, y=-half_separation),
        spawn_zone=(
            float(zone["x_min_m"]),
            float(zone["x_max_m"]),
            float(zone["y_min_m"]),
            float(zone["y_max_m"]),
        ),
    )
