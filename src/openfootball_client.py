import json
import requests
from pathlib import Path


def fetch_openfootball_data(url: str, output_path: str) -> dict:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return data


def get_final_match(data: dict) -> dict:
    for match in data.get("matches", []):
        if match.get("round") == "Final":
            return match
    return {}


def parse_match_summary(match: dict) -> dict:
    score = match.get("score", {})
    return {
        "round": match.get("round"),
        "date": match.get("date"),
        "time": match.get("time"),
        "team1": match.get("team1"),
        "team2": match.get("team2"),
        "score_ht": score.get("ht"),
        "score_ft": score.get("ft"),
        "score_et": score.get("et"),
        "goals1": match.get("goals1", []),
        "goals2": match.get("goals2", []),
        "venue": match.get("ground"),
    }


def get_all_matches(data: dict) -> list[dict]:
    return data.get("matches", [])


def get_teams_info(data: dict) -> list[dict]:
    return [
        {"name": t.get("name"), "code": t.get("code")} for t in data.get("teams", [])
    ]
