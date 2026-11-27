#!/usr/bin/env python3
"""SR-LIVO-Karte (map.pcd) -> ausgedünnte map.ply für den Gruppenvergleich.

- map.ply liegt im SELBEN Weltframe wie traj_imu.tum (Ausgabevertrag der Gruppe).
- Für CloudCompare: dieselbe Ausrichtung wie die Trajektorie anwenden -> T_gt_est.txt (von plot_traj.py)
  per "Edit > Apply transformation" laden. Kein ICP als Hauptwert.
- Mit --aligned wird zusätzlich map_gt_aligned.ply (bereits transformiert) geschrieben (nur lokal).

Aufruf (im Container, aus /work/sr_livo):
  python3 scripts/export_map.py results/exp14/run_10 [--voxel 0.05] [--aligned]
"""
import argparse
import os

import numpy as np


def read_pcd(path):
    with open(path, "rb") as f:
        hdr = {}
        while True:
            line = f.readline().decode("ascii").strip()
            if not line or line.startswith("#"):
                continue
            k, *v = line.split()
            hdr[k] = v
            if k == "DATA":
                break
        if hdr["DATA"][0] != "binary":
            raise SystemExit(f"Nur binäre PCD unterstützt, gefunden: {hdr['DATA'][0]}")
        n = int(hdr["POINTS"][0])
        kind = {"F": "f", "U": "u", "I": "i"}
        dt = np.dtype([(name, f"<{kind[t]}{s}") for name, s, t in zip(hdr["FIELDS"], hdr["SIZE"], hdr["TYPE"])])
        return np.frombuffer(f.read(n * dt.itemsize), dtype=dt, count=n)


def voxel_mean(xyz, rgb, voxel):
    keys = np.floor(xyz / voxel).astype(np.int64)
    _, inv, cnt = np.unique(keys, axis=0, return_inverse=True, return_counts=True)
    inv = inv.ravel()
    out_xyz = np.zeros((len(cnt), 3))
    out_rgb = np.zeros((len(cnt), 3))
    np.add.at(out_xyz, inv, xyz)
    np.add.at(out_rgb, inv, rgb)
    return out_xyz / cnt[:, None], np.clip(np.round(out_rgb / cnt[:, None]), 0, 255).astype(np.uint8)


def write_ply(path, xyz, rgb):
    n = len(xyz)
    v = np.empty(n, dtype=[("x", "<f4"), ("y", "<f4"), ("z", "<f4"), ("red", "u1"), ("green", "u1"), ("blue", "u1")])
    v["x"], v["y"], v["z"] = xyz[:, 0], xyz[:, 1], xyz[:, 2]
    v["red"], v["green"], v["blue"] = rgb[:, 0], rgb[:, 1], rgb[:, 2]
    header = (f"ply\nformat binary_little_endian 1.0\ncomment SR-LIVO Exp14, Frame wie traj_imu.tum\n"
              f"element vertex {n}\nproperty float x\nproperty float y\nproperty float z\n"
              "property uchar red\nproperty uchar green\nproperty uchar blue\nend_header\n")
    with open(path, "wb") as f:
        f.write(header.encode("ascii"))
        f.write(v.tobytes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--voxel", type=float, default=0.05)
    ap.add_argument("--aligned", action="store_true")
    a = ap.parse_args()

    pc = read_pcd(os.path.join(a.run, "map.pcd"))
    xyz = np.stack([pc["x"], pc["y"], pc["z"]], 1).astype(np.float64)
    ok = np.isfinite(xyz).all(1)
    packed = pc["rgb"].astype(np.uint32)
    rgb = np.stack([(packed >> 16) & 255, (packed >> 8) & 255, packed & 255], 1).astype(np.float64)
    xyz, rgb = xyz[ok], rgb[ok]
    print(f"map.pcd: {len(pc)} Punkte ({(~ok).sum()} ungültig)")

    vx, vc = voxel_mean(xyz, rgb, a.voxel)
    out = os.path.join(a.run, "map.ply")
    write_ply(out, vx, vc)
    ext = vx.max(0) - vx.min(0)
    print(f"map.ply: {len(vx)} Punkte (Voxel {a.voxel} m), Ausdehnung {ext.round(1)} m, "
          f"{os.path.getsize(out) / 1e6:.1f} MB")

    if a.aligned:
        T = np.loadtxt(os.path.join(a.run, "T_gt_est.txt"))
        write_ply(os.path.join(a.run, "map_gt_aligned.ply"), vx @ T[:3, :3].T + T[:3, 3], vc)
        print("map_gt_aligned.ply geschrieben (mit T_gt_est.txt transformiert, nur lokal)")


if __name__ == "__main__":
    main()
