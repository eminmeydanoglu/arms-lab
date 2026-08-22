import pytest

from so101_sim.config import load_config
from so101_sim.simulation.geometry import scene_geometry


def test_default_arm_base_poses_match_design() -> None:
    geometry = scene_geometry(load_config())
    assert geometry.left_arm.x == pytest.approx(-0.255)
    assert geometry.right_arm.x == pytest.approx(-0.255)
    assert geometry.left_arm.y == pytest.approx(0.200)
    assert geometry.right_arm.y == pytest.approx(-0.200)


def test_default_spawn_zone_matches_design() -> None:
    geometry = scene_geometry(load_config())
    assert geometry.spawn_zone == pytest.approx((-0.075, 0.125, -0.120, 0.120))
