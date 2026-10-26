"""Run locally: python -m unittest discover -s tests"""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dedup import deduplicate

def station(source, ident, lat, lon, observed=None):
    return {"source": source, "station_id": ident, "callsign": ident,
            "latitude": lat, "longitude": lon, "observed_at": observed,
            "weather": {"temperature": 10}}

class DedupTests(unittest.TestCase):
    def test_same_station_prefers_timestamped_metar(self):
        stations, count = deduplicate([
            station("APRS", "LOWG", 47.0, 15.0),
            station("METAR", "LOWG", 47.0001, 15.0001, "2026-10-26T12:00:00+00:00")])
        self.assertEqual((len(stations), count), (1, 1))
        self.assertEqual(stations[0]["source"], "METAR")
        self.assertEqual(stations[0]["also_reported_by"], ["APRS", "METAR"])

    def test_nearby_independent_stations_preserved(self):
        stations, count = deduplicate([
            station("APRS", "ABC", 47.0, 15.0),
            station("METAR", "DEF", 47.0, 15.0)])
        self.assertEqual((len(stations), count), (2, 0))

    def test_same_id_different_position_preserved(self):
        stations, count = deduplicate([
            station("APRS", "ABC", 47.0, 15.0),
            station("METAR", "ABC", 48.0, 15.0)])
        self.assertEqual((len(stations), count), (2, 0))

if __name__ == "__main__":
    unittest.main()
