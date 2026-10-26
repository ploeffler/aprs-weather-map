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
