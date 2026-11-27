#!/usr/bin/env python3
"""Kartengenauigkeit: Cloud-to-Cloud-Abstand einer SLAM-Karte (map.ply) zum Hilti-Referenzscan.

Entspricht CloudCompare "Cloud/Cloud Distance" ohne lokales Modell: Für jeden Kartenpunkt der Abstand zum
nächsten Scanpunkt (exakter Nächster-Nachbar, KD-Baum). Die Karte wird nur mit T_gt_est.txt ausgerichtet
(dieselbe SE(3)-Umeyama-Transformation wie die Trajektorie in evo, berechnet aus traj_imu.tum und der GT), **kein ICP**.
Gibt es im Run-Ordner T_gt_est.txt nicht, wird sie hier berechnet und gespeichert.

Voraussetzung: map.ply liegt im selben Weltframe wie traj_imu.tum (Ausgabevertrag).

Speicher: Der Scan wird blockweise gelesen (--chunk Punkte je Block). Pro Block wird ein KD-Baum über die Scanpunkte
in der Kartenbox gebaut, und für jeden Kartenpunkt wird der kleinste Abstand über alle Blöcke mitgeführt. Das ist
derselbe exakte nächste Nachbar wie mit einem Baum über den ganzen Scan, braucht aber nur rund 1 GB RAM
(Standard 5 Mio. Punkte je Block) statt ~26 GB. Läuft damit auch auf den Laptops.

Aufruf aus der Repo-Wurzel im Auswerte-Image (siehe common/README.md):
    python common/eval/c2c_scan.py systems/<system>/results/exp14/run_<n> /data/laser_scans/sheldonian_full.e57

Ausgabe in <run>/c2c/: c2c.txt (Kennzahlen), c2c_hist.pdf/.png, c2c_topview.png, map_c2c.ply (ausgerichtete Karte
+ Abstand, nur lokal, nicht committen).
"""
import argparse
import os
import resource
import sys
import time

import numpy as np
import pye57
from plyfile import PlyData, PlyElement
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kpi  # noqa: E402

THRESH = (0.05, 0.10, 0.20)  # Anteile < 5 / 10 / 20 cm
N_SAMPLE = 3_000_000  # Scanpunkte (Stichprobe) als grauer Hintergrund der Draufsicht


def load_T(run_dir, gt):
    """T_gt_est aus dem Run-Ordner oder wie evo_ape -a neu berechnen (und speichern)."""
    path = os.path.join(run_dir, "T_gt_est.txt")
    if os.path.exists(path):
        T = np.loadtxt(path, comments="#")
        assert T.shape == (4, 4), T.shape
        return T
    _, _, T = kpi.align(gt, os.path.join(run_dir, "traj_imu.tum"))
    np.savetxt(path, T, fmt="%.9f", header="T_gt_est: p_gt = T @ p_est (SE(3)-Umeyama, ohne Skalierung, wie evo_ape -a)")
    print(f"T_gt_est.txt berechnet und gespeichert: {path}")
    return T


def load_map(path, T):
    v = PlyData.read(path)["vertex"].data
    p = np.column_stack([v["x"], v["y"], v["z"]]).astype(np.float64)
    return p @ T[:3, :3].T + T[:3, 3], v


def scan_blocks(path, chunk):
    """Scan blockweise lesen, Header-Pose anwenden. Liefert (n_gesamt, Generator über xyz-Blöcke).

    Gleiche Punkte und dieselbe Rechnung wie pye57 read_scan(transform=True): ungültige Punkte (InvalidState,
    falls vorhanden) verwerfen, dann E57.to_global mit der Pose aus dem Header.
    """
    e = pye57.E57(path)
    if e.scan_count != 1:
        sys.exit(f"erwartet 1 Scan, gefunden {e.scan_count}")
    h = e.get_header(0)
    if h.get_coordinate_system(pye57.e57.COORDINATE_SYSTEMS) is not pye57.e57.COORDINATE_SYSTEMS.CARTESIAN:
        sys.exit("nur kartesische E57-Scans werden unterstützt")
    fields = ["cartesianX", "cartesianY", "cartesianZ"]
    has_invalid = "cartesianInvalidState" in h.point_fields
    if has_invalid:
        fields.append("cartesianInvalidState")

    def gen():
        buf, buffers = e.make_buffers(fields, chunk)
        reader = h.points.reader(buffers)
        try:
            while (n := reader.read()) > 0:
                xyz = np.column_stack([buf["cartesianX"][:n], buf["cartesianY"][:n], buf["cartesianZ"][:n]])
                if has_invalid:
                    xyz = xyz[~buf["cartesianInvalidState"][:n].astype("?")]
                if h.has_pose():
                    xyz = e.to_global(xyz, h.rotation, h.translation)
                yield xyz
        finally:
            reader.close()

    return h.point_count, gen()


def c2c(scan, pm, lo, hi, margin, chunk):
    """Exakter Abstand jedes Kartenpunkts zum nächsten Scanpunkt (inf, wenn > margin), blockweise über den Scan.

    Rückgabe: Abstände, Scanpunkte gesamt, Scanpunkte in der Box, Stichprobe der Boxpunkte für die Draufsicht.
    """
    n_all, blocks = scan_blocks(scan, chunk)
    d = np.full(len(pm), np.inf)
    rng = np.random.default_rng(0)
    q = min(1.0, 10 * N_SAMPLE / n_all)  # Stichprobe (Sheldonian ~10 %, ~140 MB), am Ende auf N_SAMPLE gekürzt
    sample, n_read, n_box, t0, next_report = [], 0, 0, time.time(), 0.1
    for xyz in blocks:
        n_read += len(xyz)
        xyz = xyz[np.all((xyz >= lo) & (xyz <= hi), axis=1)]
        if len(xyz):
            n_box += len(xyz)
            sample.append(xyz[rng.random(len(xyz)) < q].astype(np.float32))
            # nur Kartenpunkte, die näher als margin an der Box dieses Blocks liegen, können hier einen Partner haben
            sel = np.flatnonzero(np.all((pm >= xyz.min(0) - margin) & (pm <= xyz.max(0) + margin), axis=1))
            if len(sel):
                dc, _ = cKDTree(xyz, leafsize=32).query(pm[sel], k=1, distance_upper_bound=margin, workers=-1)
                d[sel] = np.minimum(d[sel], dc)
        if n_read / n_all >= next_report:
            print(f"  Scan {100 * n_read / n_all:3.0f} %  ({n_box} Punkte in der Box, {time.time() - t0:.0f} s)",
                  flush=True)
            next_report += 0.1
    sample = np.concatenate(sample) if sample else np.empty((0, 3), np.float32)
    if len(sample) > N_SAMPLE:
        sample = sample[rng.choice(len(sample), N_SAMPLE, replace=False)]
    return d, n_all, n_box, sample


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir")
    ap.add_argument("scan")
    ap.add_argument("--gt", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "gt", "exp14_gt.tum"))
    ap.add_argument("--margin", type=float, default=2.0,
                    help="Rand um die Kartenbox beim Zuschneiden des Scans [m]. Abstände bis zu diesem Wert sind exakt.")
    ap.add_argument("--chunk", type=int, default=5_000_000,
                    help="Scanpunkte je Block. Kleiner = weniger RAM, das Ergebnis ändert sich nicht.")
    a = ap.parse_args()

    out = os.path.join(a.run_dir, "c2c")
    os.makedirs(out, exist_ok=True)
    t0 = time.time()

    T = load_T(a.run_dir, a.gt)
    pm, vmap = load_map(os.path.join(a.run_dir, "map.ply"), T)
    lo, hi = pm.min(0) - a.margin, pm.max(0) + a.margin
    print(f"Karte: {len(pm)} Punkte, Box {np.round(lo, 1)} .. {np.round(hi, 1)}", flush=True)

    d, n_all, n_box, sub = c2c(a.scan, pm, lo, hi, a.margin, a.chunk)
    n_far = int(np.isinf(d).sum())
    d[np.isinf(d)] = a.margin  # > margin: nur als untere Schranke zählbar
    peak_gb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 2
    print(f"Scan: {n_all} Punkte gesamt, {n_box} in der Box, Abstände fertig "
          f"({time.time() - t0:.0f} s, Spitze {peak_gb:.1f} GB RAM)", flush=True)

    lines = [
        "# C2C SLAM-Karte -> Hilti-Referenzscan (Nächster Nachbar, ohne lokales Modell, ohne ICP)",
        f"karte          {os.path.join(a.run_dir, 'map.ply').replace(os.sep, '/')}  ({len(pm)} Punkte)",
        f"ausrichtung    T_gt_est.txt (SE(3)-Umeyama wie evo, ohne Skalierung)",
        f"scan           {os.path.basename(a.scan)}  ({n_all} Punkte, volle Auflösung, Header-Pose angewendet)",
        f"scan_in_box    {n_box}  (Kartenbox + {a.margin} m)",
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
    with open(os.path.join(out, "c2c.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write(txt + "\n")

    # ausgerichtete Karte mit Abstand als Skalarfeld (für die Ansicht in CloudCompare, nur lokal)
    has_rgb = all(c in vmap.dtype.names for c in ("red", "green", "blue"))
    fields = [("x", "f4"), ("y", "f4"), ("z", "f4")] + ([("red", "u1"), ("green", "u1"), ("blue", "u1")] if has_rgb else [])
    v = np.empty(len(pm), dtype=fields + [("c2c", "f4")])
    v["x"], v["y"], v["z"] = pm.T.astype(np.float32)
    if has_rgb:
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
    # Diagnose-Draufsicht: Karte nach C2C eingefärbt über dem Scan (grau, Stichprobe), getrennt Keller / oben
    est = np.loadtxt(os.path.join(a.run_dir, "traj_imu.tum"))
    tr = est[:, 1:4] @ T[:3, :3].T + T[:3, 3]
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
