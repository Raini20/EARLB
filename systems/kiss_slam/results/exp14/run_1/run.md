# KISS-SLAM – exp14_basement_2.bag

- Datum: 2026-11-27 19:01
- System: kiss-slam 0.0.2 (von PyPI, kein Git-Commit), kiss-icp 1.3.0, map_closures 2.0.2
- Config: config_used.yaml (Kopie von config/kiss_slam_hilti.yaml)
- Laufzeit: 48 s inkl. Visualisierung (Bag-Dauer 74 s)
- Zeitbasis: Bag-Empfangszeit, t_offset 0 s (alle 689 GT-Posen zugeordnet)

## Ergebnis KISS-SLAM

─────────────────────── Results for RosbagDataset Sequence exp14_basement_2 ────────────────────────
+--------------------------+-------+----------+
|                   Metric | Value | Units    |
+==========================+=======+==========+
|        Average Frequency |  37   | Hz       |
|          Average Runtime |  27   | ms       |
| Number of closures found |   0   | closures |
+--------------------------+-------+----------+

## Auffälligkeiten

- map_closures==2.0.2 nötig: ab 2.1.0 fehlt align_map_to_local_ground, --refuse-scans stürzt ab
- keine Loop Closures auf Exp14 (Strecke kehrt nicht an bekannte Orte zurück)
