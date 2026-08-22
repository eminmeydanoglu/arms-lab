from pathlib import Path

import yaml


def test_default_config_has_locked_v1_values() -> None:
    config = yaml.safe_load(Path("config/default.yaml").read_text(encoding="utf-8"))

    assert config["simulation"]["physics_hz"] == 500
    assert config["simulation"]["servo_hz"] == 100
    assert config["scene"]["table"]["width_m"] == 1.30
    assert config["scene"]["table"]["depth_m"] == 0.75
    assert config["scene"]["arms"]["separation_m"] == 0.40
    assert config["encoder"]["bits"] == 12
    assert config["servo"]["stall_torque_nm"] == 1.91
