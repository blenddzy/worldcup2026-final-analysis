import json
import requests
from pathlib import Path


BASE_URL = "https://wcup2026.org/api/data.php"


def fetch_matches(output_path: str) -> list[dict]:
    resp = requests.get(BASE_URL, params={"action": "all"}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return data if isinstance(data, list) else []


def fetch_standings(output_path: str) -> dict:
    resp = requests.get(BASE_URL, params={"action": "standings"}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    standings = data.get("standings", {})
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output.parent / "wcup2026_standings.json", "w", encoding="utf-8") as f:
        json.dump(standings, f, indent=2, ensure_ascii=False)
    return standings


def find_final_match(matches: list[dict]) -> dict:
    for m in matches:
        if "final" in m.get("round", "").lower():
            return m
    return {}
