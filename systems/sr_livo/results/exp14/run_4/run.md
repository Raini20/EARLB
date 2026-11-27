# SR-LIVO – Exp14 – Run 4

- Datum: 2026-11-21
- SR-LIVO Commit: `97a26660ca0d3723e1556b447d3b7d34f2866555` + `patches/0001-robo-absolute-timestamp.patch`
- Repo-Commit: `d3857e7`
- Config: `config_used.yaml`, Launch: `launch_used.launch`
- Bag-Abspielrate: 1.0, ohne RViz
- Laufzeit (Wanduhr): 106 s
- Rechner: Laptop (16 Threads, WSL2 mit 6,6 GB RAM)

## Parameteränderungen gegenüber dem vorherigen Run

| Parameter | alt | neu | Begründung |
| --- | --- | --- | --- |
| `odometry_options/init_voxel_size` | 0.2 (Default) | 0.1 | mehr Punkte pro Frame im engen Treppenhaus |
| `odometry_options/init_sample_voxel_size` | 1.0 (Default) | 0.5 | mehr Keypoints in der Initialisierung |
| `odometry_options/sample_voxel_size` | 1.5 | 0.5 | mehr Keypoints (Innenraum statt NTU-Campus) |
| `odometry_options/min_distance_points` | 0.15 | 0.05 | dichtere Karte |
| `icp_options/size_voxel_map` | 1.0 | 0.5 | feinere Nachbarschaftssuche |

Vorab getestet über die ersten 30 s: 0 ICP-Fehlschläge, Positionen ~10 cm an der GT.

## Ergebnisse

Unvollständig – nicht mit evo ausgewertet.

- 0 ICP-Fehlschläge, 468 Posen, Karte 15.8 MB.
- Nur Bag-Zeit 3.2–49.9 s verarbeitet: mit den dichteren Parametern **nicht mehr echtzeitfähig** auf dem Laptop.
  Das Skript hat SR-LIVO 3 s nach Bag-Ende beendet.
- -> `run_exp14.sh` wartet jetzt, bis `pose.txt` nicht mehr wächst; Run 5 mit Rate 0.5.
