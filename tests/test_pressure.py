import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from pressure_map import build

class PressureTests(unittest.TestCase):
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
