# MOLA-LO – Hilti 2022 Exp14 (Victor)

MOLA LiDAR Odometry [Blanco-Claraco 2025, arXiv:2407.20465] auf `exp14_basement_2.bag`
(Hilti-Oxford Dataset [Zhang et al. 2023, arXiv:2208.09825]). Ausgabe nach dem
gemeinsamen Ausgabevertrag: `results/exp14/run_<n>/traj_imu.tum` (+ `map.ply`, `run.md`).

## Eingabedaten (geprüft mit `scripts/bag_info.py`)

| Topic | Typ | Nachrichten | Bemerkung |
|---|---|---|---|
| `/hesai/pandar` | PointCloud2 | 740 (10 Hz) | Frame `PandarXT-32`, Felder x,y,z,intensity,**timestamp (f64, absolut)**,ring; Punktzeit 0–0,1 s nach Header |
| `/alphasense/imu` | Imu | 29 539 (~400 Hz) | Frame `imu_sensor_frame` |
| `/alphasense/cam0..4/image_raw` | Image | je ~2960 | von MOLA-LO nicht genutzt |

- Das Bag ist ein **ROS-1-Bag** (`#ROSBAG V2.0`), Dauer 74,0 s, **kein `/tf`**.
- MOLA-LO liest es direkt über `--input-rosbag1` (Paket `mola_input_rosbag1`); keine Konvertierung nötig.

## Konfiguration

Verwendet wird das offizielle MOLA-LO-Profil `hilti2022` (`mola-lo-cli-hilti2022`, ab MOLA-LO 3.3.0):

- `base_link` = IMU-Frame „I“ → Trajektorie liegt direkt im GT-Frame, kein Nachrechnen mit `--transform_right`.
- Feste LiDAR-Pose (`MOLA_USE_FIXED_LIDAR_POSE=1`) aus der Hilti-Kalibrierung `lidar_calibration.yaml`:
  t = (−0,001; −0,00855; 0,055) m, q(x,y,z,w) = (0,7071; −0,7071; 0; 0) ≙ yaw −90°, pitch 0°, roll 180°.
- Deskew mit IMU (`MotionCompensationMethod::IMU`), Pitch/Roll-Initialisierung aus IMU,
  State Estimator `mola_state_estimation_smoother`, erste Pose fixiert (`MOLA_LINK_FIRST_POSE_SIGMA=1e-6`).
- ICP-Pipeline: `lidar3d-default.yaml` (Standard).

Die Extrinsik ist die Hilti-Kalibrierung `lidar_calibration.yaml` (Eintrag `PandarXT-32`),
also die Inverse von `common/calib/T_lidar_imu.json`. Weil MOLA-LO direkt IMU-Posen
ausgibt, braucht es diese Datei nicht.

## Ausführung

Gemeinsame Voraussetzung: das Bag lokal, z. B. per `systems/sr_livo/scripts/download_data.sh`
(lädt nach `~/data/hilti2022`). `run_exp14.sh` nimmt den Bag-Pfad als Argument; die Befehle
unten gehen von `data/exp14_basement_2.bag` im Repo aus (per `.gitignore` ausgeschlossen).

### Nativ unter Linux (verwendet für die Ergebnisse im Paper)

Ubuntu 24.04 „noble“ + ROS 2 Jazzy. Der Wrapper `mola-lo-cli-hilti2022` ist ab
MOLA-LO 3.3.0 im Binärpaket enthalten; das Jazzy-Repo liefert genau 3.3.0.

```bash
sudo apt update && sudo apt install -y \
  ros-jazzy-mola-lidar-odometry \
  ros-jazzy-mola-metric-maps \
  ros-jazzy-mola-input-rosbag1 \
  ros-jazzy-mp2p-icp \
  ros-jazzy-mola-state-estimation \
  ros-jazzy-mola-traj-tools

source /opt/ros/jazzy/setup.bash
which mola-lo-cli-hilti2022      # muss gefunden werden

# evo separat, nicht in die System-Python-Installation (Ubuntu 24.04 ist extern verwaltet):
conda create -n evo python=3.12 && conda activate evo && pip install evo
# oder venv: python3 -m venv ~/.venvs/evo && ~/.venvs/evo/bin/pip install evo

# Lauf (aus dem Repo-Root)
bash systems/mola_lo/scripts/run_exp14.sh data/exp14_basement_2.bag run_1
```

Die KPIs in diesem Repo sind mit **evo 1.31.1** gerechnet, derselben Version wie im
gemeinsamen Auswerte-Image `earlb-eval` (`common/eval/Dockerfile`). Andere evo-Versionen
liefern dieselbe ATE, aber eine leicht andere RPE (evo 1.38.1: 7,02 statt 7,08 cm) –
für den Gruppenvergleich also immer das Image oder evo 1.31.1 nehmen.
`run_exp14.sh` findet `evo_*` auch dann, wenn es nur in `~/miniconda3/envs/evo/bin`,
`~/.venvs/evo/bin` oder `~/.local/bin` liegt und nicht auf dem `PATH` ist.
**`common/eval/evaluate.sh` und `compare.py` tun das nicht** – dort vorher
`conda activate evo` oder das Image `earlb-eval` nehmen (siehe `common/README.md`).

**`ros-jazzy-mola-metric-maps` ist zwingend**, obwohl `ros-jazzy-mola-lidar-odometry` es
nicht als apt-Abhängigkeit zieht: die ICP-Pipeline lädt `libmola_metric_maps.so` erst zur
Laufzeit per YAML. Fehlt sie, bricht MOLA-LO nicht ab, sondern verwirft jeden Scan
(`Discarding incoming observations: a fatal error ocurred above`), beendet sich trotzdem
mit Status 0 und schreibt eine leere Trajektorie. `run_exp14.sh` prüft die Bibliothek
daher vorab und kontrolliert nach dem Lauf Log und Posenzahl.

### Docker (Fallback und Reproduzierbarkeits-Check)

≥ 8 GB RAM für Docker empfohlen, Windows: Docker Desktop mit WSL2-Backend.
Das Image installiert `evo` und `rosbags` in ein venv unter `/opt/evo` (auf dem `PATH`).
`pip3 install --break-system-packages` funktioniert hier **nicht**: evo zieht ein neueres
numpy, und das von Debian gelieferte numpy 1.26.4 hat keine `RECORD`-Datei, lässt sich von
pip also nicht deinstallieren – der Build bricht mit
`Cannot uninstall numpy 1.26.4, RECORD file not found` ab.
`run_docker.sh` hängt `-it` nur an, wenn wirklich ein Terminal dranhängt, und startet den
Container als aufrufender Benutzer (`-u $(id -u):$(id -g)`, `HOME=/tmp`), damit die
Ergebnisse in `results/` nicht dem root des Hosts gehören.

```powershell
# aus systems/mola_lo
./run_docker.sh ../../data/exp14_basement_2.bag run_docker
```

### Live zusehen

Zum Zusehen gibt es `mola-lo-gui-hilti2022` – dasselbe Profil, aber über `mola-cli` mit
3D-Ansicht (`mola_viz`): aufgebaute Karte, aktueller Scan, Trajektorie, Zeiten pro Scan.

```bash
source /opt/ros/jazzy/setup.bash
mola-lo-gui-hilti2022 data/exp14_basement_2.bag
```

Die GUI-Variante **erzeugt keine Vertragsdateien**: `mola-cli` kennt die
`--output-tum-path`-Flags von `mola-lidar-odometry-cli` nicht. Sie ist zum Hinsehen und
Debuggen da; die Ergebnisse kommen weiter aus `run_exp14.sh`.

Nach dem Lauf die Draufsicht Schätzung gegen GT: `common/eval/evaluate.sh` legt sie als
`traj_xy.pdf` in den Run-Ordner (Sichtprüfung aus Schritt 1 der Gruppen-Doku).

```bash
T_OFFSET=-0.05 bash common/eval/evaluate.sh mola_lo 1     # Run-Nummer, nicht "run_1"
```

### Was `scripts/run_exp14.sh` tut

1. `mola-lo-cli-hilti2022 <bag> --output-tum-path traj_imu.tum
   --output-tum-path-fused traj_imu_fused.tum --output-tum-path-smoothed traj_imu_smoothed.tum
   --output-simplemap map.simplemap`
2. rendert `config/sm2mm_exp14.yaml` nach `sm2mm_exp14.rendered.yaml` (sm2mm ist ein reines
   mp2p_icp-CLI und kennt die `${VAR|default}`-Substitution von mola_yaml nicht), dann
   `sm2mm` → `mm2ply -b --export-fields x,y,z,intensity` → `map.ply`,
   Weltframe = Trajektorie, Voxel `SM2MM_VOXEL_SIZE` (Default 0,05 m)
3. schreibt `run.md` (Version, Parameter, Laufzeit, Posenanzahl, Kartengröße); eine
   vorhandene `run.md` wird vorher als `run.md.bak.<Zeit>` gesichert
4. legt `t_offset.txt` mit `-0.05` an, falls sie fehlt (Begründung in `run_1/run.md`), und
   ruft das gemeinsame `common/eval/evaluate.sh` mit diesem Versatz auf → `ape.zip`,
   `rpe_*.zip`, `evo_traj.txt`, `ape.txt`, `rpe_*.txt`, `traj_xy.pdf`.
   Dazu vergleicht es die drei Trajektorien-Varianten in `variants_ate.txt` (ohne Versatz).

### Trajektorien-Varianten

Das Profil `hilti2022` nutzt den State Estimator `mola_state_estimation_smoother`. Die CLI kann
daraus drei Trajektorien schreiben – alle im selben Frame (`base_link` = IMU), alle aus **einem** Lauf:

| Datei | Flag | Inhalt |
|---|---|---|
| `traj_imu.tum` | `--output-tum-path` | registrierte Posen der LiDAR-Odometrie selbst; der Smoother wirkt nur über den Motion Prior |
| `traj_imu_fused.tum` | `--output-tum-path-fused` | fusionierte Schätzung des State Estimators, je verarbeitetem Scan |
| `traj_imu_smoothed.tum` | `--output-tum-path-smoothed` | Keyframe-Posen beim Verlassen des Optimierungsfensters, d. h. ihr Endwert (braucht `MOLA_SMOOTHER_KEEP_TRAJECTORY=true`, setzt das Skript) |

`traj_imu.tum` bleibt die Datei des Ausgabevertrags. `variants_ate.txt` belegt, wie groß der
Unterschied auf Exp14 tatsächlich ist; die Wahl für das Paper wird in `run.md` begründet.

## Determinismus und Reproduzierbarkeit

MOLA-LO parallelisiert die Registrierung und ist **nicht bitweise reproduzierbar**. Vier
native Läufe plus ein Lauf im Docker-Image, alle mit identischer Konfiguration auf derselben
Maschine (AMD Ryzen AI 9 365, Ubuntu 24.04.4, ROS 2 Jazzy), ausgewertet mit den
Gruppenparametern, `common/eval/evaluate.sh`, evo 1.31.1 und `t_offset = -0.05`:

| Lauf | ATE RMSE | ATE mean | RPE 1 m trans | RPE 1 m rot | zugeordnet | Laufzeit |
|---|---|---|---|---|---|---|
| `run_1` (Ausgabevertrag) | 0,1002 m | 0,0877 m | 0,0708 m | 3,348° | 680/689 | 35 s |
| `run_2` | 0,0968 m | 0,0859 m | 0,0717 m | 3,402° | 680/689 | 44 s |
| `run_3` | 0,0983 m | 0,0869 m | 0,0706 m | 3,347° | 680/689 | 43 s |
| `run_4` | 0,0991 m | 0,0900 m | 0,0720 m | 3,345° | 680/689 | 46 s |
| `run_docker` | 0,0985 m | 0,0877 m | 0,0676 m | 3,349° | 680/689 | — |

- **Aggregiert stabil:** ATE RMSE = 0,0986 ± 0,0013 m über alle fünf Läufe, Spanne 3,5 mm.
  Die Posenzahl (730) und die Zeitstempel sind in jedem Lauf identisch.
- **Einzelposen wandern:** über alle zehn Lauf-Paare beträgt die Positionsdifferenz bei
  gleichem Zeitstempel im Mittel 41 mm, 95-%-Quantil 99 mm, max 127 mm; die
  Rotationsdifferenz im Mittel 0,08–0,32°. Das ist dieselbe Größenordnung wie der ATE
  selbst. Dabei liegen einzelne Paare sehr dicht (`run_1`/`run_3` 8 mm,
  `run_2`/`run_docker` 11 mm) und andere weit auseinander (`run_3`/`run_4` 73 mm) – der
  Nichtdeterminismus tritt also schubweise auf, passend zu Thread-Scheduling.
- **Konsequenz für den Vergleich:** Streuung zwischen Läufen (±~4 cm je Pose) und
  GT-Genauigkeit (1–2 cm) zusammen setzen die Auflösung, ab der eine Rangfolge der vier
  Systeme sinnvoll ist, auf etwa **5 cm** – nicht auf die Millimeter, mit denen evo rechnet.
- **Docker reproduziert nativ:** der Containerlauf liegt mit 0,0985 m innerhalb der nativen
  Spanne (0,0968–0,1002 m); die Posen weichen von `run_1` im Mittel um 43 mm ab, also
  genauso viel wie zwei native Läufe untereinander. Das Image ist damit als
  Reproduzierbarkeits-Nachweis geprüft, nicht nur gebaut.
- Ein früherer `run_1` mit ATE 0,0953 m wurde am 04.11.2026 um 18:32 durch einen erneuten
  Lauf überschrieben. Die Tabelle nennt nur Läufe, deren Dateien auch im Repo liegen.

Nur `run_1` liefert die Karte ins Repo. Die Karten der Wiederholungsläufe sind per
`.gitignore` ausgeschlossen – sie belegen nichts, kosten aber je ~15 MB.

## Ausgaben

`run_1` ist der Lauf des Ausgabevertrags und Referenzlauf im Gruppenvergleich.
`results/exp14/REFERENCE` nennt `1 2 3 4`: `common/eval/compare.py` nimmt die erste Zeile als
Referenz und gibt über alle vier nativen Läufe zusätzlich Mittelwert ± Streuung der ATE an
(MOLA-LO ist nicht deterministisch, siehe oben). `run_docker` hat keine Nummer und wird von
`compare.py` nicht gezählt; er belegt nur die Determinismus-Tabelle.

```
results/exp14/run_1/              der Lauf des Ausgabevertrags
  traj_imu.tum                    t x y z qx qy qz qw (Unix-Sekunden, IMU-Frame)
  ape.zip rpe_trans.zip rpe_rot.zip   KPIs, Eingang fuer evo_res
  run.md                          Laufprotokoll inkl. KPI-Tabelle und Auffälligkeiten
  map.ply                         Karte für CloudCompare (5-cm-Voxel, x,y,z,intensity)
  t_offset.txt                    Zeitversatz für evo (-0.05 s)
  evo_traj.txt ape.txt rpe_*.txt  Terminalausgabe von evaluate.sh (680 von 689 GT-Posen)
  traj_xy.pdf                     Draufsicht gegen GT aus evaluate.sh
  traj_imu_fused.tum              Variantenvergleich: Begründung der Wahl von
  traj_imu_smoothed.tum           traj_imu.tum, Zahlen in variants_ate.txt
  variants_ate.txt
  sm2mm_exp14.rendered.yaml       expandierte Karten-Config, so wie sie lief

results/exp14/run_{2,3,4,docker}/ nur traj_imu.tum, ape.zip, rpe_*.zip, run.md, t_offset.txt
results/exp14/REFERENCE           Läufe für compare.py (1 = Referenz, 1–4 = Streuung)
```

Nicht im Repo (`.gitignore`): `map.simplemap`, `map.mm`, `map_full*.ply`, `mola.log` sowie
Karte und Variantenvergleich der Wiederholungsläufe. Aus `map.simplemap` lässt sich
`map.ply` jederzeit neu rendern, ohne MOLA-LO erneut laufen zu lassen.

**Zeitversatz im Gruppenvergleich:** `compare.py` rechnet ATE/RPE selbst neu. Ohne
`t_offset.txt`-Unterstützung ordnet es bei MOLA-LO nur 439 von 689 GT-Posen zu (ATE 10,6
statt 10,0 cm) und meldet „wenige GT-Zuordnungen“. Die Korrektur in `common/` (liest
`t_offset.txt` in `evaluate.sh`, `compare.py`, `c2c_scan.py`) ist als Pull Request auf
`main` vorgeschlagen.

## Quellen
- J. L. Blanco-Claraco, „A flexible framework for accurate LiDAR odometry, map manipulation, and localization“, arXiv:2407.20465.
- L. Zhang et al., „Hilti-Oxford Dataset“, IEEE RA-L 2023, arXiv:2208.09825.
- MOLAorg/mola_lidar_odometry: `scripts/lib/profiles/hilti2022.sh`, `apps/mola-lidar-odometry-cli.cpp`.
- MOLAorg/mp2p_icp: `sm2mm`, `mm2ply`, `demos/sm2mm_pointcloud_voxelize.yaml`.
