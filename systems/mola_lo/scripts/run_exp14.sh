#!/usr/bin/env bash
# MOLA-LO auf Hilti 2022 Exp14 ausfuehren (nativ oder im Container).
# Erzeugt nach Ausgabevertrag: results/exp14/<run>/traj_imu.tum, map.ply, run.md
# Aufruf: run_exp14.sh /data/exp14_basement_2.bag [run_1]
set -euo pipefail

BAG=${1:-/data/exp14_basement_2.bag}
RUN=${2:-run_1}
SYS_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
OUT="$SYS_DIR/results/exp14/$RUN"
GT=${GT:-$SYS_DIR/../../common/gt/exp14_gt.tum}
mkdir -p "$OUT"

[ -f "$BAG" ] || { echo "Bag nicht gefunden: $BAG" >&2; exit 1; }

# ROS-Umgebung: nativ muss /opt/ros/$ROS_DISTRO/setup.bash gesourct sein.
WRAPPER=$(command -v mola-lo-cli-hilti2022 || find /opt/ros -name mola-lo-cli-hilti2022 2>/dev/null | head -1)
[ -n "$WRAPPER" ] || { echo "mola-lo-cli-hilti2022 nicht gefunden. 'source /opt/ros/\$ROS_DISTRO/setup.bash'" \
                            "und ros-\$ROS_DISTRO-mola-lidar-odometry installieren." >&2; exit 1; }

# Preflight: die ICP-Pipeline laedt libmola_metric_maps.so erst zur Laufzeit per YAML.
# Fehlt sie, bricht MOLA-LO nicht ab, sondern verwirft stillschweigend jeden Scan
# ("Discarding incoming observations") und schreibt am Ende 0 Posen. Paket:
# ros-$ROS_DISTRO-mola-metric-maps (keine harte apt-Abhaengigkeit von mola-lidar-odometry).
if ! find /opt/ros -name libmola_metric_maps.so -print -quit 2>/dev/null | grep -q .; then
  echo "libmola_metric_maps.so nicht gefunden. Bitte installieren:" >&2
  echo "  sudo apt install -y ros-\${ROS_DISTRO:-jazzy}-mola-metric-maps" >&2
  exit 1
fi

# evo liegt bei nativer Installation ggf. in einem venv/conda-Env statt auf dem PATH.
if ! command -v evo_ape >/dev/null 2>&1; then
  for d in "$HOME/miniconda3/envs/evo/bin" "$HOME/.venvs/evo/bin" "$HOME/.local/bin"; do
    [ -x "$d/evo_ape" ] && { PATH="$d:$PATH"; export PATH; break; }
  done
fi

# Hilti-2022-Profil von MOLA-LO: IMU = base_link, feste LiDAR-Pose T_imu_pandar,
# IMU-Deskew, Pitch/Roll-Init aus IMU, Smoother als State Estimator.
# HILTI2022_BASE_FRAME=imu -> Trajektorie liegt direkt im GT-Frame "I".
export HILTI2022_BASE_FRAME=imu
# Haelt die finalisierte Keyframe-Trajektorie im Smoother vor, damit
# --output-tum-path-smoothed etwas schreiben kann (sonst leer).
export MOLA_SMOOTHER_KEEP_TRAJECTORY=true

# Drei Trajektorien aus demselben Lauf (kostet keine zusaetzliche Rechenzeit):
#   traj_imu.tum           --output-tum-path          reine LiDAR-Odometrie-Posen (Ausgabevertrag)
#   traj_imu_fused.tum     --output-tum-path-fused    Fusion des State Estimators je Scan
#   traj_imu_smoothed.tum  --output-tum-path-smoothed Keyframe-Posen nach Verlassen des Optimierungsfensters
# Alle drei im selben Frame (base_link = IMU). Die Wahl fuer das Paper wird in
# run.md begruendet; Default bleibt traj_imu.tum.
T0=$(date +%s)
"$WRAPPER" "$BAG" \
  --output-tum-path "$OUT/traj_imu.tum" \
  --output-tum-path-fused "$OUT/traj_imu_fused.tum" \
  --output-tum-path-smoothed "$OUT/traj_imu_smoothed.tum" \
  --output-simplemap "$OUT/map.simplemap" \
  2>&1 | tee "$OUT/mola.log"
T1=$(date +%s)

# mola-lidar-odometry-cli beendet sich mit Status 0, auch wenn es nach einem Fatal
# Error in der ICP-Pipeline alle weiteren Scans verworfen hat. Exit-Code allein
# reicht als Erfolgskriterium also nicht; Log und Posenzahl pruefen.
if grep -q "a fatal error ocurred" "$OUT/mola.log"; then
  echo "FEHLER: MOLA-LO hat Observations verworfen (Fatal Error in der Pipeline)." >&2
  grep -m1 -A3 "==== MRPT exception ====" "$OUT/mola.log" >&2 || true
  echo "Volles Log: $OUT/mola.log" >&2
  exit 1
fi
NPOSE_CHECK=$(grep -cvE '^\s*(#|$)' "$OUT/traj_imu.tum" 2>/dev/null || echo 0)
if [ "$NPOSE_CHECK" -lt 100 ]; then
  echo "FEHLER: nur $NPOSE_CHECK Posen in traj_imu.tum (erwartet ~740). Siehe $OUT/mola.log" >&2
  exit 1
fi

# Karte: simplemap -> metric map -> PLY (gleicher Weltframe wie traj_imu.tum)
#
# Voxelgroesse: 5 cm. Das YAML-Default von 2 cm liefert 2,21 M Punkte und eine
# 72-MB-PLY -- zu gross fuer die Repo-Historie (GitHub warnt ab 50 MB, blockt ab
# 100 MB, Rausnehmen danach nur per History-Rewrite). 5 cm gibt 0,99 M Punkte und
# 16 MB. Die Diskretisierung von 2,5 cm liegt klar unter dem Signal, das die Karte
# belegen soll (ATE ~10 cm, GT-Genauigkeit 1-2 cm). Fuer mehr Detail in
# CloudCompare: SM2MM_VOXEL_SIZE=0.03 -> 25 MB.
export SM2MM_VOXEL_SIZE=${SM2MM_VOXEL_SIZE:-0.05}
#
# sm2mm ist ein reines mp2p_icp-CLI und kennt die ${VAR|default}-Substitution
# nicht: die stammt aus mola_yaml und wird nur von MOLA-Apps angewandt. Unexpandiert
# scheitert sm2mm an Enum-Feldern ("Unknown name '${SM2MM_DESKEW_METHOD|...}'").
# Daher hier selbst rendern; das Rendering bleibt als Beleg neben den Ergebnissen.
RENDERED="$OUT/sm2mm_exp14.rendered.yaml"
python3 - "$SYS_DIR/config/sm2mm_exp14.yaml" > "$RENDERED" <<'PY'
import os, re, sys
def sub(m):
    name, sep, default = m.group(1).partition('|')
    if name in os.environ:
        return os.environ[name]
    if not sep:
        raise SystemExit(f"Variable {name} ist nicht gesetzt und hat keinen Default")
    return default
sys.stdout.write(re.sub(r'\$\{([^}]*)\}', sub, open(sys.argv[1]).read()))
PY

sm2mm -i "$OUT/map.simplemap" -o "$OUT/map.mm" -p "$RENDERED"
# Nur die Felder, die CloudCompare fuer die Cloud/Cloud-Distanz braucht. Die uebrigen
# Felder der Metric Map (t, view_x/y/z, ring) verdoppeln die Datei ohne Nutzen: 33 -> 16 MB.
mm2ply -i "$OUT/map.mm" -o "$OUT/map_full" -b --export-fields x,y,z,intensity
PLY=$(ls "$OUT"/map_full*.ply | head -1)
mv "$PLY" "$OUT/map.ply"

# Kennzahlen fuer run.md
NPOSE=$(grep -cvE '^\s*(#|$)' "$OUT/traj_imu.tum" || true)
DISTRO=${ROS_DISTRO:-jazzy}
VER=$(dpkg-query -W -f='${Version}' ros-$DISTRO-mola-lidar-odometry 2>/dev/null || echo unbekannt)
NSCAN=740; DUR=$((T1-T0))
NPTS=$(awk '/element vertex/{print $3; exit}' "$OUT/map.ply" 2>/dev/null || echo "?")
PLYMB=$(du -m "$OUT/map.ply" 2>/dev/null | cut -f1 || echo "?")

# run.md wird hier maschinell erzeugt. Die Auffaelligkeiten darin sind Handarbeit,
# deshalb eine vorhandene Datei nicht stillschweigend ueberschreiben, sondern wegsichern.
[ -f "$OUT/run.md" ] && cp "$OUT/run.md" "$OUT/run.md.bak.$(date +%Y%m%d-%H%M%S)"

cat > "$OUT/run.md" <<MD
# MOLA-LO – Exp14 – $RUN

- Datum: $(date -Iseconds)
- System: ros-$DISTRO-mola-lidar-odometry $VER (Binärpaket; nativ oder Docker-Image ../../../Dockerfile)
  Der Ausgabevertrag verlangt den Commit-Hash des Systems. MOLA-LO kommt hier aus dem
  offiziellen apt-Repo, nicht aus einem Git-Checkout; die Paketversion oben ist die
  entsprechende, eindeutige Kennung. Das Dockerfile installiert dieselbe Version.
- Aufruf: mola-lo-cli-hilti2022 (Profil hilti2022, HILTI2022_BASE_FRAME=imu)
- Pipeline: lidar3d-default.yaml, Deskew IMU, Init PitchAndRollFromIMU, State Estimator Smoother
- Extrinsik LiDAR im IMU-Frame: x=-0.001 y=-0.00855 z=0.055 [m], yaw=-90 pitch=0 roll=180 [deg]
- Input: $(basename "$BAG"), LiDAR /hesai/pandar ($NSCAN Scans, 10 Hz), IMU /alphasense/imu
- Laufzeit gesamt: ${DUR} s (≈ $(awk "BEGIN{printf \"%.1f\", $DUR*1000/$NSCAN}") ms/Scan, inkl. Bag-Lesen)
- Posen in traj_imu.tum: $NPOSE
- Trajektorien-Varianten aus demselben Lauf: traj_imu.tum (Ausgabevertrag, reine LiDAR-Odometrie),
  traj_imu_fused.tum (State-Estimator-Fusion), traj_imu_smoothed.tum (finalisierte Keyframes);
  ATE-Vergleich in variants_ate.txt
- Karte: sm2mm (config/sm2mm_exp14.yaml, gerendert als sm2mm_exp14.rendered.yaml) -> mm2ply,
  Datei map.ply ($NPTS Punkte, ${SM2MM_VOXEL_SIZE}-m-Voxel, Felder x,y,z,intensity, ${PLYMB} MB)
- t_offset für evo: siehe t_offset.txt im selben Ordner (legt dieses Skript mit -0.05 an, falls sie fehlt)
- Auffälligkeiten: (manuell ergänzen – ein erneuter Lauf sichert die alte run.md als run.md.bak.<Zeit>)
MD

# Auswertung gegen die GT, sobald common/ gemerged ist
if [ -f "$GT" ] && command -v evo_ape >/dev/null 2>&1; then
  export MPLBACKEND=${MPLBACKEND:-Agg}

  # Zeitversatz: MOLA-LO-Posen liegen auf einem 10-Hz-Raster, das gegen das der GT um
  # ~50 ms phasenverschoben ist -- genau auf der Zuordnungsschwelle --t_max_diff 0.05.
  # Ohne Versatz werden nur 439 von 689 GT-Posen zugeordnet, mit -0.05 s 680 (Begruendung
  # in run_1/run.md). Der Wert ist systematisch, also fuer jeden neuen Lauf gleich.
  [ -f "$OUT/t_offset.txt" ] || echo "-0.05" > "$OUT/t_offset.txt"

  # Ausgabevertrag: traj_imu.tum mit dem gemeinsamen Skript der Gruppe auswerten
  # (common/eval/evaluate.sh erwartet die Run-Nummer, also "1" statt "run_1").
  # T_OFFSET explizit uebergeben, damit es auch mit einer evaluate.sh-Version ohne
  # t_offset.txt-Unterstuetzung stimmt. traj_xy.pdf vorher weg: sonst fragt evo_traj
  # beim erneuten Lauf nach dem Ueberschreiben und bricht ohne Terminal ab.
  rm -f "$OUT/traj_xy.pdf"
  T_OFFSET=$(tr -d ' \r\n' < "$OUT/t_offset.txt") \
    bash "$SYS_DIR/../../common/eval/evaluate.sh" mola_lo "${RUN#run_}"

  # Vergleich der drei Trajektorien-Varianten -> Entscheidungsgrundlage fuer run.md
  : > "$OUT/variants_ate.txt"
  for v in traj_imu traj_imu_fused traj_imu_smoothed; do
    f="$OUT/$v.tum"
    if [ -s "$f" ]; then
      echo "=== $v ===" >> "$OUT/variants_ate.txt"
      evo_ape tum "$GT" "$f" -a --t_max_diff 0.05 --no_warnings >> "$OUT/variants_ate.txt" 2>&1 || true
    else
      echo "=== $v === (leer oder nicht geschrieben)" >> "$OUT/variants_ate.txt"
    fi
  done
  echo "Varianten-ATE: $OUT/variants_ate.txt"
else
  echo "Hinweis: GT ($GT) oder evo fehlt – evo-Auswertung übersprungen."
fi
echo "Fertig: $OUT"
