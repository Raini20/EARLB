# SR-LIVO – Exp14 – Run 9 (Reproduktion von Run 8)

- Datum: 2026-11-22
- SR-LIVO Commit: `97a26660ca0d3723e1556b447d3b7d34f2866555` + Patches 0001, 0002, 0003 (0003 wie in Run 8 im Container)
- Repo-Commit: `f40c7be` (Lauf-Skript mit Watchdog)
- Config/Launch: identisch zu Run 8
- Bag-Abspielrate: 0.5, ohne RViz
- Visuelles Pose-Update (VIO): an (Standard)
- Laufzeit (Wanduhr): ~180 s, SR-LIVO hält bei 0.5x mit dem Bag Schritt (CPU ~200–230 %, RSS ~0.9 GB), siehe `progress.log`

## Parameteränderungen gegenüber dem vorherigen Run

Keine (Reproduktionstest). Nur das Lauf-Skript hat jetzt einen Watchdog (Neustart bei > 60 s ohne neue Posen).

## Ergebnisse

- `traj_imu.tum` **byte-identisch zu Run 8** (MD5 `3c431ef0…`), daher identische Kennzahlen:
  APE RMSE 0.0419 m, Mean 0.0350 m, Median 0.0296 m, Max 0.1228 m;
  RPE 1 m trans RMSE 0.0441 m, rot RMSE 1.213 deg.
- Watchdog: kein Hänger. Abdeckung 3.2–73.8 s.
- Karte `map.pcd` 18.5 MB (nicht im Repo).

## Auffälligkeiten

- Ergebnis reproduzierbar; die Verarbeitung ist bei gleicher Eingabe deterministisch (wie Run 5/6).
- Der sporadische Hänger aus Run 7 trat nicht auf.
