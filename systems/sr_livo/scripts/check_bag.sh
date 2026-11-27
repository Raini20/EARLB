#!/usr/bin/env bash
# Prüft Topics und PointCloud2-Felder des Bags, bevor die Config final ist (im Container ausführen).
# Aufruf:  ./scripts/check_bag.sh [BAG] [LIDAR_TOPIC]
set -eo pipefail
source /opt/ros/noetic/setup.bash

BAG="${1:-/data/exp14_basement_2.bag}"
LIDAR_TOPIC="${2:-/hesai/pandar}"

echo "=== rosbag info ==="
rosbag info "$BAG"

echo "=== PointCloud2-Felder von $LIDAR_TOPIC (1 Nachricht) ==="
python3 - "$BAG" "$LIDAR_TOPIC" <<'EOF'
import sys, rosbag
from sensor_msgs import point_cloud2 as pc2
bag, topic = sys.argv[1], sys.argv[2]
types = {1:'int8',2:'uint8',3:'int16',4:'uint16',5:'int32',6:'uint32',7:'float32',8:'float64'}
with rosbag.Bag(bag) as b:
    for _, msg, _ in b.read_messages(topics=[topic]):
        print("header.stamp:", msg.header.stamp.to_sec(), " frame_id:", msg.header.frame_id)
        print("Punkte:", msg.width * msg.height)
        for f in msg.fields:
            print(f"  {f.name:12s} {types.get(f.datatype, f.datatype)}")
        names = [f.name for f in msg.fields]
        tf = next((n for n in ("timestamp", "time", "t") if n in names), None)
        if tf:
            ts = [p[0] for p in pc2.read_points(msg, field_names=[tf], skip_nans=True)]
            print(f"{tf}: erster={ts[0]:.6f} min={min(ts):.6f} max={max(ts):.6f} span={max(ts)-min(ts):.6f}")
            print("erster Punkt == min?", ts[0] == min(ts))
        break
EOF
