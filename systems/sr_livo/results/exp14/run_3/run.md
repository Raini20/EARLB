# SR-LIVO – Exp14 – Run 3

- Datum: 2026-11-21
- SR-LIVO Commit: `97a26660ca0d3723e1556b447d3b7d34f2866555` + `patches/0001-robo-absolute-timestamp.patch`
- Config: `config_used.yaml`
- Bag-Abspielrate: 1.0, ohne RViz
- Rechner: Laptop (16 Threads, WSL2 mit 6,6 GB RAM)

## Parameteränderungen gegenüber dem vorherigen Run

| Parameter | alt | neu | Begründung |
| --- | --- | --- | --- |
| `common/image_topic` | `/alphasense/cam0/image_raw` (40 Hz) | `/alphasense/cam0/image_10hz` (Launch: `topic_tools/drop 3 4`) | Ein Frame = LiDAR-Punkte zwischen zwei Bildern; bei 40 Hz nur 90°-Sektor ohne Überlapp zur Karte (Run 2) |
| Abspielrate | 0.5 | 1.0 | Echtzeit prüfen |

## Ergebnisse

Ungültig – nicht mit evo ausgewertet.

- 701 Posen (10 Hz) über die volle Sequenz -> mit 10-Hz-Frames echtzeitfähig.
- **ICP scheitert weiterhin in 684 von 701 Frames** (662 x 0 Residuen, sonst 12–18).
- Drift wie in Run 1, am Ende > 3 km Abweichung.

## Ursache (Debug-Lauf mit `debug_output`, 10 s)

- Frames im Stillstand liegen mit 5.8 cm Median-NN-Abstand aufeinander -> Extrinsik/Transformationen korrekt.
- Treppenhaus ~4 x 9 x 3 m, Median-Punktabstand 2.7 m, ~670 Punkte/Frame nach 0.2-m-Voxelfilter.
- NTU-Parameter (draußen): Keypoint-Raster 1.0/1.5 m, Karten-Voxel 1.0 m -> nur wenige Dutzend Keypoints,
  ICP verlangt >= 20 Residuen -> scheitert. -> Run 4: Innenraum-Parameter.
