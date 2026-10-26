"""Bounded rolling APRS observation history in daily JSONL files."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

def append_observations(observations, directory="data/archive", retention_days=2):
    folder = Path(directory)
    folder.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).date()
    by_day = {}
    for obs in observations:
        try:
            day = datetime.fromisoformat(obs["received_at"].replace("Z", "+00:00")).astimezone(timezone.utc).date()
        except (ValueError, KeyError, TypeError):
            continue
        if today - timedelta(days=retention_days - 1) <= day <= today:
            by_day.setdefault(day.isoformat(), []).append(obs)
    for day, rows in by_day.items():
        with (folder / (day + ".jsonl")).open("a", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False, allow_nan=False) + "\n")
    cutoff = today - timedelta(days=retention_days - 1)
    for path in folder.glob("????-??-??.jsonl"):
        if path.stem < cutoff.isoformat() or path.stem > today.isoformat():
            path.unlink()
