"""Collect APRS weather packets from APRS-IS for a bounded interval."""
import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
import aprslib
from quality import normalize
from archive import append_observations

def collect(duration=180, output="data/latest.json"):
    stations = {}
    observations = []
    stats = {"received": 0, "accepted": 0, "rejected": 0, "rejected_fields": 0}
    callsign = os.environ.get("APRS_CALLSIGN", "N0CALL")
    server = os.environ.get("APRS_SERVER", "rotate.aprs2.net")
    port = int(os.environ.get("APRS_PORT", "14580"))
    passcode = os.environ.get("APRS_PASSCODE", "").strip()
    if not passcode:
        raise RuntimeError("APRS_PASSCODE fehlt. Bitte als GitHub Actions Secret hinterlegen.")
    ais = aprslib.IS(callsign, passwd=passcode, host=server, port=port)
    ais.set_filter("t/w")
    deadline = time.monotonic() + duration

    def callback(packet):
        if time.monotonic() >= deadline:
            raise StopIteration()
        stats["received"] += 1
        try:
            item = aprslib.parse(packet)
        except Exception:
            stats["rejected"] += 1
            return
        observation = normalize(item, datetime.now(timezone.utc).isoformat())
        if observation is None:
            stats["rejected"] += 1
            return
        stats["accepted"] += 1
        stats["rejected_fields"] += len(observation["rejected_fields"])
        observations.append(observation)
        stations[observation["callsign"]] = observation

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
    append_observations(observations)
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "collection_seconds": duration,
        "quality": stats,
        "stations": list(stations.values())
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {len(stations)} stations, archived {len(observations)} observations, QC: {stats}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=int, default=180)
    parser.add_argument("--output", default="data/latest.json")
    args = parser.parse_args()
    collect(args.duration, args.output)
