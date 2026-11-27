# SR-LIVO – Exp14 – Run 1

- Datum: 2026-11-21
- SR-LIVO Commit: `97a26660ca0d3723e1556b447d3b7d34f2866555` + `patches/0001-robo-absolute-timestamp.patch`
- Config: `config_used.yaml`
- Bag-Abspielrate: 1.0, mit RViz
- Laufzeit (Wanduhr, inkl. Start/Ende): 108 s
- Rechner: Laptop (16 Threads, WSL2 mit 6,6 GB RAM)

## Parameteränderungen gegenüber dem vorherigen Run

Erster Lauf mit Patch. Vorher (ohne Patch, nicht gespeichert) wurden ab dem zweiten LiDAR-Scan alle Punkte
verworfen, weil SR-LIVO für `lidar_type: 4` relative Punktzeiten erwartet, Hesai aber absolute Unix-Zeiten
liefert (`last_end_time` lag ~50 Jahre in der Zukunft). Keine Initialisierung, keine `pose.txt`.

## Ergebnisse

Ungültig – nicht mit evo ausgewertet.

- IMU-Initialisierung erfolgreich (`init_gravity = 0.176 0.167 -9.807`).
- 1425 Posen mit 40 Hz (= Kamerarate), aber nur Bag-Zeit 3–39 s von 74 s verarbeitet (langsamer als Echtzeit).
- Stetig wachsende Drift: Geschwindigkeit 0.9 m/s (7 s) -> 7.4 m/s (37 s), letzte Pose z = 102 m.
  GT: max. 1.7 m/s, 38 m Gesamtweg. Muster einer reinen IMU-Integration.
- `map.pcd` fast leer (12 KB).

## Auffälligkeiten

- `Failed to find match for field 'intensity'` pro Scan (erwartet, Intensität float32 statt uint8, irrelevant).
- Gelegentlich `Remove_outlier_using_ransac_pnp error` (visueller Teil).
- ICP-Fehler werden bei `debug_print: false` nicht ausgegeben -> Run 2 zur Diagnose.
