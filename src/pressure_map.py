"""Build a conservative sea-level pressure layer from verified-reference observations.

Only measured sea-level pressure values are used. Mask unless at least
three distinct stations lie within 300 km. 2-degree cells are indicative,
not a forecast or an analysis in data-sparse regions.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from contourpy import contour_generator

EARTH_KM = 6371.0
RADIUS_KM = 300.0
STEP = 2.0

def unit_vectors(lat, lon):
    a, b = np.radians(lat), np.radians(lon)
    return np.column_stack((np.cos(a) * np.cos(b), np.cos(a) * np.sin(b), np.sin(a)))

def pressure_centers(grid, xs, ys, min_prominence=1.5, min_spacing_km=500):
    """Conservative local extrema; require a fully observed 3x3 neighbourhood."""
    candidates = []
    for j in range(1, grid.shape[0] - 1):
        for i in range(1, grid.shape[1] - 1):
            window = grid[j-1:j+2, i-1:i+2]
            if not np.isfinite(window).all():
                continue
            center = float(grid[j, i])
            neighbours = np.delete(window.ravel(), 4)
            if center > neighbours.max() and center - float(neighbours.min()) >= min_prominence:
                kind = "high"
            elif center < neighbours.min() and float(neighbours.max()) - center >= min_prominence:
                kind = "low"
            else:
                continue
            candidates.append((abs(center - float(np.mean(neighbours))), kind, center, float(ys[j]), float(xs[i])))
    selected = []
    for _, kind, value, lat, lon in sorted(candidates, reverse=True):
        if any(existing["properties"]["kind"] == kind and
               2 * EARTH_KM * np.arcsin(min(1.0, np.linalg.norm(
                   unit_vectors(np.array([lat]), np.array([lon]))[0] -
                   unit_vectors(np.array([existing["geometry"]["coordinates"][1]]),
                                np.array([existing["geometry"]["coordinates"][0]]))[0]) / 2))
               < min_spacing_km for existing in selected):
            continue
        selected.append({"type": "Feature", "properties": {
            "kind": kind, "hpa": round(value, 1), "method": "local_grid_extremum",
            "estimated": True},
            "geometry": {"type": "Point", "coordinates": [lon, lat]}})
    return selected


def build(source="data/latest.json", destination="data/pressure.geojson"):
    data = json.loads(Path(source).read_text(encoding="utf-8"))
    rows = [s for s in data.get("stations", [])
            if isinstance(s.get("weather", {}).get("pressure"), (int, float))
            and s.get("pressure_reference") == "sea_level"
            and -90 <= s.get("latitude", -999) <= 90
            and -180 <= s.get("longitude", -999) <= 180]
    features = []
    if len(rows) >= 3:
        lat = np.array([s["latitude"] for s in rows], dtype=float)
        lon = np.array([s["longitude"] for s in rows], dtype=float)
        values_at_stations = np.array([s["weather"]["pressure"] for s in rows], dtype=float)
        xs = np.arange(-180, 180.01, STEP)
        ys = np.arange(-80, 80.01, STEP)
        xx, yy = np.meshgrid(xs, ys)
        query = unit_vectors(yy.ravel(), xx.ravel())
        tree = cKDTree(unit_vectors(lat, lon))
        distances, indices = tree.query(query, k=min(6, len(rows)))
        if distances.ndim == 1:
            distances, indices = distances[:, None], indices[:, None]
        km = 2 * EARTH_KM * np.arcsin(np.minimum(1, distances / 2))
        nearby = km <= RADIUS_KM
        valid = nearby.sum(axis=1) >= 3
        weights = np.where(nearby, 1.0 / np.maximum(km, 1.0) ** 2, 0.0)
        weighted = np.sum(weights * values_at_stations[indices], axis=1)
        values = np.full(len(query), np.nan)
        values[valid] = weighted[valid] / weights[valid].sum(axis=1)
        grid = values.reshape(xx.shape)
        # Colored cell footprints only where surrounding grid nodes are valid.
        for j in range(len(ys) - 1):
            for i in range(len(xs) - 1):
                corners = grid[j:j+2, i:i+2]
                if not np.isfinite(corners).all():
                    continue
                v = round(float(corners.mean()), 1)
                features.append({"type": "Feature", "properties": {"kind": "cell", "hpa": v},
                                 "geometry": {"type": "Polygon", "coordinates": [[
                                     [float(xs[i]), float(ys[j])],
                                     [float(xs[i+1]), float(ys[j])],
                                     [float(xs[i+1]), float(ys[j+1])],
                                     [float(xs[i]), float(ys[j+1])],
                                     [float(xs[i]), float(ys[j])]]]} })
        features.extend(pressure_centers(grid, xs, ys))
        masked = np.ma.masked_invalid(grid)
        if masked.count() >= 4:
            contour = contour_generator(x=xs, y=ys, z=masked, name="serial")
            lo, hi = float(np.nanmin(grid)), float(np.nanmax(grid))
            for level in range(int(np.ceil(lo / 5) * 5), int(np.floor(hi / 5) * 5) + 1, 5):
                for line in contour.lines(level):
                    if len(line) < 2:
                        continue
                    features.append({"type": "Feature",
                                     "properties": {"kind": "isobar", "hpa": level},
                                     "geometry": {"type": "LineString", "coordinates": line.tolist()}})
    result = {"type": "FeatureCollection",
              "metadata": {"generated_at": datetime.now(timezone.utc).isoformat(),
                           "source_generated_at": data.get("generated_at"),
                           "pressure_stations": len(rows), "pressure_reference": "sea_level",
                           "interpolation": "IDW, six nearest, minimum three within 300 km",
                           "grid_degrees": STEP, "no_data_is_masked": True},
              "features": features}
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    print(f"Pressure map: {len(rows)} stations, {len(features)} features")

if __name__ == "__main__":
    build()
