#!/usr/bin/env python3
"""Trajektorien-Plot für das Paper: SR-LIVO vs. Ground Truth (Exp14).

Ausrichtung wie evo: Zuordnung über Zeitstempel (|dt| <= 0.05 s), SE(3)-Umeyama ohne Skalierung.
Zur Kontrolle wird die ATE ausgegeben (muss mit evo_ape übereinstimmen).
Schreibt außerdem die Ausrichtung T_gt_est (4x4) für die Karte (CloudCompare).

Aufruf (im Container, aus /work/sr_livo):
  python3 scripts/plot_traj.py results/exp14/run_10 [GT]
Ausgabe im Run-Ordner: traj_paper.pdf, traj_paper.png, T_gt_est.txt
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

T0_BAG = 1649764528.07          # Start des Exp14-Bags (Unix-s)
NARROW = (59.0, 66.0)           # enger Treppenaufgang (75 % der LiDAR-Punkte < 1 m), Bag-Zeit [s]
T_MAX_DIFF = 0.05

# Farben: Referenzpalette (dataviz-Skill), nur eine Datenfarbe; GT als neutrale Referenz
C_EST = "#2a78d6"     # Serie 1 (blau)
C_GT = "#52514e"      # text-secondary (neutral)
C_INK = "#0b0b0b"
C_MUTED = "#898781"
C_GRID = "#e1e0d9"
C_AXIS = "#c3c2b7"
C_BAND = "#efeee9"


def load_tum(path):
    a = np.loadtxt(path)
    return a[:, 0], a[:, 1:4], a[:, 4:8]


def associate(t_ref, t_est, max_diff):
    """Wie evo: zu jedem Referenz-Zeitstempel den nächstgelegenen Schätz-Zeitstempel (eindeutig)."""
    idx = np.searchsorted(t_est, t_ref)
    idx = np.clip(idx, 1, len(t_est) - 1)
    left, right = t_est[idx - 1], t_est[idx]
    idx = idx - ((t_ref - left) < (right - t_ref))
    ok = np.abs(t_est[idx] - t_ref) <= max_diff
    i_ref = np.nonzero(ok)[0]
    i_est = idx[ok]
    _, first = np.unique(i_est, return_index=True)   # Doppelzuordnungen vermeiden
    return i_ref[first], i_est[first]


def umeyama_se3(src, dst):
    """R, t mit dst ≈ R @ src + t (ohne Skalierung)."""
    mu_s, mu_d = src.mean(0), dst.mean(0)
    cov = (dst - mu_d).T @ (src - mu_s) / len(src)
    U, _, Vt = np.linalg.svd(cov)
    S = np.eye(3)
    if np.linalg.det(U) * np.linalg.det(Vt) < 0:
        S[2, 2] = -1
    R = U @ S @ Vt
    return R, mu_d - R @ mu_s


def style_axes(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(C_AXIS)
        ax.spines[s].set_linewidth(0.8)
    ax.tick_params(colors=C_MUTED, labelcolor=C_INK, width=0.8, labelsize=7)
    ax.grid(True, color=C_GRID, linewidth=0.5)
    ax.set_axisbelow(True)


def main():
    run = sys.argv[1]
    gt_path = sys.argv[2] if len(sys.argv) > 2 else (
        "/work/common/gt/exp14_gt.tum" if os.path.exists("/work/common/gt/exp14_gt.tum")
        else "/data/exp14_basement_2_imu.txt")

    t_e, p_e, _ = load_tum(os.path.join(run, "traj_imu.tum"))
    t_g, p_g, _ = load_tum(gt_path)
    i_g, i_e = associate(t_g, t_e, T_MAX_DIFF)
    R, t = umeyama_se3(p_e[i_e], p_g[i_g])
    p_e_al = p_e @ R.T + t
    err = np.linalg.norm(p_e_al[i_e] - p_g[i_g], axis=1)
    tt = t_g[i_g] - T0_BAG

    print(f"GT: {gt_path}")
    print(f"Zuordnungen: {len(i_g)} von {len(t_g)} GT-Posen")
    print(f"ATE [m]: rmse {np.sqrt((err**2).mean()):.4f}  mean {err.mean():.4f}  "
          f"median {np.median(err):.4f}  max {err.max():.4f}")
    m = (tt >= NARROW[0]) & (tt < NARROW[1])
    print(f"ATE im engen Treppenaufgang {NARROW[0]:.0f}-{NARROW[1]:.0f} s: mean {err[m].mean():.4f}  max {err[m].max():.4f}")

    T = np.eye(4)
    T[:3, :3], T[:3, 3] = R, t
    np.savetxt(os.path.join(run, "T_gt_est.txt"), T, fmt="%.9f",
               header="T_gt_est: p_gt = T @ p_est (SE(3)-Umeyama, ohne Skalierung, wie evo_ape -a)")

    plt.rcParams.update({"font.family": "serif", "font.size": 8, "axes.labelsize": 8,
                         "pdf.fonttype": 42, "ps.fonttype": 42})
    fig = plt.figure(figsize=(3.45, 3.7))   # IEEE-Spaltenbreite
    gs = fig.add_gridspec(2, 1, height_ratios=[1.25, 1.0], hspace=0.55)

    # (a) Draufsicht
    ax = fig.add_subplot(gs[0])
    style_axes(ax)
    ax.plot(p_g[:, 0], p_g[:, 1], color=C_GT, lw=1.6, ls=(0, (4, 2)), label="Ground truth", zorder=2)
    ax.plot(p_e_al[:, 0], p_e_al[:, 1], color=C_EST, lw=1.2, label="SR-LIVO", zorder=3)
    nar = (t_e - T0_BAG >= NARROW[0]) & (t_e - T0_BAG < NARROW[1])
    ax.plot(p_e_al[nar, 0], p_e_al[nar, 1], color=C_EST, lw=3.2, alpha=0.35, solid_capstyle="round", zorder=1)
    ax.plot(*p_g[0, :2], marker="o", ms=5, mfc="white", mec=C_INK, mew=0.9, zorder=4)
    ax.plot(*p_g[-1, :2], marker="s", ms=5, mfc=C_INK, mec=C_INK, zorder=4)
    ax.annotate("Start", p_g[0, :2], xytext=(6, -2), textcoords="offset points", fontsize=7, color=C_INK, va="top")
    ax.annotate("End", p_g[-1, :2], xytext=(0, -7), textcoords="offset points", fontsize=7, color=C_INK,
                ha="center", va="top")
    k = np.argmin(np.abs(t_e - T0_BAG - np.mean(NARROW)))
    ax.annotate("narrow stairway", p_e_al[k, :2], xytext=(14, -4), textcoords="offset points", fontsize=7,
                color=C_INK, ha="left", va="center", arrowprops=dict(arrowstyle="-", color=C_MUTED, lw=0.6))
    ax.set_aspect("equal", adjustable="datalim")
    ax.set_xlabel("x [m]")
    ax.set_ylabel("y [m]")
    ax.legend(loc="lower center", fontsize=7, frameon=False, handlelength=2.6, ncol=2)
    ax.set_title("(a) Top view, SE(3)-aligned", fontsize=8, loc="left", color=C_INK)

    # (b) Fehler über die Zeit
    ax2 = fig.add_subplot(gs[1])
    style_axes(ax2)
    ax2.axvspan(*NARROW, color=C_BAND, lw=0, zorder=0)
    ax2.text(np.mean(NARROW), 1.0, "narrow\nstairway", transform=ax2.get_xaxis_transform(), ha="center",
             va="top", fontsize=6.5, color=C_MUTED)
    ax2.plot(tt, err * 100, color=C_EST, lw=1.0)
    rmse = np.sqrt((err**2).mean()) * 100
    ax2.axhline(rmse, color=C_MUTED, lw=0.8, ls=(0, (2, 2)))
    # Label dort, wo die Kurve am niedrigsten ist (keine Überlappung)
    win = [(a, a + 10) for a in range(15, 50, 2)]
    a0 = min(win, key=lambda w: err[(tt >= w[0]) & (tt < w[1])].max() if ((tt >= w[0]) & (tt < w[1])).any() else 1e9)[0]
    ax2.text(a0, rmse + 0.4, f"RMSE {rmse:.1f} cm", fontsize=6.5, color=C_MUTED, va="bottom")
    ax2.set_xlim(0, 75)
    ax2.set_ylim(0, max(15, err.max() * 110))
    ax2.set_xlabel("time [s]")
    ax2.set_ylabel("APE [cm]")
    ax2.set_title("(b) Absolute position error", fontsize=8, loc="left", color=C_INK)

    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(run, f"traj_paper.{ext}"), dpi=300, bbox_inches="tight", facecolor="white")
    print("geschrieben:", os.path.join(run, "traj_paper.pdf/.png"), "und T_gt_est.txt")


if __name__ == "__main__":
    main()
