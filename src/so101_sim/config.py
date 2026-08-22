from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = PROJECT_ROOT / "config" / "default.yaml"


def _positive(config: dict[str, Any], path: tuple[str, ...]) -> float:
    value: Any = config
    for key in path:
        value = value[key]
    number = float(value)
    if number <= 0:
        dotted = ".".join(path)
        raise ValueError(f"{dotted} must be positive, got {number}")
    return number


def validate_config(config: dict[str, Any]) -> None:
    physics_hz = _positive(config, ("simulation", "physics_hz"))
    servo_hz = _positive(config, ("simulation", "servo_hz"))
    joint_state_hz = _positive(config, ("ros", "joint_state_hz"))

    if servo_hz > physics_hz:
        raise ValueError("simulation.servo_hz cannot exceed simulation.physics_hz")
    if joint_state_hz > physics_hz:
        raise ValueError("ros.joint_state_hz cannot exceed simulation.physics_hz")

    width = _positive(config, ("scene", "table", "width_m"))
    depth = _positive(config, ("scene", "table", "depth_m"))
    separation = _positive(config, ("scene", "arms", "separation_m"))
    rear_offset = _positive(config, ("scene", "arms", "rear_offset_m"))

    if separation >= width:
        raise ValueError("arm separation must be smaller than table width")
    if rear_offset >= depth:
        raise ValueError("arm rear offset must be smaller than table depth")

    bits = int(config["encoder"]["bits"])
    if bits < 1:
        raise ValueError("encoder.bits must be >= 1")

    joints = config["robot"]["joint_names"]
    if len(joints) != 6 or len(set(joints)) != 6:
        raise ValueError("SO-101 joint_names must contain six unique names")


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    configured = path or os.getenv("ARMS_LAB_CONFIG")
    config_path = Path(configured) if configured else DEFAULT_CONFIG
    if not config_path.is_absolute():
        config_path = PROJECT_ROOT / config_path

    with config_path.open("r", encoding="utf-8") as handle:
        config: dict[str, Any] = yaml.safe_load(handle)

    if os.getenv("ARMS_LAB_HEADLESS") == "1":
        config["simulation"]["headless"] = True
    if device := os.getenv("ARMS_LAB_DEVICE"):
        config["simulation"]["device"] = device

    validate_config(config)
    return config
