#!/usr/bin/env bash
# Ein kompletter SR-LIVO-Lauf auf Exp14 (im Container ausführen, aus /work/sr_livo).
# Aufruf:  ./scripts/run_exp14.sh <run_nr> [RATE=0.5] [RVIZ=true|false]
#          Referenz- und Vergleichsläufe mit Rate 0.5, Rate 1.0 nur als Echtzeittest.
# Ergebnis: results/exp14/run_<n>/{traj_imu.tum, map.pcd, run.md, launch.log, progress.log}
#
# Watchdog: Kommen HANG_TIMEOUT s lang keine neuen Posen, gilt der Versuch als hängend (sporadischer Hänger
# in SR-LIVO, siehe Run 7). Er wird abgebrochen, protokolliert und bis zu MAX_ATTEMPTS-mal neu gestartet.
set -eo pipefail
source /opt/ros/noetic/setup.bash
source /catkin_ws/devel/setup.bash

RUN="${1:?Run-Nummer angeben, z. B. 1}"
RATE="${2:-0.5}"
RVIZ="${3:-true}"
BAG="${BAG:-/data/exp14_basement_2.bag}"
HANG_TIMEOUT="${HANG_TIMEOUT:-60}"
MAX_ATTEMPTS="${MAX_ATTEMPTS:-3}"
T0_BAG=1649764528.07   # Startzeit des Exp14-Bags

HERE="$(cd "$(dirname "$0")/.." && pwd)"
OUT_TMP="$HERE/output"
RES="$HERE/results/exp14/run_$RUN"

if [ -e "$RES" ]; then echo "$RES existiert schon – andere Run-Nummer wählen."; exit 1; fi
mkdir -p "$RES"

log() { echo "[run_exp14] $*" | tee -a "$RES/progress.log"; }
pose_size() { stat -c %s "$OUT_TMP/pose.txt" 2>/dev/null || echo 0; }
pose_info() {
    local n=0 l="–"
    if [ -f "$OUT_TMP/pose.txt" ]; then
        n=$(wc -l < "$OUT_TMP/pose.txt")
        l=$(tail -1 "$OUT_TMP/pose.txt" | awk -v t0=$T0_BAG '{printf "%.1f", $1 - t0}')
    fi
    local p; p=$(pgrep -f "sr_livo/livo_node" | head -1)
    echo "posen=$n bag_t=${l}s cpu/rss=[$(ps -o %cpu=,rss= -p "$p" 2>/dev/null | xargs)]"
}

# Ein Versuch: 0 = fertig, 1 = Hänger
attempt() {
    local k=$1
    # pose.txt wird von SR-LIVO angehängt -> Ausgabeordner immer leeren
    rm -rf "$OUT_TMP" && mkdir -p "$OUT_TMP/cloud_frame"
    roslaunch "$HERE/launch/livo_hilti.launch" rviz:="$RVIZ" output_path:="$OUT_TMP" > "$RES/launch.log" 2>&1 &
    LAUNCH_PID=$!
    sleep 5
    rosbag play "$BAG" --clock -d 1.0 -r "$RATE" -q < /dev/null > /dev/null 2>&1 &
    local bag_pid=$! t=0 last=-1 still=0 tick=0 bag_done_at=""
    while true; do
        sleep 2; t=$((t + 2)); tick=$((tick + 2))
        local cur; cur=$(pose_size)
        if [ "$cur" = "$last" ]; then still=$((still + 2)); else still=0; last=$cur; fi
        [ $tick -ge 10 ] && { log "V$k $(( $(date +%s) - START ))s $(pose_info)"; tick=0; }
        if [ -z "$bag_done_at" ] && ! kill -0 $bag_pid 2>/dev/null; then bag_done_at=$t; log "V$k Bag fertig abgespielt"; fi
        # Fertig: Bag durch und pose.txt 10 s stabil (SR-LIVO kann hinter Echtzeit liegen)
        if [ -n "$bag_done_at" ] && [ $still -ge 10 ]; then return 0; fi
        # Hänger: keine neuen Posen (vor der ersten Pose großzügiger wegen Initialisierung)
        local limit=$HANG_TIMEOUT; [ "$cur" = "0" ] && limit=$((HANG_TIMEOUT + 60))
        if [ $still -ge $limit ] && [ -z "$bag_done_at" ]; then
            log "V$k HÄNGER: ${still}s keine neuen Posen ($(pose_info)) – breche ab"
            kill $bag_pid 2>/dev/null || true
            return 1
        fi
        [ $t -ge 1800 ] && { log "V$k Zeitlimit 30 min erreicht"; return 1; }
    done
}

START=$(date +%s)
: > "$RES/progress.log"
ok=0
for k in $(seq 1 "$MAX_ATTEMPTS"); do
    log "Versuch $k/$MAX_ATTEMPTS (Rate $RATE)"
    if attempt "$k"; then ok=1; break; fi
    kill -INT "$LAUNCH_PID" 2>/dev/null || true; wait "$LAUNCH_PID" 2>/dev/null || true
    cp "$RES/launch.log" "$RES/launch_haenger_v$k.log"
done

# Ctrl+C an roslaunch -> SR-LIVO schreibt rgb_map.pcd
kill -INT "$LAUNCH_PID" 2>/dev/null || true
wait "$LAUNCH_PID" 2>/dev/null || true
END=$(date +%s)

cp "$OUT_TMP/pose.txt" "$RES/traj_imu.tum"
[ -f "$OUT_TMP/rgb_map.pcd" ] && cp "$OUT_TMP/rgb_map.pcd" "$RES/map.pcd"

SR_COMMIT=$(git -C /catkin_ws/src/sr_livo rev-parse HEAD)
if [ "${SRLIVO_NO_VIO:-0}" = "1" ]; then VIO="aus (SRLIVO_NO_VIO=1, nur LIO)"; else VIO="an (Standard)"; fi
sed -e "s/{{RUN}}/$RUN/" -e "s/{{COMMIT}}/$SR_COMMIT/" -e "s/{{RATE}}/$RATE/" \
    -e "s/{{DURATION}}/$((END-START)) s/" -e "s/{{DATE}}/$(date -I)/" -e "s/{{VIO}}/$VIO/" \
    "$HERE/results/run_template.md" > "$RES/run.md"
cp "$HERE/config/hilti_exp14.yaml" "$RES/config_used.yaml"
cp "$HERE/launch/livo_hilti.launch" "$RES/launch_used.launch"
HANGS=$(grep -c "HÄNGER" "$RES/progress.log" || true)
[ "$HANGS" -gt 0 ] && echo "- Watchdog: $HANGS Hänger, automatisch neu gestartet (siehe progress.log, launch_haenger_v*.log)" >> "$RES/run.md"

# Abdeckung prüfen: Trajektorie muss bis kurz vor Bag-Ende reichen (Exp14 endet bei 74.0 s)
LAST=$(tail -1 "$RES/traj_imu.tum" | awk -v t0=$T0_BAG '{printf "%.1f", $1 - t0}')
if [ $ok -ne 1 ] || awk -v l="$LAST" 'BEGIN{exit !(l < 73.0)}'; then
    log "WARNUNG: Trajektorie endet bei ${LAST} s statt ~73.8 s – Lauf unvollständig, nicht auswerten!"
    echo "- **WARNUNG: unvollständig, letzte Pose bei ${LAST} s – nicht auswerten**" >> "$RES/run.md"
else
    log "FERTIG: $(wc -l < "$RES/traj_imu.tum") Posen, letzte bei ${LAST} s, Abdeckung OK"
fi

# Dateien gehören sonst root (Container) -> dem WSL-Benutzer zurückgeben
chown -R "${HOST_UID:-1000}:${HOST_GID:-1000}" "$RES" "$OUT_TMP"
echo "Weiter: ./scripts/evaluate.sh $RUN"
