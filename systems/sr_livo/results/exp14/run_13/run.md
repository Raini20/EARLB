# SR-LIVO – Exp14 – Run 13 (Wiederholung Echtzeittest, Rate 1.0, PC)

- Datum: 2026-11-26
- SR-LIVO Commit: `97a26660ca0d3723e1556b447d3b7d34f2866555` + Patches 0001, 0002, 0003 (im Docker-Build angewendet)
- Repo-Commit: `2caa741`, selbes Image wie Run 11/12
- Config: `config_used.yaml`, Launch: `launch_used.launch` (identisch zu Run 10–12)
- Rechner: PC, AMD Ryzen 9 5900X (12 Kerne / 24 Threads), WSL2 ~31 GB RAM
- Bag-Abspielrate: **1.0**, ohne RViz
- Visuelles Pose-Update (VIO): an (Standard)
- Laufzeit: 107 s Wanduhr, kein Hänger, echtzeitfähig wie Run 12
- Ground Truth: `exp14_basement_2_imu.txt` (Hilti, direkt)

## Parameteränderungen gegenüber dem vorherigen Run

Keine. Zweck: prüfen, ob die Abweichung von Run 12 zur Referenz zufällig ist (schwankt von Lauf zu Lauf) oder
reproduzierbar von der Abspielrate abhängt.

## Ergebnisse (evo, SE(3)-Umeyama, ohne Skalierung)

`traj_imu.tum` **byte-identisch zu Run 12** (MD5 `480efb1cd8a3d94d358607b52227d09a`), damit wie Run 12 verschieden von
Run 10/11 (`3c431ef0…`). 707 Posen, letzte bei 73.8 s (volle Abdeckung). Kennzahlen identisch zu Run 12:

| Metrik | RMSE | Mean | Median | Max |
| --- | --- | --- | --- | --- |
| APE trans [m] | 0.0388 | 0.0317 | 0.0277 | 0.1251 |
| RPE trans, 1 m [m] | 0.0436 | 0.0345 | 0.0277 | 0.1583 |
| RPE rot, 1 m [deg] | 1.201 | 1.096 | 0.965 | 2.422 |

## Bewertung

- SR-LIVO ist auch bei Rate 1.0 deterministisch: zwei Läufe, gleiche Trajektorie. Die Abweichung zur Referenz ist also
  **kein Zufall**, sondern hängt reproduzierbar von der Abspielrate ab (Rate 0.5: `3c431ef0…`, Run 8–11; Rate 1.0:
  `480efb1c…`, Run 12/13). Welcher Mechanismus das bewirkt, ist nicht untersucht.
- Laut Gruppenregel bleibt Rate 1.0 nicht gleichwertig zur Referenz (MD5 verschieden), Referenz bleibt Run 10.
  Genauigkeit unverändert (ATE RMSE 3.9 vs. 4.2 cm, unter der GT-Genauigkeit).
- Nicht deterministisch bleibt nur die Farbkarte: `map.pcd` 1 156 322 Punkte (Run 12: 1 156 285),
  VIO-Meldungen (`Remove_outlier_using_ransac_pnp error`) 19-mal (Run 12: 22).
