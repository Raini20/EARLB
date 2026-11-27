# MOLA-LO – Exp14 – run_3

- Datum: 2026-11-04T17:04:43+01:00
- System: ros-jazzy-mola-lidar-odometry 3.3.0-1noble.20261001.233519 (Binärpaket; nativ oder Docker-Image ../../../Dockerfile)
- Aufruf: mola-lo-cli-hilti2022 (Profil hilti2022, HILTI2022_BASE_FRAME=imu)
- Pipeline: lidar3d-default.yaml, Deskew IMU, Init PitchAndRollFromIMU, State Estimator Smoother
- Extrinsik LiDAR im IMU-Frame: x=-0.001 y=-0.00855 z=0.055 [m], yaw=-90 pitch=0 roll=180 [deg]
- Input: exp14_basement_2.bag, LiDAR /hesai/pandar (740 Scans, 10 Hz), IMU /alphasense/imu
- Laufzeit gesamt: 43 s (≈ 58.1 ms/Scan, inkl. Bag-Lesen)
- Posen in traj_imu.tum: 730
- Trajektorien-Varianten aus demselben Lauf: traj_imu.tum (Ausgabevertrag, reine LiDAR-Odometrie),
  traj_imu_fused.tum (State-Estimator-Fusion), traj_imu_smoothed.tum (finalisierte Keyframes);
  ATE-Vergleich in variants_ate.txt
- Karte: sm2mm (config/sm2mm_exp14.yaml, gerendert als sm2mm_exp14.rendered.yaml) -> mm2ply,
  Datei map.ply (988199 Punkte, 0.05-m-Voxel, Felder x,y,z,intensity, 16 MB)
- t_offset für evo: siehe t_offset.txt im selben Ordner (fehlt die Datei, rechnet evaluate.sh mit 0)
- Auffälligkeiten: (manuell ergänzen – ein erneuter Lauf sichert die alte run.md als run.md.bak.<Zeit>)
