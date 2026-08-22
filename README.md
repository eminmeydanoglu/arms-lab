# arms-lab

Bimanual SO-101 simulation environment built around Genesis and ROS 2.

The frozen design specification is in [`nihai.md`](./nihai.md).

## Run

Host requirement: Docker Engine with Docker Compose v2.

```bash
./run.sh
```

Optional modes:

```bash
./run.sh --headless
./run.sh --cpu
./run.sh --reset-build
```

The initial portable baseline is CPU-only. A GPU profile should be added only after CUDA, PyTorch and Genesis versions are pinned and tested together.

The container owns ROS 2 Jazzy, Python 3.12, uv and Genesis dependencies so the host stays minimal.

## Scaffold status

The repository currently provides the deployment/configuration skeleton, not the completed simulation. `./run.sh` builds the environment and runs a smoke check for dependencies, geometry and ROS contracts.

Implemented scaffold pieces:

- Ubuntu 24.04 + ROS 2 Jazzy container
- Python 3.12 + uv project environment
- Genesis 1.3.1 and CPU PyTorch dependency source
- CycloneDDS middleware
- canonical `config/default.yaml`
- table/arm placement geometry helper
- fixed ROS topic contracts for commands, noisy state and ground truth
- initial configuration/geometry/contract tests

The next implementation order is documented in [`FIRST_STEPS.md`](./FIRST_STEPS.md).
