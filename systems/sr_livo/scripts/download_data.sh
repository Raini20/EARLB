#!/usr/bin/env bash
# Lädt Exp14-Bag, Ground Truth und Kalibrierung der Hilti SLAM Challenge 2022 (Hugging Face).
# Aufruf:  ./scripts/download_data.sh [--scan] [DATA_DIR]   (Standard: ~/data/hilti2022, NICHT unter /mnt/c)
#   --scan  zusätzlich den Referenz-Laserscan des Sheldonian Theatre (5.4 GB, E57) für den Kartenvergleich
set -euo pipefail

SCAN=0
if [ "${1:-}" = "--scan" ]; then SCAN=1; shift; fi
DATA_DIR="${1:-${DATA_DIR:-$HOME/data/hilti2022}}"
BASE="https://huggingface.co/datasets/Hilti-Research/hilti-slam-challenge-2022/resolve/main"

mkdir -p "$DATA_DIR/calibration" "$DATA_DIR/laser_scans"
cd "$DATA_DIR"

fetch() {  # fetch <remote-pfad> <ziel>   – setzt abgebrochene Downloads (.part) automatisch fort
    if [ -f "$2" ]; then echo "vorhanden: $2"; return; fi
    echo "lade: $1"
    local try=1
    # HTTP/1.1: bei Hugging Face brechen große Downloads häufig ab (curl 56/92) -> in Schleife fortsetzen
    until curl -L --fail --http1.1 -C - -o "$2.part" "$BASE/$1"; do
        if [ "$try" -ge 300 ]; then echo "Abbruch nach $try Versuchen: $1"; exit 1; fi
        try=$((try + 1))
        echo "Download unterbrochen, setze fort (Versuch $try)..."
        sleep 5
    done
    mv "$2.part" "$2"
}

check() {  # check <sha256> <datei>
    echo "prüfe SHA256 von $2 ..."
    if echo "$1  $2" | sha256sum -c -; then
        echo "OK: $2"
    else
        echo "FEHLER: Prüfsumme stimmt nicht – $2 löschen und neu laden"; exit 1
    fi
}

# SHA256 laut Hugging Face (LFS-oid), um fortgesetzte Downloads zu prüfen
BAG_SHA256="18eea013076b8263ababf4f36eb68d331564a0a493262b006dc0dddc2aa85b82"
SCAN_SHA256="46575d3eaf3169a24e24ba0013cc48610125ac842d6745e5e8156c6aecc59756"

fetch ground_truth/exp14_basement_2_imu.txt                          exp14_basement_2_imu.txt
fetch calibration/calibration_files/lidar_calibration.yaml           calibration/lidar_calibration.yaml
fetch calibration/calibration_files/calib_3_cam0-1-camchain-imucam.yaml calibration/calib_3_cam0-1-camchain-imucam.yaml
fetch rosbags/exp14_basement_2.bag                                   exp14_basement_2.bag   # ~6 GB
check "$BAG_SHA256" exp14_basement_2.bag

if [ $SCAN -eq 1 ]; then
    # Exp14 wurde im Sheldonian Theatre (Oxford) aufgenommen, nicht auf der Baustelle
    fetch laser_scans/sheldonian_full.e57 laser_scans/sheldonian_full.e57   # ~5.4 GB
    check "$SCAN_SHA256" laser_scans/sheldonian_full.e57
fi

echo "Fertig: $DATA_DIR"
ls -lh "$DATA_DIR" "$DATA_DIR/laser_scans"
