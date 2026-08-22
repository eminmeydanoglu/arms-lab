# First implementation steps

This file is intentionally short. The architectural decisions live in `nihai.md`; this is the implementation order.

## 1. Pin and vendor SO-101 assets

Copy the selected SO-101 URDF and STL assets from TheRobotStudio/SO-ARM100 at an exact upstream commit into `third_party/so101/`. Preserve licensing and add `SOURCE_COMMIT`.

Acceptance: an automated test can locate the URDF, all referenced meshes exist, and no runtime internet access is required.

## 2. Build the static Genesis scene

Create the 1.30 m x 0.75 m table, then instantiate two SO-101 robots at the geometry calculated by `so101_sim.simulation.geometry`:

- left base: x=-0.255 m, y=+0.200 m
- right base: x=-0.255 m, y=-0.200 m
- both face +X

Add the primitive object library and reset/spawn support.

Acceptance: both arms and a medium box appear in one Genesis rigid-body world without interpenetration at startup.

## 3. Implement SO-101 actuation

Add a servo layer between joint targets and Genesis position control. Start from the configured STS3215 7.4 V baseline: PD gains, torque-speed envelope, damping, friction, armature, joint limits, and backlash.

Acceptance: a 30-degree step command does not teleport, respects configured speed/torque limits, and converges near the target.

## 4. Implement measured encoder state

Keep Genesis joint state as ground truth. Build a separate encoder pipeline with 12-bit quantization, calibration offset hook, jitter, sample-and-hold, and latency.

Acceptance: measured state and ground truth are both available and differ when the sensor model is enabled.

## 5. Add the ROS 2 adapter

Use the topic names in `so101_sim.ros.contracts`.

- subscribe to `/left_arm/joint_targets` and `/right_arm/joint_targets` using `trajectory_msgs/msg/JointTrajectory`
- publish measured `/left_arm/joint_states` and `/right_arm/joint_states` using `sensor_msgs/msg/JointState`
- publish exact `/sim/<arm>/ground_truth/joint_states`
- publish `/clock`, `/tf`, and `/tf_static`

Acceptance: an external ROS 2 controller can command both arms without importing Genesis.

## 6. Add fidelity/regression tests

Add tests for joint limits, FK known poses, encoder quantization, servo step response, table/gripper collision, bimanual core-zone reachability, and ROS smoke behavior.

Only after these pass should optional ros2_control, MoveIt, cameras, or GPU profiles be added.
