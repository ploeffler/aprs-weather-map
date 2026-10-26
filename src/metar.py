"""Import current airport station observations from AviationWeather METAR JSON.

Only actual reports with coordinates and an observation time are accepted.
No forecasts, model fields, or inferred values.
"""
import json
import math
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen
from quality import normalize

URL = "https://aviationweather.gov/api/data/metar?format=json&hours=2"

def number(value):
    try:
        n = float(value)
        return n if math.isfinite(n) else None
    except (ValueError, TypeError):
        return None

def utc_time(value):
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, timezone.utc)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
        except ValueError:
            return None
    return None

def fetch_metar(timeout=25, max_age_minutes=120):
    request = Request(URL, headers={"User-Agent": "APRS-Weather-Map/0.4 (weather observation research)", "Accept": "application/json"})
    with urlopen(request, timeout=timeout) as response:
        reports = json.load(response)
    if not isinstance(reports, list):
        raise ValueError("Unexpected METAR response")
    now = datetime.now(timezone.utc)
    result = []
    for report in reports:
        if not isinstance(report, dict):
            continue
        observed = utc_time(report.get("obsTime") or report.get("reportTime"))
        if observed is None or not now - timedelta(minutes=max_age_minutes) <= observed <= now + timedelta(minutes=5):
            continue
        identifier = report.get("icaoId")
        if not isinstance(identifier, str) or not identifier:
            continue
        wx = {}
        mapping = {"temp": "temperature", "wdir": "wind_direction", "wspd": "wind_speed",
                   "wgst": "wind_gust"}
        for source, target in mapping.items():
            value = number(report.get(source))
            if value is not None:
                # METAR wind speeds and gusts are reported in knots.
                wx[target] = value * 0.514444 if target in ("wind_speed", "wind_gust") else value
        # altim is an altimeter setting, not necessarily sea-level pressure.
        # Do not treat it as a verified MSL pressure.
        temp, dew = number(report.get("temp")), number(report.get("dewp"))
        if temp is not None and dew is not None and dew <= temp:
            # Magnus approximation; only if both actual readings exist.
            wx["humidity"] = max(0, min(100, 100 * math.exp((17.625 * dew)/(243.04 + dew) - (17.625 * temp)/(243.04 + temp))))
        item = {"from": identifier, "latitude": number(report.get("lat")),
                "longitude": number(report.get("lon")), "weather": wx}
        normalized = normalize(item, now.isoformat())
        if normalized is None:
            continue
        normalized.update({"source": "METAR", "station_id": identifier,
                           "observed_at": observed.isoformat(),
                           "pressure_reference": None})
        result.append(normalized)
    return result
