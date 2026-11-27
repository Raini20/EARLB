#!/usr/bin/env python3
"""Kartengenauigkeit: Cloud-to-Cloud-Abstand der SR-LIVO-Karte zum Hilti-Referenzscan.

Entspricht CloudCompare "Cloud/Cloud Distance" ohne lokales Modell: Für jeden Kartenpunkt der Abstand zum
nächsten Scanpunkt (exakter Nächster-Nachbar, KD-Baum). Die Karte wird nur mit T_gt_est.txt ausgerichtet
(dieselbe SE(3)-Umeyama-Transformation wie die Trajektorie in evo), **kein ICP**.

Aufruf (im c2c-Container, siehe README):
    python scripts/c2c_scan.py results/exp14/run_10 /data/laser_scans/sheldonian_full.e57

Ausgabe in <run>/c2c/: c2c.txt (Kennzahlen), c2c_hist.pdf/.png, map_c2c.ply (ausgerichtete Karte + Abstand,
nur lokal).
"""
import argparse
import os
import sys
import time

import numpy as np
import pye57
from plyfile import PlyData, PlyElement
from scipy.spatial import cKDTree

THRESH = (0.05, 0.10, 0.20)  # Anteile < 5 / 10 / 20 cm


def load_T(path):
    T = np.loadtxt(path, comments="#")
    assert T.shape == (4, 4), T.shape
    return T


def load_map(path, T):
    v = PlyData.read(path)["vertex"].data
    p = np.column_stack([v["x"], v["y"], v["z"]]).astype(np.float64)
    return p @ T[:3, :3].T + T[:3, 3], v


def load_scan(path, lo, hi):
    """Scan mit Header-Pose (pye57 transform=True) laden und auf die Box [lo, hi] zuschneiden."""
    e = pye57.E57(path)
    if e.scan_count != 1:
        sys.exit(f"erwartet 1 Scan, gefunden {e.scan_count}")
    n_all = e.get_header(0).point_count
    d = e.read_scan(0, ignore_missing_fields=True, colors=False, intensity=False, transform=True)
    xyz = np.column_stack([d["cartesianX"], d["cartesianY"], d["cartesianZ"]])
    del d
    m = np.all((xyz >= lo) & (xyz <= hi), axis=1)
    return xyz[m], n_all


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("scan")
    ap.add_argument("--margin", type=float, default=2.0,
                    help="Rand um die Kartenbox beim Zuschneiden des Scans [m]. Abstände bis zu diesem Wert sind exakt.")
    a = ap.parse_args()

    out = os.path.join(a.run_dir, "c2c")
    os.makedirs(out, exist_ok=True)
    t0 = time.time()

    T = load_T(os.path.join(a.run_dir, "T_gt_est.txt"))
    pm, vmap = load_map(os.path.join(a.run_dir, "map.ply"), T)
    lo, hi = pm.min(0) - a.margin, pm.max(0) + a.margin
    print(f"Karte: {len(pm)} Punkte, Box {np.round(lo, 1)} .. {np.round(hi, 1)}", flush=True)

    ps, n_all = load_scan(a.scan, lo, hi)
    print(f"Scan: {n_all} Punkte gesamt, {len(ps)} in der Box ({time.time() - t0:.0f} s)", flush=True)

    tree = cKDTree(ps, leafsize=32, balanced_tree=False, compact_nodes=False)
    d, _ = tree.query(pm, k=1, distance_upper_bound=a.margin, workers=-1)
    n_far = int(np.isinf(d).sum())
    d[np.isinf(d)] = a.margin  # > margin: nur als untere Schranke zählbar
    print(f"KD-Baum + Abfrage fertig ({time.time() - t0:.0f} s)", flush=True)

    lines = [
        "# C2C SR-LIVO-Karte -> Hilti-Referenzscan (Nächster Nachbar, ohne lokales Modell, ohne ICP)",
        f"karte          {os.path.join(a.run_dir, 'map.ply')}  ({len(pm)} Punkte, Voxel 5 cm)",
        f"ausrichtung    T_gt_est.txt (SE(3)-Umeyama wie evo, ohne Skalierung)",
        f"scan           {os.path.basename(a.scan)}  ({n_all} Punkte, volle Auflösung, Header-Pose angewendet)",
        f"scan_in_box    {len(ps)}  (Kartenbox + {a.margin} m)",
        f"mean_m         {d.mean():.4f}",
        f"median_m       {np.median(d):.4f}",
        f"rms_m          {np.sqrt((d ** 2).mean()):.4f}",
        f"std_m          {d.std():.4f}",
        f"p90_m          {np.percentile(d, 90):.4f}",
        f"p95_m          {np.percentile(d, 95):.4f}",
        f"max_m          {d.max():.4f}" + ("  (gekappt)" if n_far else ""),
    ]
    for t in THRESH:
        lines.append(f"anteil_<{int(t * 100)}cm    {100 * (d < t).mean():.1f} %")
    lines.append(f"ueber_{a.margin:g}m      {n_far}")
    txt = "\n".join(lines)
    print(txt)
    with open(os.path.join(out, "c2c.txt"), "w") as f:
        f.write(txt + "\n")

    # ausgerichtete Karte mit Abstand als Skalarfeld (für die Ansicht in CloudCompare, nur lokal)
    v = np.empty(len(pm), dtype=[("x", "f4"), ("y", "f4"), ("z", "f4"),
                                 ("red", "u1"), ("green", "u1"), ("blue", "u1"), ("c2c", "f4")])
    v["x"], v["y"], v["z"] = pm.T.astype(np.float32)
    for c in ("red", "green", "blue"):
        v[c] = vmap[c]
    v["c2c"] = d.astype(np.float32)
    PlyData([PlyElement.describe(v, "vertex")]).write(os.path.join(out, "map_c2c.ply"))

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(3.5, 2.3))
    ax.hist(np.minimum(d, 0.3) * 100, bins=60, range=(0, 30), color="0.4")
    for t, ls in zip(THRESH[:2], ("--", ":")):
        ax.axvline(t * 100, color="k", ls=ls, lw=0.8, label=f"{int(t * 100)} cm: {100 * (d < t).mean():.0f} %")
    ax.axvline(np.median(d) * 100, color="k", lw=0.8, label=f"Median {np.median(d) * 100:.1f} cm")
    ax.set_xlabel("C2C Karte → Scan [cm] (letzter Balken ≥ 30)")
    ax.set_ylabel("Punkte")
    ax.legend(fontsize=7, frameon=False)
    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(out, f"c2c_hist.{ext}"), dpi=300, bbox_inches="tight")
    # Diagnose-Draufsicht: Karte nach C2C eingefärbt über dem Scan (grau), getrennt Keller / oben
    est = np.loadtxt(os.path.join(a.run_dir, "traj_imu.tum"))
    tr = est[:, 1:4] @ T[:3, :3].T + T[:3, 3]
    sub = ps[np.random.default_rng(0).choice(len(ps), min(3_000_000, len(ps)), replace=False)]
    fig, axs = plt.subplots(1, 2, figsize=(14, 5.5))
    for ax, (zlo, zhi, name) in zip(axs, [(-6, -1.5, "Keller (z < -1,5 m)"), (-1.5, 5, "oben (z ≥ -1,5 m)")]):
        ms = (sub[:, 2] >= zlo) & (sub[:, 2] < zhi)
        mp = (pm[:, 2] >= zlo) & (pm[:, 2] < zhi)
        ax.scatter(sub[ms, 0], sub[ms, 1], s=0.02, c="0.8", rasterized=True)
        o = np.argsort(d[mp])
        sc = ax.scatter(pm[mp][o, 0], pm[mp][o, 1], s=0.3, c=np.minimum(d[mp][o], 0.5),
                        cmap="turbo", vmin=0, vmax=0.5, rasterized=True)
        ax.plot(tr[:, 0], tr[:, 1], "k-", lw=1)
        ax.set_aspect("equal")
        ax.set_title(name)
        ax.set_xlabel("x [m]")
    axs[0].set_ylabel("y [m]")
    fig.colorbar(sc, ax=axs, label="C2C [m] (gekappt bei 0,5)", shrink=0.8)
    fig.savefig(os.path.join(out, "c2c_topview.png"), dpi=150, bbox_inches="tight")
    print(f"fertig ({time.time() - t0:.0f} s), Ergebnisse in {out}")


if __name__ == "__main__":
    main()
