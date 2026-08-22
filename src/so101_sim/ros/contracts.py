from __future__ import annotations

from dataclasses import dataclass

JOINT_NAMES = (
    "shoulder_pan",
    "shoulder_lift",
    "elbow_flex",
    "wrist_flex",
    "wrist_roll",
    "gripper",
)

CLOCK_TOPIC = "/clock"
TF_TOPIC = "/tf"
TF_STATIC_TOPIC = "/tf_static"
OBJECT_GROUND_TRUTH_TOPIC = "/sim/ground_truth/objects"


@dataclass(frozen=True)
class ArmTopics:
    target: str
    measured_state: str
    ground_truth_state: str


def arm_topics(arm: str) -> ArmTopics:
    if arm not in {"left_arm", "right_arm"}:
        raise ValueError("arm must be 'left_arm' or 'right_arm'")
    return ArmTopics(
        target=f"/{arm}/joint_targets",
        measured_state=f"/{arm}/joint_states",
        ground_truth_state=f"/sim/{arm}/ground_truth/joint_states",
    )
