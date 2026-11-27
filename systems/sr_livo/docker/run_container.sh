#!/usr/bin/env bash
# Startet den SR-LIVO-Container in WSL2 mit GUI über WSLg.
# Aufruf (aus systems/sr_livo/):  ./docker/run_container.sh [DATA_DIR]
set -euo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"      # systems/sr_livo
REPO="$(cd "$HERE/../.." && pwd)"             # Repo-Wurzel (für common/)
DATA_DIR="${1:-${DATA_DIR:-$HOME/data/hilti2022}}"

docker run -it --rm \
    --name sr_livo \
    --net host \
    -e HOST_UID="$(id -u)" -e HOST_GID="$(id -g)" \
    -e SRLIVO_NO_VIO="${SRLIVO_NO_VIO:-0}" \
    -e DISPLAY="${DISPLAY:-:0}" \
    -e WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-}" \
    -e XDG_RUNTIME_DIR=/mnt/wslg/runtime-dir \
    -e PULSE_SERVER=/mnt/wslg/PulseServer \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v /mnt/wslg:/mnt/wslg \
    -v "$HERE":/work/sr_livo \
    -v "$REPO/common":/work/common:ro \
    -v "$DATA_DIR":/data \
    sr_livo bash
