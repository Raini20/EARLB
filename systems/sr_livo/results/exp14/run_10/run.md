# SR-LIVO – Exp14 – Run 10 (Referenzlauf, sauberes Image)

- Datum: 2026-11-22
- SR-LIVO Commit: `97a26660ca0d3723e1556b447d3b7d34f2866555` + Patches 0001, 0002, 0003 (**alle im Docker-Build angewendet**)
- Repo-Commit: `dfbbb9f` (Image-Build), Skripte für Plot/Karte `4235bfa`
- Config: `config_used.yaml`, Launch: `launch_used.launch` (identisch zu Run 8/9)
- Rechner: Laptop, AMD Ryzen 7 7735U (8 Kerne / 16 Threads), 14 GB RAM, davon WSL2 ~6.6 GB
- Bag-Abspielrate: 0.5, ohne RViz
- Visuelles Pose-Update (VIO): an (Standard)
- Laufzeit: ~175 s Wanduhr, kein Hänger (`progress.log`), SR-LIVO ~200 % CPU, ~0.86 GB RAM
- Ground Truth: `exp14_basement_2_imu.txt` (Hilti, direkt), 657 von 689 GT-Posen zugeordnet

## Parameteränderungen gegenüber dem vorherigen Run

Keine. Zweck: bestätigen, dass ein frisch gebautes Image (`docker build` aus dem Repo) dasselbe Ergebnis liefert
wie Run 8/9, bei denen Patch 0003 nachträglich im Container angewendet wurde.

## Ergebnisse (evo, SE(3)-Umeyama, ohne Skalierung)

`traj_imu.tum` **byte-identisch zu Run 8 und 9** (MD5 `3c431ef0…`).

| Metrik | RMSE | Mean | Median | Max |
| --- | --- | --- | --- | --- |
| APE trans [m] | 0.0419 | 0.0350 | 0.0296 | 0.1228 |
| RPE trans, 1 m [m] | 0.0441 | 0.0349 | 0.0281 | 0.1583 |
| RPE rot, 1 m [deg] | 1.213 | 1.114 | 1.066 | 2.427 |

- Enger Treppenaufgang (59–66 s Bag-Zeit): APE Mittel 4.5 cm, Max 7.2 cm. Abgrenzung: Die GT steigt in diesem Abschnitt um
  2.5 m (Treppe), von 59.5 bis 63.5 s liegen 60–78 % der LiDAR-Punkte < 1 m. Ab 66 s steht das Gerät still (GT-Weg < 0.1 m
  bis zum Ende). Gleicher Bereich wie `NARROW` in `scripts/plot_traj.py`. Das Fenster 61–70 s aus Run 8 gilt nicht mehr.
- Größter Fehler (12.3 cm) bei 6–9 s, also in der Anfangsphase kurz nach der Initialisierung.

## Dateien für Paper und Kartenvergleich

| Datei | Inhalt |
| --- | --- |
| `traj_paper.pdf` / `.png` | Einzel-/Diagnoseabbildung (IEEE-Spaltenbreite, nur SR-LIVO): (a) Draufsicht SR-LIVO vs. GT, (b) APE über die Zeit. Nicht die Paper-Abbildung (die zeigt alle Systeme, siehe README) |
| `map.ply` | Karte, Voxel 5 cm (238 731 Punkte, 3.6 MB), **im selben Weltframe wie `traj_imu.tum`** |
| `T_gt_est.txt` | 4x4-Ausrichtung (Umeyama wie evo): `p_gt = T · p_est`. In CloudCompare auf `map.ply` anwenden, dann C2C zum Hilti-Laserscan (kein ICP als Hauptwert) |
| `map.pcd`, `map_gt_aligned.ply` | Rohkarte bzw. vorab transformierte Karte – nur lokal |

## Auffälligkeiten

- Die Rohkarte unterscheidet sich minimal von Run 9 (1 156 241 statt 1 156 210 Punkte), obwohl die Trajektorie
  identisch ist: das Einfärben/Kartieren für die Farbkarte ist nicht vollständig deterministisch, die Pose schon.
- Kontrolle der Kartenausrichtung (Draufsicht + Seitenansicht mit GT-Trajektorie): Trajektorie verläuft in den
  kartierten Räumen, Treppen bei x ≈ 102 m und 122 m stimmen überein.

## Kartengenauigkeit (C2C zum Laserscan, nachgetragen 2026-11-27, PC)

`scripts/c2c_scan.py`: `map.ply` mit `T_gt_est.txt` ausgerichtet (kein ICP), Abstand jedes Kartenpunkts zum nächsten
Punkt von `sheldonian_full.e57` (volle Auflösung, Header-Pose angewendet). Entspricht CloudCompare C2C ohne lokales
Modell. Ergebnisse in `c2c/`.

| Mittel | Median | RMS | P90 | P95 | < 5 cm | < 10 cm | < 20 cm |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 11,2 cm | 3,3 cm | 30,8 cm | 17,3 cm | 55,2 cm | 66,2 % | 84,4 % | 90,8 % |

Langer Ausläufer (1 646 Punkte > 2 m): 41 % der Punkte > 20 cm liegen im westlichen Keller, wo der Scan ~30-mal
dünner ist (fehlende Referenz). Weitere Punkte direkt an der Trajektorie, vermutlich Personen/Dynamik. Details und
Draufsicht im README (Abschnitt „Kartengenauigkeit“) und in `c2c/c2c_topview.png`.
