# SR-LIVO – Exp14 – Run 5

- Datum: 2026-11-21
- SR-LIVO Commit: `97a26660ca0d3723e1556b447d3b7d34f2866555` + `patches/0001-robo-absolute-timestamp.patch`
- Config: `config_used.yaml` (identisch zu Run 4), Launch: `launch_used.launch`
- Bag-Abspielrate: 0.5, ohne RViz
- Laufzeit (Wanduhr, inkl. Start/Ende/Nachlauf): 184 s
- Rechner: Laptop (16 Threads, WSL2 mit 6,6 GB RAM)
- Ground Truth: `exp14_basement_2_imu.txt` (Hilti, direkt), 657 von 689 GT-Posen zugeordnet (`--t_max_diff 0.05`)

## Parameteränderungen gegenüber dem vorherigen Run

| Parameter | alt | neu | Begründung |
| --- | --- | --- | --- |
| Abspielrate | 1.0 | 0.5 | Run 4 nicht echtzeitfähig |
| `run_exp14.sh` | fest 3 s Nachlauf | wartet, bis `pose.txt` 10 s stabil | vollständige Verarbeitung |

## Ergebnisse (evo, SE(3)-Umeyama, ohne Skalierung)

| Metrik | RMSE | Mean | Median | Max |
| --- | --- | --- | --- | --- |
| APE trans [m] | 3.775 | 2.363 | 1.186 | 13.456 |
| RPE trans, 1 m [m] | 0.782 | 0.545 | 0.111 | 1.502 |
| RPE rot, 1 m [deg] | 3.014 | 2.229 | 1.279 | 10.032 |

- 707 Posen (10 Hz), Bag-Zeit 3.2–73.8 s, 0 ICP-Fehlschläge, Karte 18.8 MB.
- Weglänge SR-LIVO 68.0 m vs. GT 37.8 m.

## Auffälligkeiten

- **Bis 61 s sehr genau:** bei Ausrichtung auf 0–25 s bleibt der Fehler bis 61 s <= 0.11 m
  (Treppenhaus + Keller, ~33 m Weg).
- **Ab ~61–65 s Divergenz:** Fehler 4.6 m (65 s) -> 14.8 m (73 s). GT bewegt sich in den letzten 10 s
  praktisch nicht (0.0 m), SR-LIVO „fährt“ 8.7 m weiter. Die ATE wird fast vollständig von diesem Abschnitt bestimmt.
- Ursache noch offen (Kandidaten: Türdurchgang / degenerierte Geometrie, Person nahe am Sensor,
  visuelles Update mit Fisheye-Bildern im Pinhole-Modell).
