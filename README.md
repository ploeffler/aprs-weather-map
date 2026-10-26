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
