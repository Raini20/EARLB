#!/usr/bin/env bash
# Konvertiert die Exp14-Bag ins EuRoC-Format für OpenMAVIS und erzeugt timestamps.txt.
# Aufruf im Container:  bash scripts/prepare_data.sh [/data/exp14_basement_2.bag] [/data/euroc]
# Ergebnis: /data/euroc/exp14_basement_2/{mav0/cam0..cam4, mav0/imu0, timestamps.txt}
# Platz: die PNGs brauchen zusätzlich mehrere GB neben der Bag.
set -euo pipefail

BAG="${1:-/data/exp14_basement_2.bag}"
OUT="${2:-/data/euroc}"
SEQ="$OUT/$(basename "$BAG" .bag)"
TOOLS=/opt/euroc_dataset_tools/scripts/rosbag2euroc.py

set +u; source /opt/ros/noetic/setup.bash; set -u
[ -f "$BAG" ] || { echo "fehlt: $BAG"; exit 1; }
if [ -f "$SEQ/timestamps.txt" ]; then
    echo "schon konvertiert: $SEQ  (zum Neu-Konvertieren den Ordner löschen)"; exit 0
fi

# Der Konverter nummeriert cam<i>/imu<i> in der Reihenfolge von 'rosbag info'.
# Der OpenMAVIS-Runner erwartet cam1=links, cam0=rechts, cam4=seitlich links, cam3=seitlich rechts, imu0=Alphasense.
echo "== Topics prüfen"
rosbag info --yaml "$BAG" | python3 -c '
import sys, yaml
t = yaml.safe_load(sys.stdin)["topics"]
cams = [x["topic"] for x in t if x["type"] == "sensor_msgs/Image"]
imus = [x["topic"] for x in t if x["type"] == "sensor_msgs/Imu"]
for i, c in enumerate(cams): print(f"  cam{i} <- {c}")
for i, c in enumerate(imus): print(f"  imu{i} <- {c}")
if len(cams) != 5 or any(f"cam{i}" not in c for i, c in enumerate(cams)):
    sys.exit("Abbruch: erwartet 5 Bild-Topics in der Reihenfolge cam0..cam4 (sensor_msgs/Image, nicht komprimiert)")
if not imus or "alphasense" not in imus[0]:
    sys.exit("Abbruch: imu0 ist nicht die Alphasense-IMU")
'

echo "== Konvertieren (dauert, ~10-30 min)"
mkdir -p "$OUT"
python3 "$TOOLS" "$BAG" -o "$OUT"

# Der Runner lädt für jeden Zeitstempel <t>.png aus cam1, cam0, cam4, cam3.
# Nur Zeitstempel übernehmen, die in allen vier Ordnern vorhanden sind.
echo "== timestamps.txt"
M="$SEQ/mav0"
for c in cam0 cam1 cam3 cam4; do ls "$M/$c/data" | sed 's/\.png$//' | sort > "/tmp/ts_$c"; done
comm -12 /tmp/ts_cam0 /tmp/ts_cam1 | comm -12 - /tmp/ts_cam3 | comm -12 - /tmp/ts_cam4 | sort -n > "$SEQ/timestamps.txt"

N0=$(wc -l < /tmp/ts_cam0); N=$(wc -l < "$SEQ/timestamps.txt")
NIMU=$(grep -vc '^#' "$M/imu0/data.csv" || true)
echo "Bilder cam0: $N0, in allen 4 Kameras: $N, IMU-Zeilen: $NIMU"
[ "$N" -lt "$N0" ] && echo "Hinweis: $((N0-N)) Zeitstempel fehlen in einer Kamera und wurden weggelassen"
echo "Fertig: $SEQ"
