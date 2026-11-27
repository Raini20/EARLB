import os
import shutil
import subprocess
import time
from datetime import datetime
from importlib.metadata import version

os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/..")  # immer aus systems/kiss_slam starten

BAG = os.path.expanduser("~/data/hilti2022/exp14_basement_2.bag")
CONFIG = "config/kiss_slam_hilti.yaml"  # oder config/kiss_slam_default.yaml (Standard aus GitHub)
RUN = "results/exp14/run_3"  # gleicher Wert wie in evaluate.py

start = time.time()
subprocess.run([
    "kiss_slam_pipeline", BAG,
    "--dataloader", "rosbag",
    "--topic", "/hesai/pandar",
    "--config", CONFIG,
    "--refuse-scans",
    "-v",
], check=True)
dauer = time.time() - start

# run.md und verwendete Config im Run-Ordner ablegen (Ausgabevertrag)
os.makedirs(RUN, exist_ok=True)
shutil.copy(CONFIG, f"{RUN}/config_used.yaml")
metriken = open("slam_output/latest/result_metrics.log").read()
with open(f"{RUN}/run.md", "w") as f:
    f.write(f"""# KISS-SLAM – {os.path.basename(BAG)}

- Datum: {datetime.now():%Y-%m-%d %H:%M}
- System: kiss-slam {version('kiss-slam')} (von PyPI, kein Git-Commit), kiss-icp {version('kiss-icp')}, map_closures {version('map_closures')}
- Config: config_used.yaml (Kopie von {CONFIG})
- Laufzeit: {dauer:.0f} s inkl. Visualisierung (Bag-Dauer 74 s)
- Zeitbasis: Bag-Empfangszeit, t_offset 0 s

## Ergebnis KISS-SLAM

{metriken}
## Auffälligkeiten

- map_closures==2.0.2 nötig: ab 2.1.0 fehlt align_map_to_local_ground, --refuse-scans stürzt ab
- keine Loop Closures auf Exp14 (Strecke kehrt nicht an bekannte Orte zurück)
""")
print(f"run.md geschrieben: {RUN}/run.md")
