from so101_sim.ros.contracts import JOINT_NAMES, arm_topics


def test_ros_contract_has_measured_and_ground_truth_topics() -> None:
    left = arm_topics("left_arm")
    right = arm_topics("right_arm")

    assert left.target == "/left_arm/joint_targets"
    assert left.measured_state == "/left_arm/joint_states"
    assert left.ground_truth_state == "/sim/left_arm/ground_truth/joint_states"
    assert right.target == "/right_arm/joint_targets"
    assert right.measured_state == "/right_arm/joint_states"
    assert right.ground_truth_state == "/sim/right_arm/ground_truth/joint_states"
    assert len(JOINT_NAMES) == 6
