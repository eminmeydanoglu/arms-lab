# arms-lab

Bimanual SO-101 simulation environment built around Genesis and ROS 2.

The frozen design specification is in [`nihai.md`](./nihai.md).

## Run

Host requirement: Docker Engine with Docker Compose.

```bash
./run.sh
```

Optional modes:

```bash
./run.sh --headless
./run.sh --cpu
./run.sh --gpu
./run.sh --reset-build
```

The container owns ROS 2 Jazzy, Python 3.12, uv and Genesis dependencies so the host stays minimal.

## First implementation milestones

1. Vendor and pin the official SO-101 URDF/STL assets under `third_party/so101/` with source commit and license.
2. Build the Genesis world: 1.30 m × 0.75 m table, two SO-101 bases 0.40 m apart, primitive manipulation objects.
3. Implement the SO-101 actuator layer: position targets, torque-speed limit, damping/friction and backlash.
4. Implement the encoder layer: 12-bit quantization, configurable jitter and latency.
5. Add the ROS 2 adapter with noisy joint states and separate ground-truth joint states.
6. Add regression tests for FK, joint limits, servo response, encoder behavior and bimanual workspace.

Configuration starts in `config/default.yaml`. Simulation code should remain independent from the ROS adapter so alternative interfaces can be added later.
