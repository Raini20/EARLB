# SR-LIVO – Exp14 – Run 2 (Diagnose)

- Datum: 2026-11-21
- SR-LIVO Commit: `97a26660ca0d3723e1556b447d3b7d34f2866555` + `patches/0001-robo-absolute-timestamp.patch`
- Config: `config_used.yaml`
- Bag-Abspielrate: 0.5, ohne RViz
- Rechner: Laptop (16 Threads, WSL2 mit 6,6 GB RAM)

## Parameteränderungen gegenüber dem vorherigen Run

| Parameter | alt | neu | Begründung |
| --- | --- | --- | --- |
| `icp_options/debug_print` | false | true | ICP-Fehlschläge sichtbar machen (Verdacht aus Run 1: LiDAR korrigiert nicht) |
| Abspielrate | 1.0 | 0.5 | Rechenzeit als Ursache ausschließen (Run 1 hing hinterher) |

## Ergebnisse

Ungültig – nicht mit evo ausgewertet.

- 2819 Posen über die volle Sequenz (bei 0.5x kommt SR-LIVO mit).
- **ICP scheitert in 2816 von 2819 Frames**, davon 2584 mit exakt 0 Residuen.

## Ursache

SR-LIVO bildet einen Frame aus den LiDAR-Punkten zwischen zwei Kamerabildern (`getMeasurements`).
Bei 40-Hz-Kamera = 25 ms = 90°-Sektor des rotierenden PandarXT. Frame 0/1 (0–180°) bilden die Karte,
Frame 2 (180–270°) überlappt nicht -> 0 Residuen -> ICP schlägt fehl. Die Karte wächst nur nach erfolgreichem
ICP (`addPointsToMap` nach `return` bei `!success`), daher bleibt sie stehen und SR-LIVO läuft nur auf der IMU.
SR-LIVO ist für Livox (nicht-repetitives Muster, volles FoV in jedem Ausschnitt) und 10–15-Hz-Kameras ausgelegt.

-> Run 3: cam0 per `topic_tools/drop` auf 10 Hz, damit jeder Frame eine volle Umdrehung (100 ms) enthält.
