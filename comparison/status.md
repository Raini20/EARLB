# Vergleich Exp14 – Stand

Erzeugt 2026-11-27 mit `common/eval/compare.py` auf Commit `8146dea`. **3 von 4 Systemen ausgewertet.**

| System | Person | Läufe gefunden | Stand |
| --- | --- | --- | --- |
| OpenMAVIS | Felix | – | offen: keine traj_imu.tum unter systems/openmavis/results/exp14/run_<n>/ |
| MOLA-LO | Victor | 1, 2, 3, 4 | ausgewertet (run_1, Auswahl: REFERENCE) |
| KISS-SLAM | Merle | 1, 2, 3 | ausgewertet (run_3, Auswahl: höchster Lauf mit voller Abdeckung) |
| SR-LIVO | Rainhard | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 | ausgewertet (run_10, Auswahl: REFERENCE) |

## Hinweise je System

**MOLA-LO**

- Zeitversatz -0.050 s aus t_offset.txt angewendet (Begründung in run.md)

**KISS-SLAM**

- C2C noch nicht gerechnet (common/eval/c2c_scan.py)

## Ergebnisse

Siehe `kpi_table.md`, `overlay_xy.pdf`, `ape_time.pdf`. Fehlende Systeme fehlen dort einfach; nach jedem Merge `compare.py` erneut ausführen.
