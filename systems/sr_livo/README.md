# SR-LIVO auf Hilti SLAM Challenge 2022 – Exp14

[SR-LIVO](https://github.com/ZikangYuan/sr_livo) (RA-L 2024, LiDAR-Inertial-Visual-Odometrie auf Basis von R3Live) auf der Sequenz `exp14_basement_2`. Verwendet werden der Hesai PandarXT-32, die IMU BMI085 und die vordere Alphasense-Kamera `cam0`. Die Kamera dient nur zum Einfärben der Karte.

Getesteter SR-LIVO-Commit: `97a26660ca0d3723e1556b447d3b7d34f2866555` (im Dockerfile fest eingestellt) plus drei eigene Patches (`patches/`, werden beim Docker-Build angewendet).

## Ergebnis (Run 8–11, reproduzierbar auf Laptop und PC)

| Metrik (evo, SE(3)-Umeyama, ohne Skalierung) | RMSE | Mean | Median | Max |
| --- | --- | --- | --- | --- |
| APE trans [m] | 0.042 | 0.035 | 0.030 | 0.123 |
| RPE trans, 1 m [m] | 0.044 | 0.035 | 0.028 | 0.158 |
| RPE rot, 1 m [deg] | 1.21 | 1.11 | 1.07 | 2.43 |

Volle Sequenz (3,2–73,8 s, 707 Posen, 657 GT-Zuordnungen), Weglänge 38,3 m gegenüber 37,8 m GT. Run 8, 9 und 10 (Laptop) und Run 11 (PC, Ryzen 9 5900X, Image und Daten frisch) liefern byte-identische Trajektorien (MD5 `3c431ef0…`). **Referenzlauf ist `results/exp14/run_10/`.** Er wurde mit dem frisch gebauten Image erzeugt und enthält die Einzelabbildung `traj_paper.pdf` (nur SR-LIVO, Diagnose), die Karte `map.ply` und die Ausrichtung `T_gt_est.txt`. Der Weg dorthin (Run 1–9) ist in `results/exp14/run_<n>/run.md` dokumentiert. Kurz zusammengefasst:

| Problem | Symptom | Lösung |
| --- | --- | --- |
| Hesai liefert absolute Punktzeiten, SR-LIVO erwartet relative | keine Posen | Patch 0001 |
| 40-Hz-Kamera schneidet die LiDAR-Umdrehung in 90°-Sektoren | ICP ohne Überlapp, IMU-Drift | cam0 per `topic_tools/drop` auf 10 Hz |
| NTU-Parameter (draußen) im engen Treppenhaus | < 20 Residuen, ICP scheitert | Innenraum-Parameter (Keypoint-Raster 0,5 m, Karten-Voxel 0,5 m) |
| Ausreißer-Schwelle im ICP prüft den Abstand mit Vorzeichen | Divergenz ab 61 s im engen Treppenaufgang (ATE 3,8 m) | Patch 0003 (Betrag) |
| Dichtere Parameter kosten Rechenzeit | Laptop nicht echtzeitfähig | Bag mit Rate 0,5 abspielen |

**Enger Treppenaufgang = 59–66 s Bag-Zeit.** In diesem Abschnitt steigt die GT um 2,5 m (Treppe nach oben). Von 59,5 bis 63,5 s liegen 60–78 % der LiDAR-Punkte näher als 1 m am Sensor. Ab 66 s steht das Gerät bis zum Ende still (GT-Weg < 0,1 m). APE im Abschnitt: Mittel 4,5 cm, Max 7,2 cm. In Run 8 stand noch das grob gewählte Fenster 61–70 s mit 5,7 cm. Es enthält 4 s Stillstand und gilt nicht mehr.

### Was ist allgemein, was Exp14-spezifisch?

| Änderung | Art | Anmerkung |
| --- | --- | --- |
| Patch 0001 (absolute Punktzeit) | allgemeine Fehlerkorrektur | betrifft jeden LiDAR mit absoluten Punktzeiten im ROBO-Format |
| Patch 0003 (Betrag im Ausreißer-Test) | allgemeine Fehlerkorrektur | Vorzeichenfehler im Original. Gefunden und bestätigt nur auf Exp14. |
| Innenraum-Parameter (Voxel, Keypoint-Raster, `size_voxel_map`) | Umgebungsprofil | für enge Innenräume. Draußen sind die NTU-Werte vermutlich besser. |
| Kamera auf 10 Hz (`topic_tools/drop`) | aufbauspezifisch | nötig, weil SR-LIVO LiDAR-Frames an Bildzeitstempeln schneidet. Gilt für jede Kamera schneller als der LiDAR. |
| Extrinsik, Intrinsik, Topics | Sensor-Kalibrierung | Hilti-Phasma-Aufbau |
| Bag-Rate 0,5 | Rechnerleistung | damit SR-LIVO auf dem Laptop Schritt hält (siehe Abschnitt 6) |

## Ordnerstruktur

```text
systems/sr_livo/
├─ config/hilti_exp14.yaml     # SR-LIVO-Parameter (Topics, LiDAR-Typ, Extrinsik, Intrinsik)
├─ launch/livo_hilti.launch    # Launch-Datei (Vorlage: livo_ntu.launch)
├─ patches/*.patch             # eigene Korrekturen an SR-LIVO (Begründung im Kopf jedes Patches)
├─ docker/Dockerfile           # Ubuntu 20.04, ROS Noetic, PCL 1.10, Ceres 1.14, OpenCV 4.2, Livox-Driver
├─ docker/run_container.sh     # Container mit WSLg-GUI starten
├─ docker/Dockerfile.c2c       # Image für die ältere C2C-Fassung (scripts/c2c_scan.py)
├─ scripts/download_data.sh    # Bag, GT, Kalibrierung von Hugging Face laden
├─ scripts/check_bag.sh        # Topics + PointCloud2-Felder prüfen
├─ scripts/run_exp14.sh        # Ein Lauf: roslaunch + rosbag play -> results/exp14/run_<n>/
├─ scripts/evaluate.sh         # evo: APE, RPE (1 m) nach Gruppenvorgabe
├─ scripts/plot_traj.py        # Einzelabbildung (Draufsicht + APE) und T_gt_est.txt
├─ scripts/export_map.py       # map.pcd -> map.ply (Voxel 5 cm)
├─ scripts/c2c_scan.py         # ältere C2C-Fassung (25,6 GB RAM), aktuell: common/eval/c2c_scan.py
├─ requirements.txt            # Python-Pakete für die Auswertung
└─ results/exp14/run_<n>/      # traj_imu.tum, ape.zip, rpe_trans.zip, rpe_rot.zip, run.md, ...
```

## 1. Voraussetzungen

- Windows mit WSL2 (Ubuntu) und Docker (Docker Desktop mit WSL-Backend oder Docker Engine in WSL)
- Repo und Daten **im WSL-Dateisystem** (`~/...`), nicht unter `/mnt/c`
- ca. 20 GB freier Platz: Bag ~6 GB, Docker-Image ~6,2 GB, Referenz-Laserscan 5,4 GB (optional, nur für den Kartenvergleich)

```bash
git clone https://github.com/Raini20/EARLB.git ~/EARLB
cd ~/EARLB/systems/sr_livo
chmod +x scripts/*.sh docker/*.sh
```

## 2. Daten laden

```bash
./scripts/download_data.sh            # Standard: ~/data/hilti2022
```

Der Download von Hugging Face bricht bei großen Dateien oft ab (`curl: (56)` / `(92)`). Das Skript setzt dann automatisch fort und prüft am Ende die SHA256 des Bags. Bei einem Abbruch das Skript einfach erneut starten.

Bags und Rohdaten werden nicht committet (`.gitignore`).

## 3. Docker-Image bauen

```bash
docker build --network=host -t sr_livo -f docker/Dockerfile .
```

Die Zahl der parallelen Compile-Jobs richtet sich automatisch nach dem freien RAM der WSL-VM (`BUILD_JOBS=auto`): ein Job je 2,5 GB `MemAvailable`, höchstens `nproc`. Jede SR-LIVO-Datei braucht beim Kompilieren 1,5–3 GB RAM. WSL bekommt standardmäßig die Hälfte des Windows-RAMs.

| Rechner | RAM Windows / WSL | Jobs (auto) |
| --- | --- | --- |
| Laptop (Ryzen 7 7735U, 16 Threads) | 14 GB / ~6,6 GB | 2 |
| PC mit 64 GB | 64 GB / ~32 GB | ~12 |

Die Build-Ausgabe zeigt die gewählte Zahl (`catkin_make mit -j<n>`). Mit `-j$(nproc)` ist WSL auf dem Laptop komplett in den Swap gelaufen. Ein fester Wert geht mit `--build-arg BUILD_JOBS=<n>`. Den Fortschritt zeigt `docker build ... 2>&1 | tee ~/sr_livo_build.log` an, bzw. `tail -f ~/sr_livo_build.log` in einem zweiten Terminal.

Die Python-Pakete für evo werden früh im Dockerfile installiert, mit langen Timeouts und Wiederholungen. Bei einer Patch-Änderung bleibt diese Schicht im Cache, und es wird nur SR-LIVO neu kompiliert.

`--network=host` ist unter WSL2 mit Docker Engine nötig. Ohne den Schalter scheitert `apt-get` im Build mit `Temporary failure resolving 'archive.ubuntu.com'`, weil der Build-Container den DNS-Proxy von WSL nicht erreicht.

## 4. Container starten

```bash
./docker/run_container.sh ~/data/hilti2022
```

Im Container liegen `systems/sr_livo` unter `/work/sr_livo`, `common/` (read-only) unter `/work/common` und die Daten unter `/data`. RViz läuft über WSLg.

## 5. Bag prüfen (einmalig, vor dem ersten Lauf)

```bash
./scripts/check_bag.sh /data/exp14_basement_2.bag /hesai/pandar
```

Damit in `config/hilti_exp14.yaml` prüfen:
- Topic-Namen von LiDAR, IMU und `cam0`
- PointCloud2-Felder: SR-LIVO braucht `ring`. Mit `lidar_type: 4` (ROBO) erwartet es `timestamp` als `float64`.
- Einheit von `timestamp` (Sekunden -> `time_unit: 0`). Ist der erste Punkt der früheste? Davon hängt die relative Punktzeit ab.

### Datencheck Exp14 (Ergebnis)

| Prüfung | Ergebnis |
| --- | --- |
| Bag | 74 s, 45 082 Msgs, SHA256 `18eea013…5b82` = Hugging Face |
| LiDAR `/hesai/pandar` | 740 Msgs (10 Hz), ~52 000 Punkte/Scan, frame `PandarXT-32` |
| Felder | `x y z intensity` float32, `timestamp` float64 (abs. Unix-s), `ring` uint16 |
| Punktzeit | erster Punkt = frühester = `header.stamp`, Spanne 0,1 s -> `lidar_type: 4`, `time_unit: 0` |
| IMU `/alphasense/imu` | 29 539 Msgs (400 Hz), m/s², \|a\| ≈ 9,66, z zeigt nach unten (unkritisch, Gravitation wird aus den Daten initialisiert) |
| Kamera `/alphasense/cam0/image_raw` | 2 960 Msgs (40 Hz), `sensor_msgs/Image` |

## 6. Lauf starten

```bash
./scripts/run_exp14.sh <n> 0.5 false   # empfohlen: halbe Geschwindigkeit, ohne RViz
./scripts/run_exp14.sh <n> 0.5 true    # dasselbe mit RViz
```

`<n>` ist die nächste freie Run-Nummer. Run 1–10 existieren bereits, das Skript bricht bei einem vorhandenen Ordner ab.

Mit den Innenraum-Parametern ist SR-LIVO auf dem Laptop (16 Threads) nicht echtzeitfähig. Bei Rate 1,0 hängt es hinterher, die Daten werden aber gepuffert. Mit Rate 0,5 hält es Schritt, ein Lauf dauert dann ~3 min. Die Laufzeit hängt an der CPU, nicht am RAM: SR-LIVO braucht ~0,9 GB. Alle Referenz- und Vergleichsläufe verwenden Rate 0,5. Rate 1,0 auf einem schnelleren Rechner ist nur ein Echtzeittest und muss dieselbe Trajektorie liefern, bevor sie als gleichwertig gilt.

**Echtzeittest (Run 12, PC Ryzen 9 5900X, Rate 1,0):** SR-LIVO hält in Echtzeit Schritt (bis ~360 % CPU, Lauf 108 s). Die Trajektorie ist aber **nicht** byte-identisch zur Referenz: Die Abweichung beginnt im µm-Bereich, wächst im engen Treppenaufgang auf mehrere Zentimeter und erreicht am Ende max. 7,6 cm. Die Genauigkeit ändert sich dabei nicht messbar (ATE RMSE 3,9 statt 4,2 cm, RPE 4,4 cm / 1,20°, also innerhalb der GT-Genauigkeit). Die Wiederholung (Run 13) ist byte-identisch zu Run 12: SR-LIVO ist auch bei Rate 1,0 deterministisch, die Trajektorie hängt aber reproduzierbar von der Abspielrate ab (Rate 0,5 → MD5 `3c431ef0…`, Rate 1,0 → `480efb1c…`). Der Mechanismus ist nicht untersucht. Rate 1,0 gilt nach Gruppenregel nicht als gleichwertig, Referenz bleibt Rate 0,5.

Ausgewertet werden nur Läufe mit voller Abdeckung, also bis ~73,8 s (siehe Abdeckung unten).

Ohne Angabe gilt Rate 0,5. Das Skript leert `output/` (SR-LIVO hängt an `pose.txt` an), startet `roslaunch` und spielt das Bag mit `--clock -d 1.0` ab. Danach wartet es, bis `pose.txt` nicht mehr wächst, und beendet SR-LIVO mit SIGINT, damit `rgb_map.pcd` geschrieben wird.

- **Watchdog:** Kommen 60 s lang keine neuen Posen (sporadischer Hänger von SR-LIVO, Run 7), bricht das Skript den Versuch ab, sichert das Log als `launch_haenger_v<k>.log` und startet neu, bis zu 3 Versuche. Einstellbar über `HANG_TIMEOUT` und `MAX_ATTEMPTS`.
- **Abdeckung:** Am Ende prüft das Skript, ob die Trajektorie bis ~73,8 s reicht. Sonst steht eine Warnung in `run.md`, und der Lauf darf nicht ausgewertet werden.
- **Fortschritt** live verfolgen (in WSL, außerhalb des Containers):

  ```bash
  watch -n 5 'R=$(ls -td ~/EARLB/systems/sr_livo/results/exp14/run_* | head -1); echo $R; tail -4 $R/progress.log'
  ```

- **Diagnose-Schalter:** `SRLIVO_NO_VIO=1 ./docker/run_container.sh ...` schaltet das visuelle Pose-Update ab (Patch 0002). Auf Exp14 ist die Trajektorie damit byte-identisch (Run 5/6), die Kamera dient hier also nur der Einfärbung.

Die Ergebnisse kopiert das Skript nach `results/exp14/run_<n>/`:

| Datei | Inhalt |
| --- | --- |
| `traj_imu.tum` | = SR-LIVO `pose.txt`: `t x y z qx qy qz qw`, Unix-Sekunden, Pose des IMU-Frames |
| `map.pcd` | eingefärbte Karte (nur lokal, nicht committet) |
| `config_used.yaml`, `launch_used.launch` | Config und Launch zum Zeitpunkt des Laufs |
| `launch.log` | Konsolenausgabe von SR-LIVO (`debug_print: true` -> ICP-Fehlschläge sichtbar) |
| `progress.log` | alle 10 s: Posen, Bag-Zeit, CPU/RAM von SR-LIVO; Hänger und Neustarts |
| `run.md` | Commit, Laufzeit, Parameteränderungen, Auffälligkeiten (manuell ergänzen) |

## 7. Auswertung

```bash
./scripts/evaluate.sh <n>
```

Führt `evo_traj`, `evo_ape` und `evo_rpe` (1 m, `trans_part` / `angle_deg`) mit SE(3)-Umeyama-Ausrichtung **ohne** Skalierung aus und speichert `ape.zip`, `rpe_trans.zip` und `rpe_rot.zip` im Run-Ordner. Ground Truth ist standardmäßig `common/gt/exp14_gt.tum` von `main`.

## 8. Einzelabbildung und Karte

```bash
python3 scripts/plot_traj.py results/exp14/run_10          # -> traj_paper.pdf/.png, T_gt_est.txt
python3 scripts/export_map.py results/exp14/run_10          # -> map.ply (Voxel 5 cm), optional --aligned
```

- `plot_traj.py` richtet die Trajektorie genauso aus wie evo: Zuordnung ±0,05 s, SE(3)-Umeyama ohne Skalierung. Zur Kontrolle gibt das Skript die ATE aus, sie muss mit `ape.txt` übereinstimmen. Das Ergebnis ist eine Abbildung in IEEE-Spaltenbreite mit (a) Draufsicht und (b) APE über die Zeit, der enge Treppenaufgang (59–66 s) ist markiert.
- **Diagnose- bzw. Einzelabbildung, nicht die Paper-Abbildung.** Die Abbildung zeigt nur SR-LIVO, in Farbe und mit 7–8 pt Schrift. Laut Vorgabe braucht das Paper ein Overlay aller Systeme, eine Serifenschrift mindestens in Fließtextgröße, 300 DPI und Graustufen. Diese Abbildung entsteht beim Vergleich auf `main`.
- `map.ply` liegt laut Ausgabevertrag im Weltframe von `traj_imu.tum`. Für den Kartenvergleich in CloudCompare zuerst `T_gt_est.txt` anwenden (*Edit → Apply transformation*), damit die Karte mit derselben Transformation ausgerichtet ist wie die Trajektorie. Danach C2C zum Hilti-Laserscan berechnen, ohne ICP als Hauptwert.

### Referenz-Laserscan

```bash
./scripts/download_data.sh --scan     # zusätzlich laser_scans/sheldonian_full.e57 (5,4 GB, SHA256-geprüft)
```

- Exp14 wurde im **Sheldonian Theatre (Oxford)** aufgenommen, nicht auf der Baustelle. Deshalb ist `sheldonian_full.e57` der passende Scan und nicht `construction_site_full.e57`.
- Die Datei enthält **einen** registrierten Gesamtscan mit 285 Mio. Punkten (xyz, Intensität, RGB). Davon liegen 85,5 Mio. im Bereich der Exp14-Trajektorie (±5 m).
- **Gleicher Frame wie die Ground Truth:** Die GT-Trajektorie verläuft durch die gescannten Räume, der nächste Scanpunkt liegt im Median 0,22 m entfernt, maximal 1,33 m. Die SR-LIVO-Karte passt allein mit `T_gt_est.txt`, ohne ICP, auf den Scan. Erste Vorschau auf dem Laptop mit Scan-Voxeln von 5 cm: Median 4,0 cm, 60 % < 5 cm, 81 % < 10 cm.

### Kartengenauigkeit (C2C zum Laserscan)

Gerechnet wird mit dem gemeinsamen Skript `common/eval/c2c_scan.py` im Auswerte-Image `earlb-eval` (Bauen siehe `common/README.md`). Es braucht ~1 GB RAM und läuft damit auch auf dem Laptop. Aus der Repo-Wurzel:

```bash
docker run --rm --user "$(id -u):$(id -g)" -e MPLCONFIGDIR=/tmp \
    -v "$PWD":/repo -w /repo -v ~/data/hilti2022:/data:ro earlb-eval \
    python common/eval/c2c_scan.py systems/sr_livo/results/exp14/run_10 /data/laser_scans/sheldonian_full.e57
```

`scripts/c2c_scan.py` (Image aus `docker/Dockerfile.c2c`) ist die ältere SR-LIVO-Fassung, mit der Run 10 zuerst auf dem PC gerechnet wurde. Sie liest den ganzen Scan auf einmal (25,6 GB RAM, nur PC) und liefert dieselben Kennzahlen.

`c2c_scan.py` richtet `map.ply` nur mit `T_gt_est.txt` aus (dieselbe Transformation wie die Trajektorie, **kein ICP**). Dann berechnet es für jeden Kartenpunkt den Abstand zum nächsten Scanpunkt. Das ist dieselbe Größe wie CloudCompare *Cloud/Cloud Distance* ohne lokales Modell. Der Scan wird in voller Auflösung verwendet (285 Mio. Punkte, davon 111 Mio. in der Kartenbox + 2 m). Der Scan wird blockweise gelesen (`--chunk`, Standard 5 Mio. Punkte), für jeden Kartenpunkt bleibt das Minimum über alle Blöcke, also exakt derselbe nächste Nachbar. Auf dem Laptop (Docker mit `--memory=3g`): 5,5 min, Spitzen-RAM 0,9 GB, Kennzahlen identisch mit der ersten Rechnung auf dem PC. Ergebnisse in `results/exp14/run_10/c2c/`: `c2c.txt`, `c2c_hist.pdf/.png`, `c2c_topview.png` und `map_c2c.ply` (ausgerichtete Karte mit Abstand als Skalarfeld, nur lokal).

**Ergebnis Run 10** (238 731 Kartenpunkte, Voxel 5 cm):

| Mittel | Median | RMS | P90 | P95 | < 5 cm | < 10 cm | < 20 cm |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 11,2 cm | 3,3 cm | 30,8 cm | 17,3 cm | 55,2 cm | 66,2 % | 84,4 % | 90,8 % |

- **Der Median ist der aussagekräftige Wert.** Mittel und RMS werden von einem langen Ausläufer bestimmt (1 646 Punkte > 2 m). Wo der Scan gut abdeckt, passt die Karte: Haupthalle im Keller Median 4,0 cm, Obergeschoss überwiegend < 10 cm (`c2c_topview.png`).
- **Ausläufer, Ursache 1 – Lücken im Referenzscan:** Im westlichen Keller (x 96–104 m) ist der Scan ~30-mal dünner als in der Haupthalle (1 300 statt 42 000 Punkte/m² in der Draufsicht). Dort liegen nur 4,6 % der Kartenpunkte, aber 41 % aller Punkte mit > 20 cm (Median 75 cm). Das ist fehlende Referenz, kein Kartenfehler.
- **Ausläufer, Ursache 2 – vermutlich Dynamik:** Kartenpunkte direkt an der Trajektorie (< 0,5 m, in Kopf- bis Fußhöhe, 20–55 s) sind zu 53 % > 20 cm vom Scan entfernt. Das passt zu Personen oder Gegenständen, die beim Scan nicht da waren. Das ist nicht einzeln geprüft.
- Kontrolle in der CloudCompare-GUI (optional, braucht viel RAM): `map.ply` laden, *Edit → Apply transformation* mit `T_gt_est.txt`, Scan laden und auf die Kartenbox zuschneiden, *Tools → Distances → Cloud/Cloud Dist.* mit der Karte als *Compared* und dem Scan als *Reference*, ohne lokales Modell. Alternativ `map_c2c.ply` öffnen, das Skalarfeld `c2c` ist schon berechnet.

## Konfiguration – Herleitung

| Parameter | Wert | Quelle / Begründung |
| --- | --- | --- |
| `lidar_type` | 4 (ROBO) | SR-LIVO hat keinen Hesai-Typ. ROBO liest `ring` (uint16) + `timestamp` (double), das entspricht dem Hesai-Format. |
| `N_SCANS` / `SCAN_RATE` | 32 / 10 | PandarXT-32, 10 Hz |
| `time_unit` | 0 (s) | Hesai-Punktzeit in Sekunden (mit `check_bag.sh` geprüft) |
| `extrinsic_*_imu_lidar` | R = [[0,-1,0],[-1,0,0],[0,0,-1]], t = [-0.001, -0.00855, 0.055] | `lidar_calibration.yaml`, q_xyzw = [0.7071, -0.7071, 0, 0], parent = imu |
| `extrinsic_*_imu_camera` | inv(`T_cam_imu`) von cam0 | `calib_3_cam0-1-camchain-imucam.yaml`. SR-LIVO braucht `T_imu_cam` (`R_world_cam = R_world_imu · R_imu_camera`). |
| `camera_intrinsic` | fx 351.31, fy 351.49, cx 367.85, cy 253.84 | cam0, Kalibr |
| `camera_dist_coeffs` | 0 | Kalibr: equidistant (Fisheye), SR-LIVO: radtan, also nicht übertragbar. Betrifft nur die Karteneinfärbung. |
| `image_topic` | `/alphasense/cam0/image_10hz` | Launch: `topic_tools/drop 3 4`. SR-LIVO bildet einen Frame aus den LiDAR-Punkten zwischen zwei Bildern. Bei 40 Hz wäre das nur ein 90°-Sektor ohne Überlapp zur Karte (Run 2/3). |
| `init_voxel_size` / `voxel_size` | 0,1 / 0,1 m | Default 0,2: zu wenige Punkte im engen Treppenhaus |
| `init_sample_voxel_size` / `sample_voxel_size` | 0,5 / 0,5 m | NTU 1,0 / 1,5: zu wenige Keypoints, ICP < 20 Residuen (Run 3) |
| `min_distance_points` | 0,05 m | NTU 0,15: dichtere Karte |
| `icp_options/size_voxel_map` | 0,5 m | NTU 1,0: feinere Nachbarschaftssuche |
| `icp_options/max_dist_to_plane_icp` | 0,3 m | In der NTU-Config falsch als `..._ct_icp` benannt und dadurch ignoriert. Wirkt erst mit Patch 0003 auf beiden Seiten der Ebene. |
| `icp_options/debug_print` | true | ICP-Fehlschläge im Log sichtbar |

## Patches an SR-LIVO

| Patch | Datei | Inhalt |
| --- | --- | --- |
| `0001-robo-absolute-timestamp` | `cloudProcessing.cpp` | Scandauer relativ zum ersten Punkt. Sonst landet `last_end_time` bei absoluten Hesai-Zeiten ~50 Jahre in der Zukunft, und alle Punkte werden verworfen. |
| `0002-optional-disable-vio-update` | `imageProcessing.cpp` | Diagnose-Schalter `SRLIVO_NO_VIO=1`. Ohne Variable ändert sich nichts. |
| `0003-abs-point-to-plane-gate` | `optimize.cpp` | Ausreißer-Schwelle auf den Betrag des Punkt-Ebene-Abstands. Vorher wurden beliebig große Abstände auf einer Ebenenseite akzeptiert, ohne robuste Kostenfunktion. Das führte zur Divergenz im engen Treppenaufgang. |

## Bekannte Einschränkungen

- Fisheye-Kamera wird als Pinhole ohne Verzeichnung projiziert. Die Farben am Bildrand sind dadurch ungenau, die Trajektorie ist nicht betroffen.
- **Auf Exp14 abgestimmt:** Die Parameter und Patch 0003 wurden anhand von Exp14 und dessen Ground Truth gefunden. Es gibt keine unabhängige Validierung auf einer anderen Sequenz. Die Ergebnisse sind daher eher optimistisch.
- Nicht echtzeitfähig auf dem Laptop mit den Innenraum-Parametern (Rate 0,5 nötig). Auf dem PC echtzeitfähig (Run 12), dann aber mit anderer Trajektorie: Das Ergebnis hängt reproduzierbar von der Abspielrate ab (Run 12 = Run 13, max. 7,6 cm Abweichung zur Referenz, ATE unverändert).
- Reproduktion auf einem zweiten Rechner bestätigt: Run 11 auf dem PC (Ryzen 9 5900X, frisch gebautes Image, frisch geladene Daten) ist byte-identisch zu Run 8–10 (MD5 `3c431ef0…`). Nur die Rohkarte unterscheidet sich um wenige Punkte (nicht deterministische Einfärbung).
- Sporadischer Hänger von SR-LIVO (einmal in Run 7, nicht reproduzierbar), wird vom Watchdog abgefangen.
- Ground Truth: `evaluate.sh` nutzt `common/gt/exp14_gt.tum` von `main`. Die Datei ist eine unveränderte Kopie der Hilti-Datei `exp14_basement_2_imu.txt`. Die Läufe 1–13 wurden noch direkt mit der Hilti-Datei ausgewertet, die Ergebnisse sind identisch.

## Lizenz

SR-LIVO steht unter GPL-2.0 und wird im Container aus dem Original-Repo gebaut, nicht in dieses Repo kopiert.
