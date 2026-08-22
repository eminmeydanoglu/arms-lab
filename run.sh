#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-}"
case "$MODE" in
  "") ;;
  --headless) export ARMS_LAB_HEADLESS=1 ;;
  --cpu) export ARMS_LAB_DEVICE=cpu ;;
  --gpu) export ARMS_LAB_DEVICE=cuda ;;
  --reset-build) docker compose build --no-cache ;;
  *) echo "Unknown option: $MODE" >&2; exit 2 ;;
esac

docker compose up --build --remove-orphans
