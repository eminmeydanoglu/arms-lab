from so101_sim.config import load_config


def test_default_config_has_locked_v1_values() -> None:
    config = load_config()

    assert config["simulation"]["physics_hz"] == 500
    assert config["simulation"]["servo_hz"] == 100
    assert config["scene"]["table"]["width_m"] == 1.30
    assert config["scene"]["table"]["depth_m"] == 0.75
    assert config["scene"]["arms"]["separation_m"] == 0.40
    assert config["encoder"]["bits"] == 12
    assert config["servo"]["stall_torque_nm"] == 1.91
    assert len(config["robot"]["joint_names"]) == 6
