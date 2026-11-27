#!/usr/bin/env bash
# evo-Auswertung nach Gruppenvorgabe (SE(3)-Umeyama, keine Skalierung, RPE über 1 m).
# Aufruf:  ./scripts/evaluate.sh <run_nr> [GT]
# GT-Standard: common/gt/exp14_gt.tum (von main); sonst Hilti-GT-Datei aus /data.
set -euo pipefail

RUN="${1:?Run-Nummer angeben}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
OUT="$HERE/results/exp14/run_$RUN"
EST="$OUT/traj_imu.tum"

if [ -n "${2:-}" ]; then GT="$2"
elif [ -f /work/common/gt/exp14_gt.tum ]; then GT=/work/common/gt/exp14_gt.tum
elif [ -f "$HERE/../../common/gt/exp14_gt.tum" ]; then GT="$HERE/../../common/gt/exp14_gt.tum"
else GT=/data/exp14_basement_2_imu.txt; echo "WARNUNG: nutze Hilti-GT direkt ($GT)"; fi

export MPLBACKEND="${MPLBACKEND:-Agg}"
rm -f "$OUT"/ape.zip "$OUT"/rpe_trans.zip "$OUT"/rpe_rot.zip

evo_traj tum "$EST" --ref "$GT" -a --t_max_diff 0.05 -v --plot_mode xy --save_plot "$OUT/traj_xy.pdf"
evo_ape  tum "$GT" "$EST" -a --t_max_diff 0.05 --save_results "$OUT/ape.zip"       | tee "$OUT/ape.txt"
evo_rpe  tum "$GT" "$EST" -a --t_max_diff 0.05 --delta 1 --delta_unit m -r trans_part --save_results "$OUT/rpe_trans.zip" | tee "$OUT/rpe_trans.txt"
evo_rpe  tum "$GT" "$EST" -a --t_max_diff 0.05 --delta 1 --delta_unit m -r angle_deg  --save_results "$OUT/rpe_rot.zip"   | tee "$OUT/rpe_rot.txt"

echo "Ergebnisse in $OUT"
