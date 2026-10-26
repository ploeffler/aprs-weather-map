# APRS Weather Map

Weltweite Wetterkarte aus realen Stationsmeldungen von APRS, CWOP und METAR; keine Wettermodelle oder Vorhersagedaten.

## Version 0.1 (Grundgerüst)
- APRS-IS-Liveempfang mit Filter `t/w`
- GitHub Actions alle 15 Minuten (Best-Effort, keine garantierte Ausführung)
- Drei Minuten Empfang je Lauf: Stichprobe, keine lückenlose Erfassung
- Leaflet-Weltkarte mit Stationsmarkierungen und Wetter-Rohwerten
- METAR-Flughafenbeobachtungen werden zusätzlich über AviationWeather eingelesen (Best-Effort)

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

## Drei Stationsdatenquellen (v0.4)

- **APRS:** Wetterpakete vom APRS-IS-Server mit dem serverseitigen Filter `t/w`.
- **CWOP:** CWOP wird ebenfalls über APRS-IS transportiert und ist deshalb keine unabhängige zweite Netzwerkverbindung. Explizit als `CW` gefolgt von Ziffern identifizierbare Kennungen werden als `CWOP` markiert. Weitere CWOP-Kennungen können vorläufig unter `APRS` verbleiben; eine vollständige Registrierungserkennung steht aus.
- **METAR:** Aktuelle reale Flughafenbeobachtungen über die JSON-Schnittstelle von AviationWeather (`https://aviationweather.gov/api/data/metar?format=json&hours=2`). Beobachtungen älter als zwei Stunden werden verworfen. Temperatur °C, Wind Knoten → m/s; relative Feuchte wird nur aus gemessener Temperatur und Taupunkt abgeleitet. Altimeter-Einstellungen werden **nicht** als Meereshöhendruck ausgegeben. Die METAR-Schnittstelle benötigt keine im Repository hinterlegten Zugangsdaten. Falls sie nicht erreichbar ist, läuft die APRS/CWOP-Erfassung weiter.

Alle Quellen erhalten `source`, `station_id` und soweit zuverlässig vorhanden `observed_at`. Bei APRS/CWOP ist derzeit nur `received_at` gesichert. Quellen sind in `data/latest.json → sources` getrennt ausgewiesen. Eine systemübergreifende Dublettenerkennung, ein verbindlicher Lizenz-/Nutzungsbedingungencheck sowie METAR-Feld- und Stationsabdeckungs-Tests stehen noch aus. Die Temperaturkarte interpoliert die zusammengeführten Beobachtungen ohne externe Modellwerte.

METAR-Import kann lokal mit `python src/collector.py --no-metar` deaktiviert werden. Der Abruf ist im Collector standardmäßig aktiv. **Nicht** für die operative Luftfahrt verwenden.

## Stations-Dublettenprüfung (v0.5)

Vor der Kartenerstellung werden Stationsdatensätze nur bei **identischer Stationskennung** (ohne APRS-SSID) und maximal 1 km Positionsabweichung zusammengeführt. Verschiedene Stationen am selben Ort bleiben erhalten. Bei Übereinstimmung wird die Meldung mit verifizierter Beobachtungszeit bevorzugt; Herkunftsquellen werden in `also_reported_by` festgehalten. Es werden keine Einzelmessfelder aus verschiedenen Meldungen vermischt. `cross_source_duplicates_removed` zeigt die Zahl der zusammengeführten Einträge. Dies ist eine bewusst konservative Prüfung und erkennt nicht alle physisch identischen Stationen mit verschiedenen Kennungen. Die Rohmeldungen bleiben im Kurzzeitarchiv erhalten.

Tests: `python -m unittest discover -s tests`. Die Tests sind im Repository hinterlegt; ein erfolgreicher Actions-Lauf mit dieser Änderung steht noch aus.

## CWOP-Kandidaten und automatische Tests (v0.6)

Die APRS-IS-Erfassung markiert Kennungen nach den Mustern `CW`, `DW`, `EW` oder `FW` plus 4–6 Ziffern (optional APRS-SSID) als **CWOP-Kandidaten** (`source: CWOP`, `source_classification: callsign_pattern`). Diese Mustererkennung ist keine bestätigte CWOP-Registrierung; andere registrierte CWOP-Stationen können weiter als APRS erscheinen. Der Datenweg bleibt APRS-IS; keine zusätzliche CWOP-Verbindung. Für eine verbindliche Zuordnung wäre ein zuverlässiger Stationsregisterabgleich nötig.

Der GitHub-Actions-Workflow führt jetzt vor jeder Sammlung `python -m unittest discover -s tests -v` aus. Ein fehlerhafter Test stoppt den Lauf, bevor neue Daten erzeugt werden. Die neue Version muss noch durch einen Workflow-Lauf bestätigt werden.

## Windpfeile (v0.7)

Die Webkarte bietet den separat schaltbaren Layer **Windpfeile (Messwerte)**. Pfeile stehen direkt an den tatsächlichen Stationspositionen, zeigen in die **Windbewegungsrichtung** (180° gegenüber der meteorologischen Herkunftsrichtung) und haben eine nach Geschwindigkeit begrenzte Länge. Farben kennzeichnen grobe Geschwindigkeitsstufen; der Popup enthält die exakte Windgeschwindigkeit in m/s und die meteorologische Herkunftsrichtung in Grad. Es erfolgt **keine** Windfeldinterpolation. Stationen ohne gültige Windgeschwindigkeit und Windrichtung werden ausgelassen. Bei hoher Stationsdichte können Pfeile überlappen; eine Ausdünnung nach Zoomstufe ist als nächster Optimierungsschritt vorgesehen.

## Luftdruck und Isobaren (v0.8)

`src/pressure_map.py` erstellt `data/pressure.geojson` aus **gemessenem Meeresspiegeldruck** (`pressure_reference: sea_level`). APRS-Druckwerte ohne bestätigtes Bezugsniveau werden **nicht** interpoliert. Das Raster verwendet 2°-Zellen, maximal sechs Nachbarstationen und verlangt mindestens drei Messstationen im Umkreis von 300 km; außerhalb ausreichend abgedeckter Gebiete bleibt die Karte leer. Isobaren werden in 5-hPa-Schritten berechnet. Es handelt sich um eine grobe, datenabhängige Interpolation und **keine Wettervorhersage**. Die Weboberfläche bietet getrennte, zunächst ausgeschaltete Ebenen für Luftdruckflächen und Isobaren. METAR liefert nur dann einen verwendbaren Druckwert, wenn das Feld `sea_level_pressure_mb` tatsächlich vorhanden ist. Die Unit-Tests prüfen den Ausschluss unbekannter Druckreferenzen. Ein neuer GitHub-Actions-Lauf ist für die Bestätigung nötig.

## Niederschlag (v0.9)

Die Webkarte bietet einen optionalen Layer für gemeldete Niederschlagsmengen. Über die Auswahl kann zwischen `rain_1h` (letzte Stunde), `rain_24h` (letzte 24 Stunden) und `rain_since_midnight` (seit Mitternacht) gewechselt werden. Jede Messung wird **nur an ihrer Stationsposition** als Kreis angezeigt; Kreisgröße und Farbe codieren die Menge in mm, der Popup zeigt den Zahlenwert. Fehlende Felder werden ausgelassen; 0 mm ist ein gültiger Messwert. Es erfolgt keine räumliche Interpolation und keine Ableitung zwischen den Messintervallen. Bei „seit Mitternacht“ kann die lokale Tagesgrenze je Station unterschiedlich sein. Die neue Ebene ist standardmäßig deaktiviert. Die Kartenansicht benötigt einen gesonderten Browsertest.

## Öffentliche Wetterkarte über GitHub Pages

Die interaktive Karte wird aus `web/index.html` und den automatisch erzeugten Dateien `data/latest.json`, `data/temperature.geojson` und `data/pressure.geojson` als **statische Website** veröffentlicht. Die Kartenebenen (Temperatur, Isothermen, Wind, Luftdruck, Isobaren, Niederschlag) werden clientseitig mit Leaflet dargestellt. Die Daten sind GeoJSON und JSON, keine vorgerenderten Bilder; eine zusätzliche Bildgenerierung ist nicht erforderlich.

**Einmalige Einrichtung:** Unter **Settings → Pages → Build and deployment → Source** die Option **GitHub Actions** auswählen. Anschließend den Workflow **Publish weather map to GitHub Pages** einmal manuell starten oder auf den nächsten Push warten. Erwartete Adresse: https://ploeffler.github.io/aprs-weather-map/ (erst nach erfolgreichem Deployment erreichbar).

Der Pages-Workflow wird bei Änderungen an der Website oder den generierten Wetterdaten automatisch ausgelöst. Die Datensammlung läuft weiterhin alle 15 Minuten; nach erfolgreichem Commit wird die statische Seite neu veröffentlicht. GitHub Pages führt keinen Python-Code aus. Der lokale Server (`python server.py`) bleibt nutzbar. Beachte: Bei einem öffentlichen Repository sind veröffentlichte Stationsdaten und Karten weltweit abrufbar; **niemals Secrets oder Archive in `_site` kopieren**.

## Synoptische Kartenbedienung

Die Isobaren können eingeblendet werden und erhalten automatisch ausgedünnte Beschriftungen in hPa. Beschriftungen werden abhängig vom sichtbaren Kartenausschnitt neu gesetzt. Regionale Schnellzoom-Schaltflächen bieten großräumige Ausschnitte für Europa/Nordatlantik, Nordamerika, Ostasien/Pazifik, Südamerika, Afrika, Australien/Ozeanien und die Welt. Die Isobaren bleiben eine konservative Interpolation aus gemessenem Meeresspiegeldruck; unzureichend abgedeckte Gebiete bleiben ohne Linien.
