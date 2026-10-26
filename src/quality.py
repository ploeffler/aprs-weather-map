"""Conservative per-field validation of APRS weather observations.

aprslib reports temperature in Celsius, pressure in hPa and wind in m/s.
A rejected field is removed; a station remains if any weather field is valid.
No assumption is made about whether APRS pressure is sea-level corrected.
"""
import math

LIMITS = {
    "temperature": (-90, 65),
    "humidity": (0, 100),
    "pressure": (870, 1085),
    "wind_speed": (0, 120),
    "wind_gust": (0, 120),
    "wind_direction": (0, 360),
    "rain_1h": (0, 500),
    "rain_24h": (0, 2000),
    "rain_since_midnight": (0, 2000),
    "luminosity": (0, 200000),
}
def normalize(item, received_at):
    call = item.get("from")
    lat, lon = item.get("latitude"), item.get("longitude")
    if not isinstance(call, str) or not call.strip():
        return None
    if not all(isinstance(x, (int, float)) and math.isfinite(x) for x in (lat, lon)):
        return None
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None
    raw = item.get("weather")
    if not isinstance(raw, dict):
        return None
    weather = {}
    rejected = []
    for key, val in raw.items():
        if key not in LIMITS:
            continue
        lo, hi = LIMITS[key]
        if isinstance(val, bool) or not isinstance(val, (int, float)) or not math.isfinite(val) or not lo <= val <= hi:
            rejected.append(key)
            continue
        weather[key] = val
    if not weather:
        return None
    return {
        "callsign": call, "latitude": lat, "longitude": lon,
        "received_at": received_at, "weather": weather,
        "rejected_fields": rejected,
        "pressure_reference": "unknown" if "pressure" in weather else None,
    }
