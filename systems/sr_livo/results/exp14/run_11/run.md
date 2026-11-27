# SR-LIVO – Exp14 – Run 11 (Reproduktion auf dem PC)

- Datum: 2026-11-24
- SR-LIVO Commit: `97a26660ca0d3723e1556b447d3b7d34f2866555` + Patches 0001, 0002, 0003 (im Docker-Build angewendet)
- Repo-Commit: `8ce305b` (Image-Build und Lauf)
- Config: `config_used.yaml`, Launch: `launch_used.launch` (identisch zu Run 10)
- Rechner: PC, AMD Ryzen 9 5900X (12 Kerne / 24 Threads), WSL2 ~31 GB RAM. Image frisch gebaut (`BUILD_JOBS=auto` -> `-j12`)
- Daten: frisch von Hugging Face geladen, SHA256 des Bags = Hugging Face
- Bag-Abspielrate: 0.5, ohne RViz
- Visuelles Pose-Update (VIO): an (Standard)
- Laufzeit: 183 s Wanduhr, kein Hänger (`progress.log`), SR-LIVO ~200 % CPU, ~0.90 GB RAM
- Ground Truth: `exp14_basement_2_imu.txt` (Hilti, direkt; `common/gt/` existiert auf diesem Branch nicht)

## Parameteränderungen gegenüber dem vorherigen Run

Keine. Zweck: prüfen, ob ein anderer Rechner mit frisch gebautem Image und frisch geladenen Daten dasselbe
Ergebnis liefert wie Run 10 (Laptop).

## Ergebnisse (evo, SE(3)-Umeyama, ohne Skalierung)

`traj_imu.tum` **byte-identisch zu Run 8, 9 und 10** (MD5 `3c431ef01716bc49dd38e6ffd941100d`), 707 Posen,
letzte bei 73.8 s Bag-Zeit (volle Abdeckung).

| Metrik | RMSE | Mean | Median | Max |
| --- | --- | --- | --- | --- |
| APE trans [m] | 0.0419 | 0.0350 | 0.0296 | 0.1228 |
| RPE trans, 1 m [m] | 0.0441 | 0.0349 | 0.0281 | 0.1583 |
| RPE rot, 1 m [deg] | 1.213 | 1.114 | 1.066 | 2.427 |

Damit ist das Ergebnis rechnerunabhängig reproduzierbar (Laptop Ryzen 7 7735U / PC Ryzen 9 5900X).

## Auffälligkeiten

- Rohkarte `map.pcd`: 1 156 310 Punkte (Run 10: 1 156 241). Wie schon bei Run 9/10: Einfärben/Kartieren der Farbkarte
  ist nicht vollständig deterministisch, die Trajektorie schon.
- VIO-Meldungen im `launch.log` (`Remove_outlier_using_ransac_pnp error` + OpenCV-Ausnahme in
  `cvFindExtrinsicCameraParams2`): 16-mal (Run 10: 14-mal). Ohne Einfluss auf die Trajektorie (byte-identisch), passt
  dazu, dass die Kamera auf Exp14 nur einfärbt (vgl. Run 5/6 mit `SRLIVO_NO_VIO=1`).
- Laufzeit fast gleich wie auf dem Laptop (183 s vs. ~175 s): Bei Rate 0.5 bestimmt die Bag-Dauer die Laufzeit, nicht die CPU.
