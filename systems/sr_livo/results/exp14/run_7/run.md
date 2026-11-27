# SR-LIVO – Exp14 – Run 7 (Test Patch 0003, UNVOLLSTÄNDIG)

- Datum: 2026-11-22
- SR-LIVO Commit: `97a26660ca0d3723e1556b447d3b7d34f2866555` + Patches 0001, 0002, **0003 (im Container nachträglich angewendet und inkrementell gebaut)**
- Config: `config_used.yaml` (wie Run 5, `max_dist_to_plane_icp` korrekt benannt, Wert unverändert 0.3)
- Bag-Abspielrate: 0.5, ohne RViz
- Visuelles Pose-Update (VIO): an (Standard)

## Parameteränderungen gegenüber dem vorherigen Run

| Änderung | alt | neu | Begründung |
| --- | --- | --- | --- |
| Patch 0003, `optimize.cpp` | `distance < 0.3` (mit Vorzeichen) | `|distance| < 0.3` | Ausreißer auf der „negativen“ Ebenenseite wurden nie verworfen; ohne robuste Kostenfunktion ziehen sie die Pose weg (Verdacht für Divergenz ab 61 s, siehe Run 6) |
| Config-Schlüssel | `max_dist_to_plane_ct_icp` | `max_dist_to_plane_icp` | alter Name wurde vom Code nicht gelesen |

## Ergebnisse

**Ungültig – Trajektorie endet bei 55.3 s Bag-Zeit** (522 Posen statt ~707), also vor der kritischen Stelle bei 61 s.
evo lieferte APE RMSE 0.033 m, Max 0.135 m – **nur für 3–55 s aussagekräftig, nicht als Ergebnis verwenden.**

## Auffälligkeiten

- Kein Absturz im Log, kein NaN; SR-LIVO hat ab 55 s einfach keine Posen mehr geliefert, das Lauf-Skript hat nach
  10 s ohne neue Posen beendet.
- Wiederholung mit identischem Stand und Fortschrittsüberwachung (nicht gespeichert): **läuft vollständig durch**
  (707 Posen bis 73.8 s, hält mit dem Bag Schritt, CPU ~220 %, RSS ~850 MB).
  -> Der Abbruch ist nicht reproduzierbar, vermutlich ein sporadischer Hänger (Thread-Timing in SR-LIVO).
- Konsequenz: `run_exp14.sh` protokolliert jetzt den Fortschritt (`progress.log`) und warnt, wenn die Trajektorie
  nicht bis zum Bag-Ende reicht. Patch 0003 fest ins Image -> Run 8.
