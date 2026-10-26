"""Run: python -m unittest discover -s tests"""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cwop import classify_aprs_station

class CWOPTests(unittest.TestCase):
    def test_common_cwop_patterns(self):
        for callsign in ("CW1234", "DW1234", "EW1234", "FW1234", "dw12345-13"):
            with self.subTest(callsign=callsign):
                self.assertEqual(classify_aprs_station(callsign), ("CWOP", "callsign_pattern"))

    def test_amateur_callsigns_and_malformed_ids(self):
        for callsign in ("OE6PLD-12", "N0CALL", "CW12", "DW1234ABC", "METAR"):
            with self.subTest(callsign=callsign):
                self.assertEqual(classify_aprs_station(callsign), ("APRS", None))
