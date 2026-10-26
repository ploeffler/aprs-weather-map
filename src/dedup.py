"""Conservative cross-source duplicate handling.

Only matching station identifiers and locations within 1 km are merged.
Nearby independent sensors are intentionally retained.
"""
import math

def distance_km(a, b):
    lat1, lon1 = math.radians(a["latitude"]), math.radians(a["longitude"])
    lat2, lon2 = math.radians(b["latitude"]), math.radians(b["longitude"])
    h = math.sin((lat2-lat1)/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
    return 12742 * math.asin(min(1, math.sqrt(h)))

def deduplicate(stations):
    by_id = {}
    output = []
    removed = 0
    for station in stations:
        identifier = station.get("station_id", station.get("callsign", "")).upper().split("-")[0]
        candidates = by_id.setdefault(identifier, [])
        match = next((i for i in candidates if distance_km(output[i], station) <= 1.0), None)
        if match is None:
            candidates.append(len(output))
            output.append(station)
            continue
        old = output[match]
        sources = sorted(set(old.get("also_reported_by", [old.get("source", "APRS")]) +
                             station.get("also_reported_by", [station.get("source", "APRS")])))
        # Prefer timestamped METAR observations over APRS packets without
        # verified observation times. Never merge individual weather fields.
        prefer_new = (bool(station.get("observed_at")), station.get("source") == "METAR") > (
            bool(old.get("observed_at")), old.get("source") == "METAR")
        winner = dict(station if prefer_new else old)
        winner["also_reported_by"] = sources
        output[match] = winner
        removed += 1
    return output, removed
