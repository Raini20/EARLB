"""Gemeinsame KPI-Berechnung mit der evo-API, identisch zu den evo-CLI-Befehlen in evaluate.sh.

- Zeitzuordnung: sync.associate_trajectories, max_diff 0,05 s (wie --t_max_diff 0.05),
  Zeitversatz aus <run>/t_offset.txt (wie --t_offset in evaluate.sh)
- Ausrichtung: SE(3)-Umeyama ohne Skalierung (wie -a)
- ATE: translation_part, RPE: 1 m, consecutive pairs, trans_part / angle_deg
"""
import copy
import os

import numpy as np
from evo.core import metrics, sync
from evo.core.units import Unit
from evo.tools import file_interface

T_MAX_DIFF = 0.05
T0_BAG = 1649764528.07  # Bag-Zeit 0 von exp14_basement_2.bag (Unix-s)


def load(path):
    return file_interface.read_tum_trajectory_file(path)


def run_offset(run_dir):
    """Zeitversatz des Laufs für die Zuordnung (wie --t_offset): Inhalt von <run>/t_offset.txt, sonst 0.

    Dieselbe Datei liest evaluate.sh, damit ape.zip und der Gruppenvergleich mit demselben Wert rechnen.
    """
    p = os.path.join(run_dir, "t_offset.txt")
    if not os.path.exists(p):
        return 0.0
    return float(open(p, encoding="utf-8").read().split()[0])


def align(gt_path, est_path, t_offset=None):
    """Zuordnen + ausrichten. Gibt (ref, est_aligned, T_gt_est 4x4) zurück, p_gt = T @ p_est.

    t_offset=None: aus t_offset.txt neben est_path (fehlt die Datei: 0).
    """
    if t_offset is None:
        t_offset = run_offset(os.path.dirname(os.path.abspath(est_path)))
    # Schlüsselwortargumente: ab evo 1.32 sind max_diff/offset_2 keyword-only
    ref, est = sync.associate_trajectories(load(gt_path), load(est_path), max_diff=T_MAX_DIFF, offset_2=t_offset)
    est = copy.deepcopy(est)
    r, t, _ = est.align(ref, correct_scale=False)
    T = np.eye(4)
    T[:3, :3], T[:3, 3] = r, t
    return ref, est, T


def stats(ref, est):
    ape = metrics.APE(metrics.PoseRelation.translation_part)
    ape.process_data((ref, est))
    out = {"ape": ape.get_all_statistics(), "matched": est.num_poses}
    for key, rel in (("rpe_trans", metrics.PoseRelation.translation_part),
                     ("rpe_rot", metrics.PoseRelation.rotation_angle_deg)):
        rpe = metrics.RPE(rel, delta=1.0, delta_unit=Unit.meters, all_pairs=False)
        rpe.process_data((ref, est))
        out[key] = rpe.get_all_statistics()
    return out


def full_trajectory_aligned(est_path, T):
    """Ganze Schätzung (auch Posen ohne GT-Partner) mit T in den GT-Frame bringen: (t_bag, xyz)."""
    raw = np.loadtxt(est_path)
    xyz = raw[:, 1:4] @ T[:3, :3].T + T[:3, 3]
    return raw[:, 0] - T0_BAG, xyz
