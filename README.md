# EAR-Lab: SLAM-Vergleich auf Hilti Exp14

Gruppenprojekt EAR-Lab (Master Robotic Engineering, FH Technikum Wien, WS 2026). Vier SLAM-Systeme laufen auf derselben Sequenz der Hilti SLAM Challenge 2022 (`exp14_basement_2`, 74 s, Treppenhaus → Keller → enge Treppe). Ihre Trajektorien und Karten werden einheitlich gegen die Ground Truth und den Hilti-Laserscan ausgewertet.

| System | Person | Ordner | Branch |
| --- | --- | --- | --- |
| OpenMAVIS | Felix | `systems/openmavis/` | `Felix` |
| MOLA LiDAR Odometry | Victor | `systems/mola_lo/` | `Victor` |
| KISS-SLAM | Merle | `systems/kiss_slam/` | `Merle` |
| SR-LIVO | Rainhard | `systems/sr_livo/` | `Raini` |

**Aktueller Stand:** [`comparison/status.md`](comparison/status.md) (wird von `compare.py` erzeugt).

## Struktur

```text
EARLB/
├─ common/        gemeinsam für alle: GT, Kalibrierung, Auswerteskripte  → common/README.md
├─ systems/<s>/   je System: Installation (README, Dockerfile), Config, Ergebnisse results/exp14/run_<n>/
├─ comparison/    Gruppenvergleich: KPI-Tabelle, Trajektorien-Overlay, Status (erzeugt, nicht von Hand ändern)
└─ EAR_Paper/     Paper (LaTeX, IEEEtran)
```

Daten (Bag, Laserscan) liegen nicht im Repo. Download: `systems/sr_livo/scripts/download_data.sh [--scan]` lädt Bag, GT, Kalibrierung und optional den Laserscan von Hugging Face nach `~/data/hilti2022`.

## Ablauf

1. Jede Person arbeitet auf dem eigenen Branch nur in `systems/<eigenes System>/` und holt sich `common/` per `git merge main`.
2. Ergebnisse nach dem Ausgabevertrag ablegen und mit `common/eval/evaluate.sh` auswerten (Anleitung: [`common/README.md`](common/README.md)).
3. Pull Request auf `main`, eine zweite Person schaut drüber.
4. Nach jedem Merge `common/eval/compare.py` laufen lassen und `comparison/` committen. Fehlende Systeme blockieren dabei nichts, sie stehen im Status als offen.
