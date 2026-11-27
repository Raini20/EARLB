# SR-LIVO – Exp14 – Run 8 (erstes gültiges Ergebnis)

- Datum: 2026-11-22
- SR-LIVO Commit: `97a26660ca0d3723e1556b447d3b7d34f2866555` + Patches 0001, 0002, 0003
  (0003 im Container nachträglich angewendet und inkrementell gebaut; Image-Neubau scheiterte an pip-Download-Timeout)
- Repo-Commit: `d6d1808` (Config, Launch, Patches)
- Config: `config_used.yaml`, Launch: `launch_used.launch`
- Bag-Abspielrate: 0.5, ohne RViz
- Visuelles Pose-Update (VIO): an (Standard)
- Ground Truth: `exp14_basement_2_imu.txt` (Hilti, direkt), 657 von 689 GT-Posen zugeordnet (`--t_max_diff 0.05`)

## Parameteränderungen gegenüber Run 5 (letzter vollständiger Lauf ohne Patch 0003)

| Änderung | alt | neu | Begründung |
| --- | --- | --- | --- |
| Patch 0003, `optimize.cpp` | `distance < 0.3` | `|distance| < 0.3` | Ausreißer-Schwelle wirkte nur einseitig, Divergenz ab 61 s (Run 5/6) |
| `icp_options/max_dist_to_plane_icp` | (falscher Schlüssel `..._ct_icp`, Default 0.3) | 0.3 | nur Korrektur des Namens |

## Ergebnisse (evo, SE(3)-Umeyama, ohne Skalierung)

| Metrik | RMSE | Mean | Median | Max |
| --- | --- | --- | --- | --- |
| APE trans [m] | 0.0419 | 0.0350 | 0.0296 | 0.1228 |
| RPE trans, 1 m [m] | 0.0441 | 0.0349 | 0.0281 | 0.1583 |
| RPE rot, 1 m [deg] | 1.213 | 1.114 | 1.066 | 2.427 |

- 707 Posen (10 Hz), Bag-Zeit 3.2–73.8 s, 0 ICP-Fehlschläge.
- Weglänge SR-LIVO 38.3 m vs. GT 37.8 m (Run 5: 68.0 m).
- Fehler je Abschnitt (Ausrichtung über alles): 0–20 s Mittel 4.8 cm (Max 12.3), 20–55 s 2.2 cm,
  55–61 s 3.4 cm, **61–70 s (enger Treppenaufgang) 5.7 cm (Max 10.4)**, 70–74 s 4.0 cm.
  *Nachtrag:* Das Fenster 61–70 s war grob gewählt und enthält ab 66 s Stillstand. Der enge Treppenaufgang ist
  ab Run 10 als 59–66 s festgelegt (GT-Höhe + LiDAR-Nahbereich), dort 4.5 cm Mittel, Max 7.2 cm (siehe Run 10).

## Auffälligkeiten

- Die Divergenz aus Run 5 (bis 14.8 m) ist mit Patch 0003 vollständig behoben.
- `progress.log` hier unbrauchbar (Logging-Fehler im Skript, inzwischen behoben).
- Reproduziert in Run 9 (byte-identische Trajektorie).
