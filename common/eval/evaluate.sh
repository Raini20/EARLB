#!/usr/bin/env bash
# evo-Auswertung eines Laufs nach Gruppenvorgabe (KPI-PDF): SE(3)-Umeyama, keine Skalierung, RPE über 1 m.
#
# Aufruf aus der Repo-Wurzel, im Auswerte-Image:
#   docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp -v "$PWD":/repo earlb-eval \
#       bash common/eval/evaluate.sh <system> <run_nr>
#   z. B.  bash common/eval/evaluate.sh kiss_slam 1   ->  systems/kiss_slam/results/exp14/run_1/
#
# Ergebnis im Run-Ordner: ape.zip, rpe_trans.zip, rpe_rot.zip (Ausgabevertrag) + ape.txt, rpe_*.txt, traj_xy.pdf
set -euo pipefail

SYS="${1:?System angeben: openmavis | mola_lo | kiss_slam | sr_livo}"
RUN="${2:?Run-Nummer angeben}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$ROOT/systems/$SYS/results/exp14/run_$RUN"
EST="$OUT/traj_imu.tum"
GT="${GT:-$ROOT/common/gt/exp14_gt.tum}"
TMAX="${T_MAX_DIFF:-0.05}"
[ -f "$EST" ] || { echo "fehlt: $EST"; exit 1; }
# Zeitversatz nur wenn nötig (z. B. KISS-SLAM: Bag-Zeit), Wert in run.md begründen.
# Vorrang: Umgebung T_OFFSET, sonst <run>/t_offset.txt (liest auch compare.py), sonst 0.
OFFSET="${T_OFFSET:-}"
[ -z "$OFFSET" ] && [ -f "$OUT/t_offset.txt" ] && OFFSET="$(tr -d ' \r\n' < "$OUT/t_offset.txt")"
OFFSET="${OFFSET:-0}"
echo "t_offset: $OFFSET s"
export MPLBACKEND="${MPLBACKEND:-Agg}"
# traj_xy.pdf mit löschen: sonst fragt evo_traj beim zweiten Lauf nach und bricht ohne Terminal ab (EOFError)
rm -f "$OUT"/ape.zip "$OUT"/rpe_trans.zip "$OUT"/rpe_rot.zip "$OUT"/traj_xy.pdf

COMMON=(-a --t_max_diff "$TMAX" --t_offset "$OFFSET")
evo_traj tum "$EST" --ref "$GT" "${COMMON[@]}" -v --plot_mode xy --save_plot "$OUT/traj_xy.pdf" | tee "$OUT/evo_traj.txt"
evo_ape  tum "$GT" "$EST" "${COMMON[@]}" --save_results "$OUT/ape.zip" | tee "$OUT/ape.txt"
evo_rpe  tum "$GT" "$EST" "${COMMON[@]}" --delta 1 --delta_unit m -r trans_part --save_results "$OUT/rpe_trans.zip" | tee "$OUT/rpe_trans.txt"
evo_rpe  tum "$GT" "$EST" "${COMMON[@]}" --delta 1 --delta_unit m -r angle_deg  --save_results "$OUT/rpe_rot.zip"   | tee "$OUT/rpe_rot.txt"

echo "Ergebnisse in $OUT"
