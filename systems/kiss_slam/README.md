# KISS-SLAM auf Hilti 2022 Exp14

KISS-SLAM (PRBonn, LiDAR-only) auf der Sequenz Exp14 Basement 2 der Hilti SLAM Challenge 2022.
Getestet auf macOS (Apple Silicon) mit Python 3.12 in einer Conda-Umgebung.

## Installation

```bash
brew install libusb
conda create -n kiss python=3.12 -y
conda activate kiss
python -m pip install -r requirements.txt
```

Hinweise:
- Immer `python` aus der Umgebung `kiss` verwenden, nicht `python3`.
- `map_closures==2.0.2` ist bewusst festgelegt: ab 2.1.0 fehlt `align_map_to_local_ground`, `--refuse-scans` stürzt dann ab. Diese Version braucht `numpy<2`, deshalb auch `pandas<3`.
- Open3D braucht auf macOS `libusb` von Homebrew.

## Daten

Nicht im Repo. Nach `~/data/hilti2022/` laden:

```bash
mkdir -p ~/data/hilti2022 && cd ~/data/hilti2022
curl -L --http1.1 -C - -O https://huggingface.co/datasets/Hilti-Research/hilti-slam-challenge-2022/resolve/main/rosbags/exp14_basement_2.bag
curl -L -O https://huggingface.co/datasets/Hilti-Research/hilti-slam-challenge-2022/resolve/main/ground_truth/exp14_basement_2_imu.txt
```

## Ausführen

Aus `systems/kiss_slam/`:

```bash
python scripts/run_kiss_slam.py
python scripts/evaluate.py
python scripts/align_map.py
```

In allen drei Skripten steht oben `RUN` (Ergebnisordner); für jeden neuen Lauf einen neuen Ordner wählen. Die Config wählt `CONFIG` in `run_kiss_slam.py`.

`run_kiss_slam.py` startet KISS-SLAM (Topic `/hesai/pandar`, Config `config/kiss_slam_hilti.yaml`, mit Visualisierung: im Fenster mit der Leertaste starten) und schreibt `run.md`.
`evaluate.py` rechnet die Trajektorie in den IMU-Frame um, berechnet ATE und RPE mit evo und erzeugt die Karte.
`align_map.py` richtet die Karte mit derselben Transformation wie evo (`-a`) auf die Ground Truth aus (`T_gt_est.txt`, `map_aligned.ply`) – Grundlage für den CloudCompare-Vergleich mit `sheldonian_full.e57` (CloudCompare 2.13.2, kein ICP).

## Ergebnisse

`results/exp14/run_<n>/`:

| Datei | Inhalt |
|---|---|
| `traj_imu.tum` | Trajektorie im IMU-Frame, TUM (`t x y z qx qy qz qw`), geht in den Vergleich |
| `traj_lidar.tum` | Trajektorie im LiDAR-Frame, so wie KISS-SLAM sie ausgibt |
| `ape.zip`, `rpe_trans.zip`, `rpe_rot.zip` | evo-Ergebnisse (ATE, RPE über 1 m) |
| `map.ply` | Karte aus den lokalen Karten, im selben Weltframe wie die Trajektorie |
| `traj_xy.pdf` | Draufsicht KISS-SLAM gegen Ground Truth |
| `run.md`, `config_used.yaml` | Versionen, Config, Laufzeit, Auffälligkeiten |

Umrechnung LiDAR → IMU: `T_W_I = T_W_L · T_L_I` mit `calib/T_lidar_imu.json` (aus der Hilti-Kalibrierung).
