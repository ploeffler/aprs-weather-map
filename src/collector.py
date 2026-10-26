"""Collect APRS weather packets from APRS-IS for a bounded interval."""
import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
import aprslib

def collect(duration=180, output="data/latest.json"):
    stations = {}
    callsign = os.environ.get("APRS_CALLSIGN", "N0CALL")
    server = os.environ.get("APRS_SERVER", "rotate.aprs2.net")
    port = int(os.environ.get("APRS_PORT", "14580"))
    ais = aprslib.IS(callsign, passwd=-1, host=server, port=port)
    ais.set_filter("t/w")
    deadline = time.monotonic() + duration

    def callback(packet):
        if time.monotonic() >= deadline:
            raise StopIteration()
        try:
            item = aprslib.parse(packet)
        except Exception:
            return
        wx = item.get("weather")
        lat, lon = item.get("latitude"), item.get("longitude")
        if not isinstance(wx, dict) or lat is None or lon is None:
            return
        call = item.get("from", "")
        if not call:
            return
        stations[call] = {
            "callsign": call, "latitude": lat, "longitude": lon,
            "received_at": datetime.now(timezone.utc).isoformat(),
            "weather": wx,
        }

    try:
        ais.connect()
        ais.consumer(callback, raw=True, blocking=True)
    except StopIteration:
        pass
    finally:
        try:
            ais.close()
        except Exception:
            pass
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "collection_seconds": duration,
        "stations": list(stations.values())
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {len(stations)} weather stations to {target}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=int, default=180)
    parser.add_argument("--output", default="data/latest.json")
    args = parser.parse_args()
    collect(args.duration, args.output)
