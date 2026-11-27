#!/usr/bin/env bash
# Ein OpenMAVIS-Lauf nach Ausgabevertrag -> results/exp14/run_<n>/
# Aufruf im Container:  bash scripts/run.sh <n> [config.yaml]
#   OPENMAVIS_VIEWER=0 bash scripts/run.sh 2    # ohne Pangolin-Fenster
#   SEQ=/data/euroc/exp14_basement_2            # Standard, siehe prepare_data.sh
# OpenMAVIS ist nicht deterministisch: 3-5 Läufe, Nummern in results/exp14/REFERENCE.
set -uo pipefail

N="${1:?Run-Nummer angeben, z. B. 1}"
HERE="$(cd "$(dirname "$0")/.." && pwd)"
CFG="$(realpath "${2:-$HERE/config/hilti_exp14.yaml}")"
SEQ="${SEQ:-/data/euroc/exp14_basement_2}"
OUT="$HERE/results/exp14/run_$N"
BIN=/opt/OpenMAVIS/Examples/Multi-Inertial/multi_inertial_euroc

[ -f "$SEQ/timestamps.txt" ] || { echo "fehlt: $SEQ/timestamps.txt -> erst scripts/prepare_data.sh"; exit 1; }
[ -e "$OUT/traj_imu.tum" ] && { echo "run_$N existiert schon, andere Nummer wählen"; exit 1; }
mkdir -p "$OUT"
cp "$CFG" "$OUT/config_used.yaml"
cd "$OUT"

echo "== OpenMAVIS run_$N  (Config: $CFG)"
START=$(date +%s)
"$BIN" /opt/OpenMAVIS/Vocabulary/ORBvoc.txt "$OUT/config_used.yaml" "$SEQ" "$SEQ/timestamps.txt" raw 2>&1 | tee run.log
RC=${PIPESTATUS[0]}
DUR=$(( $(date +%s) - START ))

if [ ! -s f_raw.txt ]; then
    echo "FEHLER: keine Trajektorie (f_raw.txt) erzeugt, Exit-Code $RC, siehe run.log"; exit 1
fi
python3 "$HERE/scripts/to_tum.py" f_raw.txt traj_imu.tum | tee to_tum.log

# run.md vorbefüllen (Ergebnisse und Auffälligkeiten danach von Hand ergänzen)
MAPS=$(grep -o 'There are [0-9]* maps' run.log | tail -1 | grep -o '[0-9]*' || echo "?")
if diff -q "$HERE/config/hilti_exp14.yaml" config_used.yaml >/dev/null; then CFGNOTE="unverändert (config/hilti_exp14.yaml)"
else CFGNOTE="geändert, siehe Diff unten"; fi
cat > run.md <<MD
# OpenMAVIS – Exp14 – Run $N

- Datum: $(date +%F)
- OpenMAVIS Commit: \`$(cat /opt/OpenMAVIS/COMMIT 2>/dev/null || echo ?)\` + Patch 0001 (Viewer optional)
- Repo-Commit: \`$(git -C "$HERE" rev-parse --short HEAD 2>/dev/null || echo ?)\`
- Config: \`config_used.yaml\`, $CFGNOTE
- Viewer: $([ "${OPENMAVIS_VIEWER:-1}" = "0" ] && echo aus || echo an)
- Rechner: $(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2 | xargs), $(nproc) Threads, $(free -g | awk '/Mem:/{print $2}') GB RAM im Container
- Laufzeit: ${DUR} s Wanduhr, Exit-Code $RC
- Trajektorie: $(tail -1 to_tum.log)
- Karten im Atlas: $MAPS (gespeichert wird nur die größte Karte -> bei >1 Abdeckung prüfen)
- Frame: \`traj_imu.tum\` = IMU-Pose direkt aus OpenMAVIS (SaveTrajectoryEuRoC, IMU_MULTI), Zeit in s, keine Umrechnung

## Ergebnisse (evo, SE(3)-Umeyama, ohne Skalierung)

Nach \`common/eval/evaluate.sh openmavis $N\` aus ape.txt / rpe_*.txt eintragen.

| Metrik | RMSE | Mean | Median | Max |
| --- | --- | --- | --- | --- |
| APE trans [m] | | | | |
| RPE trans, 1 m [m] | | | | |
| RPE rot, 1 m [deg] | | | | |

## Auffälligkeiten

- 
MD
if [ "$CFGNOTE" != "unverändert (config/hilti_exp14.yaml)" ]; then
    { echo; echo '## Config-Diff zu config/hilti_exp14.yaml'; echo; echo '```diff'
      diff "$HERE/config/hilti_exp14.yaml" config_used.yaml; echo '```'; } >> run.md
fi

echo
echo "Fertig: $OUT"
echo "Auswerten (PowerShell, Repo-Wurzel):  .\\systems\\openmavis\\scripts\\eval.ps1 $N"
