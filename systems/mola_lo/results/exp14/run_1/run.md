# MOLA-LO – Exp14 – run_1

- Datum: 2026-11-04T18:32:17+01:00
- System: ros-jazzy-mola-lidar-odometry 3.3.0-1noble.20261001.233519 (Binärpaket; nativ oder Docker-Image ../../../Dockerfile)
  Der Ausgabevertrag verlangt den Commit-Hash des Systems. MOLA-LO kommt hier aus dem
  offiziellen apt-Repo, nicht aus einem Git-Checkout; die Paketversion oben ist die
  entsprechende, eindeutige Kennung. Das Dockerfile installiert dieselbe Version.
- Aufruf: mola-lo-cli-hilti2022 (Profil hilti2022, HILTI2022_BASE_FRAME=imu)
- Pipeline: lidar3d-default.yaml, Deskew IMU, Init PitchAndRollFromIMU, State Estimator Smoother
- Extrinsik LiDAR im IMU-Frame: x=-0.001 y=-0.00855 z=0.055 [m], yaw=-90 pitch=0 roll=180 [deg]
- Input: exp14_basement_2.bag, LiDAR /hesai/pandar (740 Scans, 10 Hz), IMU /alphasense/imu
- Laufzeit gesamt: 35 s (≈ 47.3 ms/Scan, inkl. Bag-Lesen)
- Posen in traj_imu.tum: 730
- Trajektorien-Varianten aus demselben Lauf: traj_imu.tum (Ausgabevertrag, reine LiDAR-Odometrie),
  traj_imu_fused.tum (State-Estimator-Fusion), traj_imu_smoothed.tum (finalisierte Keyframes);
  ATE-Vergleich in variants_ate.txt
- Karte: sm2mm (config/sm2mm_exp14.yaml, gerendert als sm2mm_exp14.rendered.yaml) -> mm2ply,
  Datei map.ply (986521 Punkte, 0.05-m-Voxel, Felder x,y,z,intensity, 16 MB)
- t_offset für evo: siehe t_offset.txt im selben Ordner (-0.05 s, Begründung unter Auffälligkeiten)
- Auffälligkeiten: (manuell ergänzen – ein erneuter Lauf sichert die alte run.md als run.md.bak.<Zeit>)

## KPIs (common/eval/evaluate.sh, evo 1.31.1 wie Image earlb-eval, t_offset -0.05)

| Metrik | RMSE | Mean | Median | Max |
|---|---|---|---|---|
| ATE (APE trans, SE(3)-Umeyama) | 0,1002 m | 0,0877 m | 0,0752 m | 0,2133 m |
| RPE 1 m, Translation | 0,0708 m | 0,0608 m | 0,0558 m | 0,1508 m |
| RPE 1 m, Rotation | 3,348° | 3,067° | 2,916° | 6,882° |

Zugeordnete Posen: 680 von 689 GT-Posen (98,7 %). Die fehlenden 9 liegen vor der ersten
MOLA-Pose: MOLA-LO liefert ab t_GT + 0,95 s.

Pfadlänge der Schätzung 38,37 m gegen 37,80 m der GT (+1,5 %). ATE nach Achse (Mittelwert
der Absolutwerte): x 6,8 cm, y 2,6 cm, z 3,3 cm – keine auffällige Höhendrift.

## Kartengenauigkeit (C2C zum Hilti-Laserscan, `c2c/`)

`common/eval/c2c_scan.py` gegen `sheldonian_full.e57` (285 Mio. Punkte, davon 108 Mio. in der
Kartenbox mit 2 m Rand), Karte nur mit `T_gt_est.txt` ausgerichtet (Umeyama wie `ape.zip`, t_offset −0,05), ohne ICP.

| Median | Mean | RMS | 90 % | 95 % | < 5 cm | < 10 cm | < 20 cm |
|---|---|---|---|---|---|---|---|
| 3,6 cm | 6,5 cm | 13,1 cm | 13,5 cm | 17,9 cm | 63,5 % | 83,1 % | 95,8 % |

506 von 986 521 Kartenpunkten liegen mehr als 2 m vom Scan entfernt (auf 2 m gekappt): durch
Türen und Fenster gemessene Bereiche, die der Referenzscan nicht enthält (rot in
`c2c/c2c_topview.png`). Gerechnet unter Windows mit 23 GB RAM: Der Scan wurde blockweise gelesen
und sofort zugeschnitten (sonst ~26 GB), Rechnung sonst unverändert, Laufzeit 71 s.

## Auffälligkeiten

- **Zeitraster um 50 ms phasenversetzt – aber kein Uhrenversatz.** Ohne `t_offset` ordnet
  evo nur 439 der 689 GT-Posen zu. Beide Trajektorien laufen mit 10 Hz, die Raster liegen
  aber in unterschiedlicher Phase. Die Differenz zum nächsten Nachbarn ist damit für *jede*
  Pose 50,0–50,9 ms und liegt genau auf der Matching-Schwelle `--t_max_diff 0.05`; welche
  Pose noch durchkommt, entscheidet Fließkomma-Rauschen. Daher die 64-%-Quote.
  Mit `t_offset = -0.05` steigt die Zuordnung auf 680 Posen und der ATE sinkt von 0,1057
  auf 0,1002 m; die Gegenprobe `+0.05` paart mit der jeweils nächsten GT-Pose und liefert
  0,1047 m. Jeder Wert ungleich 0 behebt die Zuordnung (geprüft über ein Raster
  −0,10…+0,10 s), `-0.05` legt die Raster exakt übereinander.
  **Ein echter Zeitversatz liegt nicht vor:** Ein kontinuierlicher Lag-Fit – GT per SLERP
  auf die Schätz-Zeitstempel interpoliert, Lag-Raster ±0,2 s in 10-ms-Schritten, Zielgröße
  der mittlere Rotationsfehler – hat sein Minimum bei exakt 0 ms (2,12°). Die 50 ms sind
  also ein Abtast-Phasenunterschied zweier unabhängiger 10-Hz-Reihen, kein
  Synchronisationsfehler. `FilterAdjustTimestamps` mit `MiddleIsZero` (aus
  `pipelines/blocks/observations-common.yaml`) verschiebt die *Punkt*-Zeitstempel innerhalb
  eines Sweeps für Deskew und Twist-Schätzung, nicht den Zeitstempel der ausgegebenen Pose –
  als Ursache kommt es nach dieser Messung nicht in Frage. Resteinfluss auf die KPIs:
  Interpolation bei Lag 0 ergibt ATE 0,0973 m gegen 0,1002 m mit `t_offset -0.05`, also
  0,3 cm und damit deutlich unter der GT-Genauigkeit von 1–2 cm. `t_offset = -0.05` bleibt
  die Wahl, weil es mit den Gruppenparametern in evo reproduzierbar ist.
- **Trajektorie liegt im IMU-Frame, wie beabsichtigt.** Wird `common/calib/T_lidar_imu.json`
  nachträglich per `evo_traj --transform_right` angewandt, springt der Rotations-APE von
  2,61° auf 178,72°. `HILTI2022_BASE_FRAME=imu` arbeitet also korrekt; ein
  `--transform_right` in der Auswertung wäre falsch.
- **Rotationsfehler 2,42° im Mittel ist echt, aber keine Drift.** Er wächst nicht mit dem
  Delta (RPE 1 m 3,33°, RPE 20 m 3,36°), korreliert aber mit der GT-Drehrate (r = +0,68).
  Der bestmögliche *konstante* körperfeste Offset beträgt nur 0,47° und erklärt 2 % des
  Fehlers – die LiDAR-IMU-Extrinsik ist also nicht schief. Erwartbares Verhalten bei
  schnellen Handdrehungen: weniger Scan-Überlappung, unvollständiger Deskew.
- **RPE über 1 m ist keine Driftrate.** 0,0708 m auf 1 m sind 7,1 %, aber vom
  Rotationsfehler dominiert (1 m · sin 2,4° ≈ 4,2 cm). Dieselbe Trajektorie: 2 m 4,7 %,
  5 m 2,0 %, 10 m 1,6 %, 20 m 1,4 %. Die echte Driftrate liegt bei ~1,4 %.
- **Variantenvergleich (variants_ate.txt, ohne t_offset gerechnet):** `traj_imu.tum` ist mit
  0,1057 m ATE besser als `traj_imu_smoothed.tum` (0,1146 m) und `traj_imu_fused.tum`
  (0,1262 m). Der Ausgabevertrag bleibt damit bei der reinen LiDAR-Odometrie; die
  Smoother-Ausgaben bringen hier keinen Gewinn.
- **Posenzahl 730 statt 740.** Die ersten Scans liefern noch keine Pose (ICP lief 729-mal,
  Initialisierung über PitchAndRollFromIMU).
- **Lokale Karte wurde 112-mal aktualisiert**, die Simplemap enthält 90 Keyframes.
- **Harmlose Log-Warnungen:** fünf Kamera-Topics (`/alphasense/cam0..4`) und `/Point_name`
  (Hilti-Kontrollpunkte) werden nicht verarbeitet – MOLA-LO nutzt sie nicht. `Kein /tf_static`
  ist erwartbar, das Profil setzt die Sensorposen fest. Eine IMU-Warnung
  (`invalid IMU orientation quaternion`) ist für eine Roh-IMU ohne Orientierungsschätzung normal.
- **Dieser Lauf ersetzt einen früheren `run_1`** (ATE 0,0953 m), der am 04.11.2026 um 18:32
  überschrieben wurde. Beide liegen innerhalb der Nichtdeterminismus-Spanne; die alte
  Trajektorie existiert nicht mehr, deshalb nennt die Determinismus-Tabelle in
  `../../../README.md` nur die fünf vorhandenen Läufe.
- **Noch offen (visuelle Prüfung durch Victor):** Zuordnung der ATE-Spitzen (max 0,21 m) zu
  Türen, Treppenhaus und Drehbewegungen. Dafür:
  `evo_ape tum ../../../../../common/gt/exp14_gt.tum traj_imu.tum -a --t_max_diff 0.05 --t_offset -0.05 -p --plot_mode xy`
