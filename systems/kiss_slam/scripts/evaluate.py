import os
import shutil
import subprocess

import glob
import open3d as o3d

import numpy as np

os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/..")  # immer aus systems/kiss_slam starten

GT = os.path.expanduser("~/data/hilti2022/exp14_basement_2_imu.txt")
RUN = "results/exp14/run_3"  # gleicher Wert wie in run_kiss_slam.py
EST = f"{RUN}/traj_imu.tum"
OPT = "-a --t_max_diff 0.05 --no_warnings"


def run(cmd):
    subprocess.run(cmd, shell=True, check=True)


# KISS-Trajektorie holen und vom LiDAR- in den IMU-Frame umrechnen
os.makedirs(RUN, exist_ok=True)
shutil.copy("slam_output/latest/exp14_basement_2_poses_tum.txt", f"{RUN}/kiss_lidar.txt")
shutil.copy(f"{RUN}/kiss_lidar.txt", f"{RUN}/traj_lidar.tum")
run(f"cd {RUN} && evo_traj tum kiss_lidar.txt --transform_right ../../../calib/T_lidar_imu.json --save_as_tum --no_warnings")
shutil.move(f"{RUN}/kiss_lidar.tum", EST)

# ATE und RPE (1 m) wie im Gruppen-PDF
run(f"evo_ape tum {GT} {EST} {OPT} --save_results {RUN}/ape.zip")
run(f"evo_rpe tum {GT} {EST} {OPT} --delta 1 --delta_unit m -r trans_part --save_results {RUN}/rpe_trans.zip")
run(f"evo_rpe tum {GT} {EST} {OPT} --delta 1 --delta_unit m -r angle_deg --save_results {RUN}/rpe_rot.zip")

# Plot: KISS-SLAM gegen Ground Truth
run(f"evo_traj tum {EST} --ref {GT} {OPT} -p --plot_mode xy --save_plot {RUN}/traj_xy.pdf")

# Karte: lokale Karten zusammenfügen, als map.ply speichern und anzeigen
karte = o3d.geometry.PointCloud()
for f in sorted(glob.glob("slam_output/latest/local_maps/plys/*.ply")):
    karte += o3d.io.read_point_cloud(f)
o3d.io.write_point_cloud(f"{RUN}/map.ply", karte)

traj = np.loadtxt(f"{RUN}/traj_imu.tum")[:, 1:4]
linie = o3d.geometry.LineSet(
    points=o3d.utility.Vector3dVector(traj),
    lines=o3d.utility.Vector2iVector([[i, i + 1] for i in range(len(traj) - 1)]),
)
linie.paint_uniform_color([1, 0, 0])
karte.paint_uniform_color([0.6, 0.6, 0.6])
o3d.visualization.draw_geometries([karte, linie])