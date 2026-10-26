"""Heuristic CWOP station identification within APRS-IS weather packets.

A matching ID is a CWOP candidate, not proof of registration. APRS-IS
does not supply an authoritative CWOP membership flag.
"""
import re

CWOP_ID = re.compile(r"^(?:CW|DW|EW|FW)[0-9]{4,6}$", re.ASCII)

def classify_aprs_station(callsign):
    base = callsign.strip().upper().split("-", 1)[0]
    if CWOP_ID.fullmatch(base):
        return "CWOP", "callsign_pattern"
    return "APRS", None
