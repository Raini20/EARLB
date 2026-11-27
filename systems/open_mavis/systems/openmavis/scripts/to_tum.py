#!/usr/bin/env python3
"""OpenMAVIS-Trajektorie (SaveTrajectoryEuRoC) -> traj_imu.tum nach Ausgabevertrag.

OpenMAVIS (Commit b13b1c2) schreibt im Modus IMU_MULTI bereits
  - die Pose des IMU-Frames (Twb = (Tbc * Tcw)^-1, System.cc SaveTrajectoryEuRoC),
  - die Zeit in Sekunden (Runner teilt die ns-Zeitstempel durch 1e9).
Es ist also weder eine Frame-Umrechnung noch ns->s nötig. Zur Sicherheit wird die
Zeit trotzdem geprüft: Werte > 1e12 werden als Nanosekunden behandelt.

Aufruf: python3 to_tum.py f_raw.txt traj_imu.tum
"""
import sys

src, dst = sys.argv[1], sys.argv[2]
rows = []
for line in open(src):
    p = line.split()
    if not p or p[0].startswith("#"):
        continue
    if len(p) != 8:
        sys.exit(f"unerwartete Zeile ({len(p)} Spalten): {line.strip()}")
    rows.append([float(v) for v in p])
if not rows:
    sys.exit(f"keine Posen in {src} (Tracking nie initialisiert?)")

ns = rows[0][0] > 1e12
with open(dst, "w") as f:
    for r in rows:
        t = r[0] / 1e9 if ns else r[0]
        f.write("%.9f %s\n" % (t, " ".join("%.9f" % v for v in r[1:])))

t0, t1 = rows[0][0], rows[-1][0]
if ns:
    t0, t1 = t0 / 1e9, t1 / 1e9
if not 1.5e9 < t0 < 2.0e9:
    print(f"WARNUNG: erste Zeit {t0} sieht nicht nach Unix-Sekunden aus")
print(f"{len(rows)} Posen, {t0:.3f} - {t1:.3f} s ({t1 - t0:.1f} s), Eingabe in {'ns' if ns else 's'}")
