"""Read actual worldwide METAR observations from AviationWeather's bulk cache."""
import csv
import gzip
import io
import math
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen
from quality import normalize

URL = "https://aviationweather.gov/data/cache/metars.cache.csv.gz"

def number(value):
    try:
        n = float(value)
        return n if math.isfinite(n) else None
    except (ValueError, TypeError):
        return None

def utc_time(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None

def fetch_metar(timeout=40, max_age_minutes=120):
    request = Request(URL, headers={"User-Agent": "APRS-Weather-Map/0.4 (observational weather research)"})
    with urlopen(request, timeout=timeout) as response:
        payload = response.read()
    raw = gzip.decompress(payload).decode("utf-8-sig")
    # NOAA cache includes a comment and record-count preamble.
    rows = csv.DictReader(line for line in io.StringIO(raw) if not line.startswith("#") and "," in line)
    now = datetime.now(timezone.utc)
    latest = {}
    for report in rows:
        observed = utc_time(report.get("observation_time"))
        if observed is None or not now - timedelta(minutes=max_age_minutes) <= observed <= now + timedelta(minutes=5):
            continue
        identifier = (report.get("station_id") or "").strip()
        if not identifier:
            continue
        wx = {}
        mapping = {"temp_c": "temperature", "wind_dir_degrees": "wind_direction",
                   "wind_speed_kt": "wind_speed", "wind_gust_kt": "wind_gust"}
        for source, target in mapping.items():
            value = number(report.get(source))
            if value is not None:
                wx[target] = value * 0.514444 if target in ("wind_speed", "wind_gust") else value
        temp, dew = number(report.get("temp_c")), number(report.get("dewpoint_c"))
        if temp is not None and dew is not None and dew <= temp:
            wx["humidity"] = max(0, min(100, 100 * math.exp(
                17.625 * dew / (243.04 + dew) - 17.625 * temp / (243.04 + temp))))
        slp = number(report.get("sea_level_pressure_mb"))
        if slp is not None:
            wx["pressure"] = slp
        item = {"from": identifier, "latitude": number(report.get("latitude")),
                "longitude": number(report.get("longitude")), "weather": wx}
        normalized = normalize(item, now.isoformat())
        if normalized is None:
            continue
        normalized.update({"source": "METAR", "station_id": identifier,
                           "observed_at": observed.isoformat(),
                           "pressure_reference": "sea_level" if "pressure" in normalized["weather"] else None})
        if identifier not in latest or observed > utc_time(latest[identifier]["observed_at"]):
            latest[identifier] = normalized
    return list(latest.values())
