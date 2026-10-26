import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from pressure_map import build, pressure_centers
import numpy as np

class PressureTests(unittest.TestCase):
    def test_pressure_centers_require_complete_neighbourhood(self):
        xs = np.arange(5, dtype=float)
        ys = np.arange(5, dtype=float)
        grid = np.full((5, 5), 1010.0)
        grid[2, 2] = 1015.0
        centers = pressure_centers(grid, xs, ys)
        self.assertEqual(len(centers), 1)
        self.assertEqual(centers[0]["properties"]["kind"], "high")
        grid[1, 1] = np.nan
        self.assertEqual(pressure_centers(grid, xs, ys), [])

    def test_low_pressure_center(self):
        grid = np.full((5, 5), 1010.0)
        grid[2, 2] = 1005.0
        centers = pressure_centers(grid, np.arange(5), np.arange(5))
        self.assertEqual(len(centers), 1)
        self.assertEqual(centers[0]["properties"]["kind"], "low")

    def test_only_sea_level_pressure_is_used(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "latest.json"
            dest = Path(directory) / "pressure.geojson"
            source.write_text(json.dumps({"stations": [
                {"latitude": 47, "longitude": 15, "weather": {"pressure": 1010}, "pressure_reference": "unknown"},
                {"latitude": 47, "longitude": 15, "weather": {"pressure": 1012}, "pressure_reference": "sea_level"}
            ]}))
            build(str(source), str(dest))
            result = json.loads(dest.read_text())
            self.assertEqual(result["metadata"]["pressure_stations"], 1)
            self.assertEqual(result["features"], [])
            self.assertEqual(result["metadata"]["pressure_reference"], "sea_level")
