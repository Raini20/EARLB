#!/usr/bin/env python3
"""Gruppenvergleich auf main: wertet aus, was unter systems/*/results/exp14/ schon da ist.

Fehlende Systeme blockieren nichts: Sie erscheinen in comparison/status.md als offen, Tabelle und Abbildungen
enthalten die vorhandenen. Einfach erneut ausführen, sobald ein weiteres System gemergt ist.

Aufruf aus der Repo-Wurzel im Auswerte-Image (siehe common/README.md):
    python common/eval/compare.py

Referenzlauf je System:
  - Datei systems/<system>/results/exp14/REFERENCE mit einer Run-Nummer pro Zeile (z. B. "10").
    Die erste Zeile ist der Referenzlauf. Stehen mehrere Läufe drin (z. B. OpenMAVIS, nicht deterministisch),
    gibt die Tabelle zusätzlich Mittelwert ± Streuung der ATE über diese Läufe an.
  - Ohne Datei: der höchste run_<n> mit voller Abdeckung (letzte Pose >= 73,5 s Bag-Zeit).

Ausgabe in comparison/:
  kpi_table.md / .csv      ATE, RPE (1 m), Abdeckung, Kartengenauigkeit (falls c2c/c2c.txt vorhanden)
  overlay_xy.pdf / .png    Trajektorien-Overlay aller Systeme mit GT (Paper: Serif, 10 pt, 300 DPI, graustufentauglich)
  ape_time.pdf / .png      ATE über der Bag-Zeit, enger Treppenaufgang markiert
  status.md                was je System vorhanden ist und was fehlt
"""
import csv
import datetime
import glob
import os
import re
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kpi  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
GT = os.path.join(ROOT, "common", "gt", "exp14_gt.tum")
OUT = os.path.join(ROOT, "comparison")
FULL_COVERAGE_S = 73.5          # letzte Pose ab hier = volle Sequenz (Ende 73,8 s)
NARROW = (59.0, 66.0)           # enger Treppenaufgang, Bag-Zeit [s]

# (Ordner, Anzeigename, Person, dichte Karte für C2C erwartet, Linienstil, Graustufe)
SYSTEMS = [
    ("openmavis", "OpenMAVIS", "Felix", False, (0, (1, 1.2)), "0.55"),
    ("mola_lo", "MOLA-LO", "Victor", True, (0, (5, 1.5)), "0.35"),
    ("kiss_slam", "KISS-SLAM", "Merle", True, (0, (4, 1.2, 1, 1.2)), "0.45"),
    ("sr_livo", "SR-LIVO", "Rainhard", True, (0, (2.2, 1.2)), "0.15"),
]


def runs_of(sys_dir):
    runs = {}
    for p in glob.glob(os.path.join(sys_dir, "run_*", "traj_imu.tum")):
        m = re.search(r"run_(\d+)$", os.path.dirname(p))
        if m:
            runs[int(m.group(1))] = os.path.dirname(p)
    return runs


def last_pose_bag_time(run_dir):
    t = np.loadtxt(os.path.join(run_dir, "traj_imu.tum"), usecols=0, ndmin=1)
    return float(t.min() - kpi.T0_BAG), float(t.max() - kpi.T0_BAG), len(t)


def pick_runs(sys_dir, runs):
    ref_file = os.path.join(sys_dir, "REFERENCE")
    if os.path.exists(ref_file):
        ids = [int(re.sub(r"\D", "", l)) for l in open(ref_file, encoding="utf-8") if re.search(r"\d", l)]
        missing = [i for i in ids if i not in runs]
        return [i for i in ids if i in runs], "REFERENCE", missing
    full = [i for i in sorted(runs) if last_pose_bag_time(runs[i])[1] >= FULL_COVERAGE_S]
    if full:
        return [full[-1]], "höchster Lauf mit voller Abdeckung", []
    return ([max(runs)] if runs else []), "höchster Lauf (keiner mit voller Abdeckung)", []


def read_c2c(run_dir):
    p = os.path.join(run_dir, "c2c", "c2c.txt")
    if not os.path.exists(p):
        return None
    vals = {}
    for line in open(p, encoding="utf-8"):
        if line.startswith("#"):
            continue
        k, _, v = line.partition(" ")
        num = re.match(r"\s*([\d.]+)", v)
        if num:
            vals[k] = float(num.group(1))
    return vals


def git_head():
    if os.environ.get("GIT_COMMIT"):
        return os.environ["GIT_COMMIT"]
    try:
        return subprocess.check_output(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"], text=True,
                                       stderr=subprocess.DEVNULL).strip()
    except Exception:
        return "?"


def cm(x):
    """Meter -> cm, eine Nachkommastelle, kaufmännisch gerundet (3,25 -> 3,3 wie in den READMEs)."""
    return f"{np.floor(1000 * x + 0.5 + 1e-9) / 10:.1f}"


def main():
    os.makedirs(OUT, exist_ok=True)
    rows, status, curves = [], [], []

    for key, name, person, dense, ls, gray in SYSTEMS:
        sys_dir = os.path.join(ROOT, "systems", key, "results", "exp14")
        runs = runs_of(sys_dir)
        st = {"name": name, "person": person, "runs": sorted(runs), "notes": []}
        status.append(st)
        if not runs:
            st["state"] = "offen: keine traj_imu.tum unter " + os.path.relpath(sys_dir, ROOT) + "/run_<n>/"
            continue

        sel, how, missing = pick_runs(sys_dir, runs)
        if missing:
            st["notes"].append(f"REFERENCE nennt fehlende Läufe: {missing}")
        if not sel:
            st["state"] = "offen: REFERENCE verweist auf keinen vorhandenen Lauf"
            continue
        ref_id = sel[0]
        rd = runs[ref_id]
        t_first, t_last, n_est = last_pose_bag_time(rd)
        ref, est, T = kpi.align(GT, os.path.join(rd, "traj_imu.tum"))
        s = kpi.stats(ref, est)
        n_gt = len(np.loadtxt(GT, usecols=0))

        spread = ""
        if len(sel) > 1:
            rm = [kpi.stats(*kpi.align(GT, os.path.join(runs[i], "traj_imu.tum"))[:2])["ape"]["rmse"] for i in sel]
            spread = f"{cm(np.mean(rm))} ± {cm(np.std(rm, ddof=1))} (n={len(rm)})"

        c2c = read_c2c(rd)
        row = {
            "System": name, "Lauf": f"run_{ref_id}",
            "ATE RMSE [cm]": cm(s["ape"]["rmse"]), "ATE Mean [cm]": cm(s["ape"]["mean"]),
            "ATE Median [cm]": cm(s["ape"]["median"]), "ATE Max [cm]": cm(s["ape"]["max"]),
            "ATE RMSE über Läufe [cm]": spread,
            "RPE 1 m trans RMSE [cm]": cm(s["rpe_trans"]["rmse"]),
            "RPE 1 m rot RMSE [°]": f"{s['rpe_rot']['rmse']:.2f}",
            "Abdeckung [s]": f"{t_first:.1f}–{t_last:.1f}",
            "GT-Zuordnung": f"{s['matched']}/{n_gt} ({100 * s['matched'] / n_gt:.0f} %)",
            "C2C Median [cm]": cm(c2c["median_m"]) if c2c else ("–" if not dense else ""),
            "C2C < 5 / < 10 cm [%]": f"{c2c['anteil_<5cm']:.0f} / {c2c['anteil_<10cm']:.0f}" if c2c else ("–" if not dense else ""),
        }
        rows.append(row)

        # Abbildungsdaten: ganze Schätzung in den GT-Frame, APE je zugeordneter Pose über Bag-Zeit
        tb, xyz = kpi.full_trajectory_aligned(os.path.join(rd, "traj_imu.tum"), T)
        err = np.linalg.norm(est.positions_xyz - ref.positions_xyz, axis=1)
        curves.append((name, ls, gray, xyz, est.timestamps - kpi.T0_BAG, err))

        # Status
        st["state"] = f"ausgewertet (run_{ref_id}, Auswahl: {how})"
        if t_last < FULL_COVERAGE_S:
            st["notes"].append(f"Abdeckung endet bei {t_last:.1f} s (< {FULL_COVERAGE_S} s): Lauf unvollständig")
        for f in ("ape.zip", "rpe_trans.zip", "rpe_rot.zip", "run.md"):
            if not os.path.exists(os.path.join(rd, f)):
                st["notes"].append(f"{f} fehlt im Run-Ordner (Ausgabevertrag)")
        if dense and not os.path.exists(os.path.join(rd, "map.ply")):
            st["notes"].append("map.ply fehlt (für C2C nötig)")
        elif dense and not c2c:
            st["notes"].append("C2C noch nicht gerechnet (common/eval/c2c_scan.py)")
        if not dense:
            st["notes"].append("C2C entfällt laut KPI-Absprache (keine dichte Karte), nur qualitativ")
        off = kpi.run_offset(rd)
        if off:
            st["notes"].append(f"Zeitversatz {off:+.3f} s aus t_offset.txt angewendet (Begründung in run.md)")
        if s["matched"] < 0.8 * n_gt:
            st["notes"].append("wenige GT-Zuordnungen: Zeitversatz prüfen (t_offset.txt, in run.md begründen)")

    write_tables(rows)
    write_figures(curves)
    write_status(status, rows)
    print(open(os.path.join(OUT, "status.md"), encoding="utf-8").read())


def write_tables(rows):
    cols = ["System", "Lauf", "ATE RMSE [cm]", "ATE Mean [cm]", "ATE Median [cm]", "ATE Max [cm]",
            "ATE RMSE über Läufe [cm]", "RPE 1 m trans RMSE [cm]", "RPE 1 m rot RMSE [°]",
            "Abdeckung [s]", "GT-Zuordnung", "C2C Median [cm]", "C2C < 5 / < 10 cm [%]"]
    with open(os.path.join(OUT, "kpi_table.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(OUT, "kpi_table.md"), "w", encoding="utf-8") as f:
        f.write("| " + " | ".join(cols) + " |\n| " + " | ".join("---" for _ in cols) + " |\n")
        for r in rows:
            f.write("| " + " | ".join(r[c] or "" for c in cols) + " |\n")
        f.write("\nATE/RPE: evo, SE(3)-Umeyama ohne Skalierung, Zuordnung ±0,05 s, RPE über 1 m. "
                "ATE-Unterschiede unter ~2 cm nicht als Rangfolge lesen (GT-Genauigkeit 1–2 cm). "
                "C2C: Karte → Hilti-Laserscan, nur mit der Trajektorien-Ausrichtung, ohne ICP.\n")


def paper_style():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "font.family": "serif", "font.serif": ["STIXGeneral", "DejaVu Serif"], "mathtext.fontset": "stix",
        "font.size": 10, "axes.labelsize": 10, "legend.fontsize": 10, "xtick.labelsize": 10, "ytick.labelsize": 10,
        "axes.linewidth": 0.6, "pdf.fonttype": 42, "savefig.dpi": 300,
    })
    return plt


def write_figures(curves):
    plt = paper_style()
    gt = np.loadtxt(GT)

    def legend_below(fig, ax, ncol):
        """Legende unter der x-Achsenbeschriftung, ohne Überlappung (Platz wird nach Zeilenzahl reserviert)."""
        h, l = ax.get_legend_handles_labels()
        rows = -(-len(h) // ncol)
        leg_in = 0.22 * rows + 0.08                      # Höhe der Legende in Zoll (10 pt)
        frac = leg_in / fig.get_figheight()
        fig.legend(h, l, loc="lower center", ncol=ncol, frameon=False, handlelength=2.6, columnspacing=1.2,
                   bbox_to_anchor=(0.5, 0.0))
        fig.tight_layout(rect=(0, frac, 1, 1))

    # Overlay Draufsicht, IEEE-Spaltenbreite 3,5 in (Beschriftung englisch wie das Paper)
    n_leg = len(curves) + 1
    fig, ax = plt.subplots(figsize=(3.5, 2.1 + 0.22 * -(-n_leg // 3)))
    ax.plot(gt[:, 1], gt[:, 2], color="black", lw=1.4, label="Ground truth", zorder=1)
    for name, ls, gray, xyz, *_ in curves:
        ax.plot(xyz[:, 0], xyz[:, 1], color=gray, lw=1.1, ls=ls, label=name, zorder=2)
    ax.plot(gt[0, 1], gt[0, 2], "o", ms=4, mfc="white", mec="black", zorder=3)
    ax.set_aspect("equal")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    legend_below(fig, ax, 3)
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(OUT, f"overlay_xy.{ext}"), bbox_inches="tight")
    plt.close(fig)

    # ATE über Bag-Zeit
    fig, ax = plt.subplots(figsize=(3.5, 2.0 + 0.22 * -(-(len(curves) + 1) // 2)))
    ax.axvspan(*NARROW, color="0.88", lw=0, label="Narrow stairway")
    for name, ls, gray, _xyz, t, err in curves:
        ax.plot(t, err * 100, color=gray, lw=1.0, ls=ls, label=name)
    ax.set_xlabel("Bag time [s]")
    ax.set_ylabel("ATE [cm]")
    ax.set_xlim(0, 75)
    ax.set_ylim(bottom=0)
    legend_below(fig, ax, 2)
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(OUT, f"ape_time.{ext}"), bbox_inches="tight")
    plt.close(fig)


def write_status(status, rows):
    done = sum(1 for s in status if s.get("state", "").startswith("ausgewertet"))
    with open(os.path.join(OUT, "status.md"), "w", encoding="utf-8") as f:
        f.write(f"# Vergleich Exp14 – Stand\n\nErzeugt {datetime.date.today().isoformat()} mit "
                f"`common/eval/compare.py` auf Commit `{git_head()}`. **{done} von {len(status)} Systemen ausgewertet.**\n\n")
        f.write("| System | Person | Läufe gefunden | Stand |\n| --- | --- | --- | --- |\n")
        for s in status:
            runs = ", ".join(map(str, s["runs"])) if s["runs"] else "–"
            f.write(f"| {s['name']} | {s['person']} | {runs} | {s['state']} |\n")
        f.write("\n## Hinweise je System\n\n")
        noted = [s for s in status if s["notes"]]
        for s in noted:
            f.write(f"**{s['name']}**\n\n" + "".join(f"- {n}\n" for n in s["notes"]) + "\n")
        if not noted:
            f.write("Keine Auffälligkeiten bei den ausgewerteten Systemen.\n\n")
        f.write("## Ergebnisse\n\nSiehe `kpi_table.md`, `overlay_xy.pdf`, `ape_time.pdf`. "
                "Fehlende Systeme fehlen dort einfach; nach jedem Merge `compare.py` erneut ausführen.\n")


if __name__ == "__main__":
    main()
