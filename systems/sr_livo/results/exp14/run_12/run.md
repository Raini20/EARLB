# SR-LIVO – Exp14 – Run 12 (Echtzeittest, Rate 1.0, PC)

- Datum: 2026-11-26
- SR-LIVO Commit: `97a26660ca0d3723e1556b447d3b7d34f2866555` + Patches 0001, 0002, 0003 (im Docker-Build angewendet)
- Repo-Commit: `7addb0b`, selbes Image wie Run 11
- Config: `config_used.yaml`, Launch: `launch_used.launch` (identisch zu Run 10/11)
- Rechner: PC, AMD Ryzen 9 5900X (12 Kerne / 24 Threads), WSL2 ~31 GB RAM
- Bag-Abspielrate: **1.0** (Echtzeittest), ohne RViz
- Visuelles Pose-Update (VIO): an (Standard)
- Laufzeit: 108 s Wanduhr, kein Hänger, SR-LIVO bis ~360 % CPU, ~0.90 GB RAM
- Ground Truth: `exp14_basement_2_imu.txt` (Hilti, direkt)

## Parameteränderungen gegenüber dem vorherigen Run

Nur die Abspielrate: 0.5 -> 1.0. Zweck: prüfen, ob SR-LIVO mit den Innenraum-Parametern auf dem PC echtzeitfähig ist
und dabei dieselbe Trajektorie liefert wie die Referenz (Run 10/11).

## Echtzeitfähigkeit

SR-LIVO hält auf dem PC Schritt: Zwischen zwei `progress.log`-Einträgen (~10 s Wanduhr) rückt die Bag-Zeit der
Posen um ~10 s vor. Die letzte Pose (73.8 s) kommt ~9 s nach Bag-Ende, das ist die Wartezeit des Skripts, kein Rückstau.
Auf dem Laptop war Rate 1.0 nicht echtzeitfähig (siehe README, Abschnitt 6).

## Ergebnisse (evo, SE(3)-Umeyama, ohne Skalierung)

`traj_imu.tum` ist **nicht byte-identisch** zu Run 10/11 (MD5 `480efb1cd8a3d94d358607b52227d09a` statt `3c431ef0…`).
707 Posen, gleiche Zeitstempel, letzte bei 73.8 s (volle Abdeckung).

| Metrik | RMSE | Mean | Median | Max |
| --- | --- | --- | --- | --- |
| APE trans [m] | 0.0388 | 0.0317 | 0.0277 | 0.1251 |
| RPE trans, 1 m [m] | 0.0436 | 0.0345 | 0.0277 | 0.1583 |
| RPE rot, 1 m [deg] | 1.201 | 1.096 | 0.965 | 2.422 |

Zum Vergleich Run 10/11 (Rate 0.5): APE RMSE 0.0419 m, RPE 0.0441 m / 1.213°. Der Unterschied (3 mm ATE) liegt weit
unter der GT-Genauigkeit (1–2 cm) und ist keine Verbesserung, sondern Streuung.

### Abweichung Run 12 gegenüber Run 10 (Positionsdifferenz je Pose)

| Bag-Zeit | Mittel | Max |
| --- | --- | --- |
| 3–10 s | 0.00 mm | 0.00 mm |
| 10–30 s | 0.40 mm | 1.19 mm |
| 30–50 s | 0.65 mm | 1.81 mm |
| 50–59 s | 3.61 mm | 15.4 mm |
| 59–66 s (enger Treppenaufgang) | 25.2 mm | 48.9 mm |
| 66–74 s (Stillstand) | 47.0 mm | 75.7 mm |

Die erste Abweichung liegt bei 3.4 s im µm-Bereich. Sie wächst langsam und verstärkt sich im engen Treppenaufgang, wo
wenige, nahe Punkte die Schätzung schlecht bedingen. Ab 66 s bleibt sie als Versatz stehen.

## Auffälligkeiten / Bewertung

- Ursache: zunächst zufälliges Timing der asynchronen Callbacks vermutet. **Widerlegt durch Run 13:** Die Wiederholung
  mit Rate 1.0 ist byte-identisch zu Run 12. Die Abweichung hängt also reproduzierbar von der Abspielrate ab, nicht vom
  Zufall. Der Mechanismus ist nicht untersucht.
- VIO-Meldungen (`Remove_outlier_using_ransac_pnp error`): 22-mal (Run 10: 14, Run 11: 16).
- Rohkarte `map.pcd`: 1 156 285 Punkte (Run 11: 1 156 310).
- **Laut Gruppenregel ist Run 12 nicht gleichwertig zur Referenz** (MD5 verschieden). Referenz bleibt Run 10 (Rate 0.5).
  Run 12 zeigt aber: SR-LIVO ist auf dem PC echtzeitfähig, und die Genauigkeit ändert sich bei Rate 1.0 nicht messbar.
