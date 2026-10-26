# APRS Weather Map

Weltweite Wetterkarte ausschließlich aus APRS-Wetterstationsmeldungen.

## Version 0.1 (Grundgerüst)
- APRS-IS-Liveempfang mit Filter `t/w`
- GitHub Actions alle 15 Minuten (Best-Effort, keine garantierte Ausführung)
- Drei Minuten Empfang je Lauf: Stichprobe, keine lückenlose Erfassung
- Leaflet-Weltkarte mit Stationsmarkierungen und Wetter-Rohwerten
- Keine externen meteorologischen Datenquellen

## Einrichtung
1. Repository privat belassen.
2. Unter Settings → Secrets and variables → Actions → Variables `APRS_CALLSIGN` auf das eigene gültige Rufzeichen setzen.
3. Workflow `Collect APRS weather` unter Actions manuell starten.
4. Karte lokal testen: `python -m http.server 8000`, dann `http://localhost:8000/web/`.

GitHub Pages ist für private Repositories nicht in jedem Tarif verfügbar; eine öffentliche Veröffentlichung ist nicht aktiviert.

## Geplant
- Datenarchiv und Qualitätsprüfung
- Positionszuordnung für positionslose Wetterberichte
- Isobaren, Isothermen und Windfelder
- Druckbezugsniveau-Prüfung
- Kennzeichnung unzureichender Stationsabdeckung

## Qualitätskontrolle und Archiv (v0.2)

Der Collector prüft Koordinaten und plausible Messwertgrenzen feldweise. Ungültige Felder werden verworfen, während gültige Werte erhalten bleiben. Die Statistik steht in `data/latest.json → quality`. Die eingegangenen gültigen Einzelbeobachtungen werden in `data/archive/YYYY-MM-DD.jsonl` protokolliert und für den aktuellen und vorherigen UTC-Kalendertag im Repository gehalten. Dies ist ein **kurzfristiges Rohdatenarchiv**, keine vollständige historische Datenbank. Bei mehreren Meldungen derselben Station zeigt die Karte nur die neueste Meldung des Erfassungsfensters.

Wichtig: `pressure_reference: unknown` bedeutet, dass die Druckmessung **nicht** als Meereshöhendruck verifiziert wurde. Für Isobaren ist eine zusätzliche Prüfung erforderlich. Zeitliche Plausibilität bezieht sich derzeit auf die **Empfangszeit**; das tatsächliche Alter einer weitergeleiteten APRS-Meldung ist noch nicht geprüft. Die begrenzten dreiminütigen Sammelfenster bleiben bestehen.

## Temperaturkarte v0.3

Nach jeder Erfassung erzeugt `src/temperature_map.py` die Datei `data/temperature.geojson`. Die Webkarte bietet separat schaltbare farbige Temperaturflächen, Isothermen in 5-°C-Schritten und Stationspunkte. Die Berechnung verwendet ausschließlich APRS-Temperaturen: inverse Distanzgewichtung (IDW) auf einem 2°-Raster mit maximal sechs Nachbarn; mindestens drei Stationen müssen innerhalb von 300 km liegen. Unzureichend abgedeckte Bereiche bleiben leer. Die Ergebnisse sind grob aufgelöste Näherungen und keine vollständige Wetteranalyse. Die Darstellung ist nicht als präzise lokale Prognose geeignet.

Die Erfassung bleibt eine dreiminütige Stichprobe alle 15 Minuten; die zeitliche Aktualität der ursprünglichen APRS-Messung wird noch nicht vollständig geprüft. Für eine lokale Vorschau: `python -m http.server 8000` im Repository-Hauptverzeichnis, danach `http://localhost:8000/web/` öffnen.

## Integrierter Mini-Webserver

Nach dem Herunterladen oder Klonen des Projekts genügt:

```bash
python server.py
```

Danach im Browser `http://127.0.0.1:8000/` öffnen. Der Webserver liefert die interaktive Karte und die bereits vorhandenen Dateien unter `data/` aus. Es werden keine zusätzlichen Python-Pakete für den Webserver benötigt. Optional: `python server.py --port 8080`; für den Zugriff aus dem lokalen Netzwerk ausdrücklich `python server.py --host 0.0.0.0` verwenden (Firewall und Zugriffsschutz beachten).

**Wichtig:** Der Mini-Webserver zeigt lokal gespeicherte Ergebnisse an; er führt nicht automatisch einen APRS-IS-Empfang durch. Die Karte lädt Leaflet und OpenStreetMap-Kacheln weiterhin über das Internet. Da der Server das gesamte Projektverzeichnis bereitstellt, sollte er **nicht öffentlich exponiert** werden; insbesondere dürfen keine Secrets im Projektverzeichnis abgelegt werden. Eine spätere Version soll die Auslieferung auf `web/` und ausgewählte Datenendpunkte beschränken.
