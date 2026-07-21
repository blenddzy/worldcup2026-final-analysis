import json
import re
from pathlib import Path

import requests

STATS_URL = "https://www.foxsports.com/soccer/2026-fifa-world-cup/stats"


def _resolve_refs(data: list, obj: dict) -> dict:
    resolved = {}
    for key, val in obj.items():
        if isinstance(val, int) and 0 <= val < len(data):
            resolved[key] = data[val]
        else:
            resolved[key] = val
    return resolved


def fetch_team_stats(url: str = STATS_URL) -> dict:
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    m = re.search(
        r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', resp.text, re.DOTALL
    )
    if not m:
        return None
    data = json.loads(m.group(1))
    results = {}
    for i, item in enumerate(data):
        if not isinstance(item, dict):
            continue
        keys = set(item.keys())
        needed = {"name", "title", "statAbbreviation", "statValue"}
        if not needed.issubset(keys):
            continue
        resolved = _resolve_refs(data, item)
        name = str(resolved.get("name", ""))
        abbr = str(resolved.get("statAbbreviation", ""))
        val = str(resolved.get("statValue", ""))
        title = str(resolved.get("title", ""))
        if abbr and val and name:
            if name not in results:
                results[name] = {}
            results[name][abbr] = {
                "value": val,
                "stat_name": title,
            }
    return results


def load_team_stats(output_path: str = None) -> dict:
    fallback_path = (
        Path(__file__).parent.parent
        / "data"
        / "external"
        / "fox_sports_team_stats.json"
    )
    if output_path:
        stats = fetch_team_stats(STATS_URL)
        if stats:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                json.dump(stats, f, indent=2)
            return stats
    if fallback_path.exists():
        with open(fallback_path) as f:
            return json.load(f)
    return None


if __name__ == "__main__":
    stats = fetch_team_stats()
    if stats:
        print(json.dumps(stats, indent=2))
    else:
        print("Could not fetch team stats")
