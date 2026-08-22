#!/usr/bin/env bash
set -euo pipefail

export ARMS_LAB_DEVICE="${ARMS_LAB_DEVICE:-cpu}"
export ARMS_LAB_HEADLESS="${ARMS_LAB_HEADLESS:-0}"

RESET_BUILD=0

for arg in "$@"; do
  case "$arg" in
    --headless)
      export ARMS_LAB_HEADLESS=1
      ;;
    --cpu)
      export ARMS_LAB_DEVICE=cpu
      ;;
    --reset-build)
      RESET_BUILD=1
      ;;
    --gpu)
      echo "GPU image/profile is intentionally not wired in the initial scaffold yet." >&2
      echo "Use the CPU baseline for now; add a pinned CUDA/PyTorch profile before enabling --gpu." >&2
      exit 2
      ;;
    -h|--help)
      cat <<'EOF'
Usage: ./run.sh [--headless] [--cpu] [--reset-build]

The default portable baseline is CPU + Docker Compose.
EOF
      exit 0
      ;;
    *)
      echo "Unknown option: $arg" >&2
      exit 2
      ;;
  esac
done

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required. Install Docker Engine/Desktop and retry." >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose v2 is required." >&2
  exit 1
fi

if [[ "$RESET_BUILD" == "1" ]]; then
  docker compose build --no-cache
fi

docker compose up --build --remove-orphans --abort-on-container-exit
