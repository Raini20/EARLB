# Vergleich Exp14 – Stand

Erzeugt 2026-11-27 mit `common/eval/compare.py` auf Commit `a8e8b14`. **2 von 4 Systemen ausgewertet.**

| System | Person | Läufe gefunden | Stand |
| --- | --- | --- | --- |
| OpenMAVIS | Felix | – | offen: keine traj_imu.tum unter systems/openmavis/results/exp14/run_<n>/ |
| MOLA-LO | Victor | 1, 2, 3, 4 | ausgewertet (run_1, Auswahl: REFERENCE) |
| KISS-SLAM | Merle | – | offen: keine traj_imu.tum unter systems/kiss_slam/results/exp14/run_<n>/ |
| SR-LIVO | Rainhard | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 | ausgewertet (run_10, Auswahl: REFERENCE) |

## Hinweise je System

**MOLA-LO**

- Zeitversatz -0.050 s aus t_offset.txt angewendet (Begründung in run.md)

## Ergebnisse

Siehe `kpi_table.md`, `overlay_xy.pdf`, `ape_time.pdf`. Fehlende Systeme fehlen dort einfach; nach jedem Merge `compare.py` erneut ausführen.
