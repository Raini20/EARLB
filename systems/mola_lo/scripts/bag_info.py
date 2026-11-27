#!/usr/bin/env python3
"""Prueft Topics, Frames und LiDAR-Punktzeit im Hilti-ROS1-Bag (pip install rosbags)."""
import sys
import numpy as np
from rosbags.rosbag1 import Reader
from rosbags.typesys import Stores, get_typestore

bag = sys.argv[1] if len(sys.argv) > 1 else "exp14_basement_2.bag"
ts = get_typestore(Stores.ROS1_NOETIC)
with Reader(bag) as r:
    print(f"Dauer {(r.end_time - r.start_time) / 1e9:.1f} s, Start {r.start_time / 1e9:.3f}")
    for c in r.connections:
        print(f"  {c.topic:32s} {c.msgtype:28s} {c.msgcount}")
    cs = [c for c in r.connections if c.topic == "/hesai/pandar"]
    for c, _, raw in r.messages(connections=cs):
        m = ts.deserialize_ros1(raw, c.msgtype)
        off = {f.name: f.offset for f in m.fields}
        d = np.frombuffer(m.data, dtype=np.uint8).reshape(-1, m.point_step)
        t = d[:, off["timestamp"]:off["timestamp"] + 8].copy().view(np.float64).ravel()
        h = m.header.stamp.sec + m.header.stamp.nanosec * 1e-9
        print(f"LiDAR frame={m.header.frame_id} Felder={list(off)} Punkte={m.width}")
        print(f"Punktzeit relativ zum Header: {t.min() - h:.4f} .. {t.max() - h:.4f} s")
        break
