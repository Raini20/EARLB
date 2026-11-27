# SR-LIVO – Exp14 – Run 6 (Diagnose: ohne visuelles Update)

- Datum: 2026-11-21
- SR-LIVO Commit: `97a26660ca0d3723e1556b447d3b7d34f2866555` + Patches 0001, 0002
- Config: `config_used.yaml` (identisch zu Run 5), Launch: `launch_used.launch`
- Bag-Abspielrate: 0.5, ohne RViz
- Visuelles Pose-Update (VIO): aus (`SRLIVO_NO_VIO=1`, Patch 0002)

## Parameteränderungen gegenüber dem vorherigen Run

| Parameter | alt | neu | Begründung |
| --- | --- | --- | --- |
| `SRLIVO_NO_VIO` | 0 | 1 | Verdacht: VIO-Update (Fisheye als Pinhole, online geschätzte Intrinsik/Extrinsik) verursacht die Divergenz ab 61 s in Run 5 |

## Ergebnisse

- `traj_imu.tum` **byte-identisch zu Run 5** (gleiche MD5), daher identische Kennzahlen (APE RMSE 3.775 m).
- -> Das visuelle Update hat in dieser Konfiguration **keinen Einfluss auf die Trajektorie**; SR-LIVO arbeitet hier
  faktisch als LIO, die Kamera dient nur dem Einfärben. Die Verarbeitung ist bei gleicher Eingabe deterministisch.
- Kamera-Verdacht widerlegt.

## Weitere Analyse der Divergenz bei ~61 s (nach Run 6)

- Geschätzte Geschwindigkeit bis 61 s nahezu gleich GT (57 s: 1.35 vs 1.35 m/s), bei 62 s Sprung 0.63 -> 1.75 m/s
  (GT 0.67 m/s). IMU-Biases bleiben stabil -> abruptes Ereignis, keine schleichende Drift.
- IMU-Drehrate bei 61–62 s 60–69 deg/s, vorher bis 93 deg/s ohne Probleme -> keine extreme Bewegung.
- LiDAR: ab 59 s 73–78 % aller Punkte < 1 m (Median 0.63 m).
- Kamerabilder: enger Treppenaufgang, cam3 sieht nur eine strukturlose Wand direkt neben dem Gerät; keine Tür.
- Träger/Gerät im Sensor-Frame statisch: nur Voxel bei 0.09–0.57 m, fast alle durch `blind: 0.5` entfernt
  -> nicht die Ursache.
- Code: Residuen gehen ohne robuste Kostenfunktion ins IEKF; Ausreißer-Schwelle prüft den **vorzeichenbehafteten**
  Punkt-Ebene-Abstand (`distance < 0.3`) -> beliebig große negative Abstände werden akzeptiert. In enger Geometrie
  (viele Fehlzuordnungen) plausible Ursache -> Run 7 mit Patch 0003 (`|distance| < 0.3`).
- Nebenbefund: Config-Schlüssel `max_dist_to_plane_ct_icp` (aus NTU-Config) wird vom Code nicht gelesen,
  richtig ist `max_dist_to_plane_icp` (Default ebenfalls 0.3, daher bisher ohne Auswirkung). Korrigiert.
