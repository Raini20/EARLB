# common/ – gemeinsame Dateien für alle Systeme

Alles hier gilt für alle vier Systeme. Änderungen nur über einen Pull Request auf `main`, nicht auf den eigenen Branches.

| Datei | Inhalt |
| --- | --- |
| `gt/exp14_gt.tum` | Ground Truth Exp14 = Hilti `exp14_basement_2_imu.txt`, unverändert. TUM `t x y z qx qy qz qw`, Unix-s, IMU-Frame „I“, ~10 Hz mit Lücken, 689 Posen. Reihenfolge der Quaternionen geprüft. |
| `calib/T_lidar_imu.json` | Pose des IMU-Frames im LiDAR-Frame (T_L_I), für `evo_traj --transform_right`. Aus der Hilti-Kalibrierung (`lidar_calibration.yaml`, PandarXT-32 relativ zu imu) invertiert. Geprüft: Hin- und Rückrechnung ergibt die Originaltrajektorie (Fehler ~1e-15 m). |
| `eval/Dockerfile` | Auswerte-Image `earlb-eval` (Python, evo 1.31.1, ohne ROS) |
| `eval/evaluate.sh` | evo-Auswertung eines Laufs (ATE, RPE 1 m) → `ape.zip`, `rpe_trans.zip`, `rpe_rot.zip` |
| `eval/c2c_scan.py` | Kartengenauigkeit: C2C `map.ply` → Hilti-Laserscan, ohne ICP |
| `eval/compare.py` | Gruppenvergleich: wertet alles aus, was unter `systems/` liegt → `comparison/` |
| `eval/kpi.py` | gemeinsame Ausrichtung und KPIs (evo-API, identisch zur evo-CLI) |

## Einmalig: Auswerte-Image bauen

```bash
docker build --network=host -t earlb-eval -f common/eval/Dockerfile common/eval
```

Alle Befehle unten laufen aus der Repo-Wurzel in diesem Image. Man braucht dafür kein ROS und keine lokale evo-Installation. Kurzform für die Shell:

```bash
EVAL='docker run --rm --user '"$(id -u):$(id -g)"' -e HOME=/tmp -e GIT_COMMIT='"$(git rev-parse --short HEAD)"' -v '"$PWD"':/repo -v '"$HOME"'/data/hilti2022:/data:ro earlb-eval'
```

## Pro System: was jede Person liefern muss

Ausgabevertrag (KPI-PDF), pro Lauf:

```text
systems/<system>/results/exp14/run_<n>/
├─ traj_imu.tum    t x y z qx qy qz qw, t in Unix-Sekunden, Pose des IMU-Frames I (nicht LiDAR!)
├─ ape.zip, rpe_trans.zip, rpe_rot.zip    aus evaluate.sh
├─ map.ply         optional, im selben Weltframe wie traj_imu.tum (für C2C)
└─ run.md          Commit des Systems, Config, Laufzeit, Auffälligkeiten
```

Dazu einmal pro System `systems/<system>/results/exp14/REFERENCE`: die Run-Nummer, die in den Vergleich soll, z. B. `3`. Bei mehreren Läufen (OpenMAVIS ist nicht deterministisch, laut KPI-PDF 3–5 Läufe) eine Nummer pro Zeile. Die erste Nummer ist der Referenzlauf, über alle gibt `compare.py` Mittelwert ± Streuung der ATE aus. Ohne die Datei nimmt `compare.py` den höchsten Lauf mit voller Abdeckung. Das ist nicht immer der richtige: Bei SR-LIVO ist Run 13 ein Echtzeittest, die Referenz ist Run 10.

### 1. LiDAR-Pose in IMU-Pose umrechnen (KISS-SLAM, ggf. MOLA-LO)

```bash
cp traj_lidar.tum run_<n>/traj_lidar.txt    # .txt, sonst will evo die Eingabedatei überschreiben und fragt nach
$EVAL evo_traj tum systems/<system>/results/exp14/run_<n>/traj_lidar.txt \
     --transform_right common/calib/T_lidar_imu.json --save_as_tum
# erzeugt traj_lidar.tum im aktuellen Ordner (/repo) -> nach run_<n>/traj_imu.tum verschieben
```

`--save_as_tum` schreibt `<Name>.tum` ins Arbeitsverzeichnis. Hat die Eingabe schon die Endung `.tum`, fragt evo, ob es überschreiben darf. Im Container gibt es dafür kein Terminal, und evo bricht mit `EOFError` ab. Deshalb die Eingabe als `.txt` übergeben.

Gegenprobe: Mit der falschen Richtung (oder ganz ohne Umrechnung) liegen die Posen ~5,6 cm neben der IMU, und die ATE steigt.

### 2. OpenMAVIS: Zeit in Sekunden

```bash
awk '{printf "%.9f %s %s %s %s %s %s %s\n", $1/1e9, $2,$3,$4,$5,$6,$7,$8}' f_exp14.txt > traj_imu.tum
```

### 3. Auswerten

```bash
$EVAL bash common/eval/evaluate.sh <system> <n>
```

Wenige GT-Zuordnungen (weit unter ~650 von 689) deuten auf einen Zeitversatz hin (KISS-SLAM: Bag-Empfangszeit statt Header-Zeit). Dann `-e T_OFFSET=<s>` an `docker run` hängen und den Wert in `run.md` begründen.

### 4. Kartengenauigkeit (nur dichte LiDAR-Karten)

Braucht den Laserscan (`sheldonian_full.e57`, 5,4 GB, Download siehe `systems/sr_livo/scripts/download_data.sh --scan`) und **~26 GB RAM**. Auf einem Laptop mit 16 GB läuft das nicht, dann jemanden mit mehr RAM fragen.

```bash
$EVAL python common/eval/c2c_scan.py systems/<system>/results/exp14/run_<n> /data/laser_scans/sheldonian_full.e57
```

Die Karte wird nur mit der Trajektorien-Ausrichtung in den GT-Frame gebracht, ohne ICP. Das Skript berechnet sie selbst und speichert sie als `T_gt_est.txt`. Gemessen wird für jeden Kartenpunkt der Abstand zum nächsten Scanpunkt, also dieselbe Größe wie CloudCompare *Cloud/Cloud Distance* ohne lokales Modell. Ergebnis in `run_<n>/c2c/`. `map_c2c.ply` ist groß und bleibt lokal (in CloudCompare öffnen, das Skalarfeld `c2c` ist schon berechnet). Hintergrund und Interpretation am Beispiel SR-LIVO: `systems/sr_livo/README.md`, Abschnitt „Kartengenauigkeit“.

## Gruppenvergleich

```bash
$EVAL python common/eval/compare.py
```

Wertet aus, was da ist: Systeme ohne Ergebnisse blockieren nichts und stehen in `comparison/status.md` als offen. Nach jedem Merge eines Systems erneut ausführen und `comparison/` committen.

- `kpi_table.md` / `.csv`: ATE (RMSE, Mean, Median, Max), RPE 1 m, Abdeckung, GT-Zuordnung, C2C
- `overlay_xy.pdf`: Trajektorien-Overlay aller Systeme mit GT (Pflichtabbildung im Paper)
- `ape_time.pdf`: ATE über der Bag-Zeit, enger Treppenaufgang (59–66 s) markiert
- `status.md`: was je System vorhanden ist und was fehlt

Die Abbildungen erfüllen die Vorgaben fürs Paper: Serifenschrift in 10 pt (wie der Fließtext in IEEEtran), 300 DPI, Spaltenbreite 3,5 in, englische Beschriftung. Die Systeme unterscheiden sich durch Linienstil und Grauton und sind damit auch in Graustufen lesbar.

## Gemeinsame Regeln (aus der KPI-PDF)

- ATE und RPE mit evo, SE(3)-Umeyama (`-a`), **ohne** Skalierung, Zuordnung `--t_max_diff 0.05`, RPE über 1 m.
- ATE-Unterschiede unter ~2 cm nicht als Rangfolge lesen: Die GT ist nur auf 1–2 cm genau.
- Karten mit derselben Transformation wie die Trajektorie ausrichten, ICP nicht als Hauptwert.
- Bags, Laserscan und große Karten nicht committen (`.gitignore`).
