#!/usr/bin/env bash
# Host-Wrapper (Linux/WSL/Git-Bash): Image bauen und Exp14 laufen lassen.
# Aufruf: ./run_docker.sh /pfad/zu/exp14_basement_2.bag [run_1]
set -euo pipefail
BAG=$(realpath "$1"); RUN=${2:-run_1}
REPO=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
docker build -t earlb/mola_lo "$REPO/systems/mola_lo"

# -it nur anhaengen, wenn wirklich ein Terminal dranhaengt: ohne TTY bricht
# "docker run -it" mit "the input device is not a TTY" ab (Pipe, Hintergrundlauf, CI).
TTY_ARGS=()
[ -t 0 ] && [ -t 1 ] && TTY_ARGS=(-it)

# Als aufrufender Benutzer laufen, sonst gehoeren die Ergebnisse in results/ dem
# root des Hosts. Dieser Benutzer hat im Image kein Home, evo will aber eins
# (~/.evo/settings.json) -- daher HOME auf ein beschreibbares Verzeichnis.
docker run --rm "${TTY_ARGS[@]}" \
  -u "$(id -u):$(id -g)" \
  -e HOME=/tmp \
  -v "$REPO":/ws \
  -v "$(dirname "$BAG")":/data:ro \
  earlb/mola_lo bash /ws/systems/mola_lo/scripts/run_exp14.sh "/data/$(basename "$BAG")" "$RUN"
