# OpenMAVIS – Hilti Exp14

Multi-Kamera-Visual-Inertial-SLAM auf ORB-SLAM3-Basis ([Byson-source/OpenMAVIS](https://github.com/Byson-source/OpenMAVIS), Commit `b13b1c2`). Nutzt 4 der 5 Alphasense-Fisheye-Kameras (cam1 links, cam0 rechts, cam4 seitlich links, cam3 seitlich rechts) und die Alphasense-IMU. Kein LiDAR, daher keine dichte Karte und kein C2C.

## Struktur

```text
systems/openmavis/
├─ .devcontainer/devcontainer.json   VS Code Dev Container (Repo -> /repo, Daten -> /data)
├─ docker/Dockerfile                 ROS Noetic + Pangolin v0.6 + OpenMAVIS (fester Commit)
├─ patches/0001-optional-viewer.patch  OPENMAVIS_VIEWER=0 -> ohne Pangolin-Fenster
├─ config/hilti_exp14.yaml           Kopie der HiltiChallenge2022.yaml, hier ändern
├─ scripts/prepare_data.sh           Bag -> EuRoC + timestamps.txt
├─ scripts/run.sh                    ein Lauf -> results/exp14/run_<n>/ (traj_imu.tum, run.md, ...)
├─ scripts/to_tum.py                 OpenMAVIS-Ausgabe -> traj_imu.tum
├─ scripts/eval.ps1                  Auswertung mit earlb-eval (Windows)
└─ results/exp14/run_<n>/            Ergebnisse nach Ausgabevertrag (common/README.md)
```

## Einrichten (Windows, Docker Desktop mit WSL2)

1. Daten: `exp14_basement_2.bag` nach `EARLB\data\` (per `.gitignore` ausgeschlossen). Die Ground Truth kommt aus `common/gt/exp14_gt.tum`.
2. VS Code: Ordner `systems/openmavis` öffnen → `F1` → „Dev Containers: Reopen in Container“. Der erste Build dauert 15–30 min.

## Ablauf

Im Container-Terminal (`/repo/systems/openmavis`):

```bash
bash scripts/prepare_data.sh                      # einmalig, ~10-30 min, mehrere GB PNGs
bash scripts/run.sh 1                             # mit Pangolin-Fenster
OPENMAVIS_VIEWER=0 bash scripts/run.sh 2          # ohne Fenster
OPENMAVIS_VIEWER=0 bash scripts/run.sh 3
```

Auswerten pro Lauf (PowerShell auf Windows, baut `earlb-eval` beim ersten Mal selbst):

```powershell
.\systems\openmavis\scripts\eval.ps1 1
```

Danach in `run_<n>/run.md` die Werte aus `ape.txt` / `rpe_*.txt` und Auffälligkeiten eintragen. Läufe für den Vergleich in `results/exp14/REFERENCE` (eine Nummer pro Zeile, erste = Referenzlauf):

```text
1
2
3
```

## Frame und Zeit (geprüft im Quellcode)

`multi_inertial_euroc` ruft `SaveTrajectoryEuRoC(filename)` auf (`src/System.cc`, Zeile ~767). Für `IMU_MULTI` schreibt diese Funktion

- die **Pose des IMU-Frames**: `Twb = (mTbc · Tcw)⁻¹`,
- die **Zeit in Sekunden**: der Runner teilt die ns-Zeitstempel beim Einlesen durch 1e9.

`f_raw.txt` ist also schon im Format des Ausgabevertrags. `to_tum.py` entfernt nur die Kopfzeile und prüft die Zeitbasis. **Achtung:** Schritt 2 in `common/README.md` (`$1/1e9`) würde die Zeit ein zweites Mal teilen und muss angepasst werden.

Die Weltkoordinaten beziehen sich auf den ersten Keyframe (gravitationsausgerichtet). Das gleicht die SE(3)-Ausrichtung in evo aus.

## Bekannte Eigenschaften

- **Nicht deterministisch** (wie ORB-SLAM3, Multithreading): 3–5 Läufe, Mittelwert ± Streuung über `REFERENCE`.
- **Mehrere Karten:** Verliert das Tracking die Karte, startet ORB-SLAM3 eine neue. Gespeichert wird nur die größte. `run.md` zeigt die Kartenzahl; bei >1 die Abdeckung prüfen.
- Kamera-Überlappung (`Camera*.overlappingBegin/End`) ist in der Original-Config noch nicht eingestellt („to be updated“).
