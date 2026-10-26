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
from metar import fetch_metar
from dedup import deduplicate
from cwop import classify_aprs_station

def collect(duration=180, output="data/latest.json", enable_metar=True):
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
        # Callsign patterns identify CWOP candidates, not verified membership.
        source, classification = classify_aprs_station(observation["callsign"])
        if classification:
            observation["source_classification"] = classification
        observation["source"] = source
        observation["station_id"] = observation["callsign"]
        observation["observed_at"] = None  # APRS packet time not verified
        stats["accepted"] += 1
        stats["rejected_fields"] += len(observation["rejected_fields"])
        observations.append(observation)
        stations[source + ":" + observation["callsign"]] = observation

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
    source_stats = {"APRS": sum(s["source"] == "APRS" for s in observations),
                    "CWOP": sum(s["source"] == "CWOP" for s in observations),
                    "METAR": 0}
    source_status = {"APRS": "ok", "CWOP": "shared_aprs_feed", "METAR": "disabled" if not enable_metar else "pending"}
    if enable_metar:
        try:
            metar = fetch_metar()
            for obs in metar:
                observations.append(obs)
                stations["METAR:" + obs["station_id"]] = obs
            source_stats["METAR"] = len(metar)
            source_status["METAR"] = "ok" if metar else "empty"
            if not metar:
                print("::warning::METAR import returned zero valid stations")
        except Exception as exc:
            source_status["METAR"] = "error"
            print(f"::warning::METAR feed unavailable; keeping APRS/CWOP observations: {exc}")
    unique_stations, duplicates = deduplicate(list(stations.values()))
    append_observations(observations)
    target = Path(output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "collection_seconds": duration,
        "quality": stats,
        "sources": source_stats,
        "source_status": source_status,
        "cross_source_duplicates_removed": duplicates,
        "stations": unique_stations
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Sources: {source_stats}; status: {source_status}")
    print(f"Deduplicated {duplicates} station entries")
    print(f"Saved {len(unique_stations)} stations, archived {len(observations)} observations, QC: {stats}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=int, default=180)
    parser.add_argument("--output", default="data/latest.json")
    parser.add_argument("--no-metar", action="store_true", help="Disable external METAR import")
    args = parser.parse_args()
    collect(args.duration, args.output, enable_metar=not args.no_metar)
