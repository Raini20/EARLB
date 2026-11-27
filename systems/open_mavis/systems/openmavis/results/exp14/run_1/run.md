# OpenMAVIS – Exp14 – Run 1

- Datum: 2026-11-27
- OpenMAVIS Commit: `b13b1c20e84efa4bb63564e26308541af70d03f2` + Patch 0001 (Viewer optional)
- Repo-Commit: `fda1487`
- Config: `config_used.yaml`, unverändert (config/hilti_exp14.yaml)
- Viewer: aus
- Rechner: Intel(R) Core(TM) Ultra 9 275HX, 24 Threads, 15 GB RAM im Container
- Laufzeit: 170 s Wanduhr, Exit-Code 0
- Trajektorie: 2957 Posen, 1649764528.121 - 1649764602.013 s (73.9 s), Eingabe in s
- Karten im Atlas: 1 (gespeichert wird nur die größte Karte -> bei >1 Abdeckung prüfen)
- Frame: `traj_imu.tum` = IMU-Pose direkt aus OpenMAVIS (SaveTrajectoryEuRoC, IMU_MULTI), Zeit in s, keine Umrechnung

## Ergebnisse (evo, SE(3)-Umeyama, ohne Skalierung)

Nach `common/eval/evaluate.sh openmavis 1` aus ape.txt / rpe_*.txt eintragen.

| Metrik | RMSE | Mean | Median | Max |
| --- | --- | --- | --- | --- |
| APE trans [m] | | | | |
| RPE trans, 1 m [m] | | | | |
| RPE rot, 1 m [deg] | | | | |

## Auffälligkeiten

- 
