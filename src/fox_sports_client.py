import json
import re
import time
from pathlib import Path

import requests

STATS_URL = "https://www.foxsports.com/soccer/2026-fifa-world-cup/stats"
API_KEY = "jE7yBJVRNAwdDesMgTzTXUUSx1It41Fq"
BASE_API = "https://api.foxsports.com/bifrost/v1"

TEAM_ABBR_MAP = {
    "MEX": "Mexico",
    "RSA": "South Africa",
    "KOR": "South Korea",
    "CZE": "Czech Republic",
    "CAN": "Canada",
    "BIH": "Bosnia & Herzegovina",
    "USA": "USA",
    "PAR": "Paraguay",
    "QAT": "Qatar",
    "SUI": "Switzerland",
    "BRA": "Brazil",
    "MAR": "Morocco",
    "HAI": "Haiti",
    "SCO": "Scotland",
    "AUS": "Australia",
    "TUR": "Turkey",
    "GER": "Germany",
    "CUW": "Curaçao",
    "NED": "Netherlands",
    "JPN": "Japan",
    "CIV": "Ivory Coast",
    "ECU": "Ecuador",
    "SWE": "Sweden",
    "TUN": "Tunisia",
    "ESP": "Spain",
    "CPV": "Cape Verde",
    "BEL": "Belgium",
    "EGY": "Egypt",
    "KSA": "Saudi Arabia",
    "URU": "Uruguay",
    "IRN": "Iran",
    "NZL": "New Zealand",
    "FRA": "France",
    "SEN": "Senegal",
    "IRQ": "Iraq",
    "NOR": "Norway",
    "ARG": "Argentina",
    "ALG": "Algeria",
    "AUT": "Austria",
    "JOR": "Jordan",
    "POR": "Portugal",
    "COD": "DR Congo",
    "ENG": "England",
    "CRO": "Croatia",
    "GHA": "Ghana",
    "PAN": "Panama",
    "UZB": "Uzbekistan",
    "COL": "Colombia",
}
REVERSE_TEAM_MAP = {v: k for k, v in TEAM_ABBR_MAP.items()}

SEGMENT_IDS = [
    "2026-20260611",
    "2026-20260618",
    "2026-20260624",
    "2026-20260628",
    "2026-20260704",
    "2026-20260709",
    "2026-20260714",
    "2026-20260718",
    "2026-20260719",
]

ROUND_MAP = {
    "2026-20260611": "Group stage",
    "2026-20260618": "Group stage",
    "2026-20260624": "Group stage",
    "2026-20260628": "Round of 32",
    "2026-20260704": "Round of 16",
    "2026-20260709": "Quarter-final",
    "2026-20260714": "Semi-final",
    "2026-20260718": "Bronze Final",
    "2026-20260719": "Final",
}

STAT_LABELS = [
    "possession",
    "total_shots",
    "shots_on_goal",
    "expected_goals",
    "chances_created",
    "passing_accuracy",
    "crosses",
    "corners",
    "offsides",
    "fouls",
    "tackles",
    "interceptions",
    "blocks",
    "clearances",
    "keeper_saves",
    "yellow_cards",
    "red_cards",
]

STAT_TITLE_MAP = {
    "POSSESSION (%)": "possession",
    "TOTAL SHOTS": "total_shots",
    "SHOTS ON GOAL": "shots_on_goal",
    "EXPECTED GOALS (xG)": "expected_goals",
    "CHANCES CREATED": "chances_created",
    "PASSING ACCURACY (%)": "passing_accuracy",
    "CROSSES (SUCCESSFUL)": "crosses",
    "CORNERS": "corners",
    "OFFSIDES": "offsides",
    "FOULS": "fouls",
    "TACKLES": "tackles",
    "INTERCEPTIONS": "interceptions",
    "BLOCKS": "blocks",
    "CLEARANCES": "clearances",
    "KEEPER SAVES": "keeper_saves",
    "YELLOW CARDS": "yellow_cards",
    "RED CARDS": "red_cards",
}


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
    return {}


# --- Per-match stats ---


def _abbr_to_full(fox_abbr: str) -> str:
    return TEAM_ABBR_MAP.get(fox_abbr, fox_abbr)


def _full_to_abbr(full_name: str) -> str:
    return REVERSE_TEAM_MAP.get(full_name, full_name)


def fetch_match_ids() -> dict:
    matches = {}
    for seg_id in SEGMENT_IDS:
        url = f"{BASE_API}/soccer/league/schedule-segment/{seg_id}?groupId=12&apikey={API_KEY}"
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        if resp.status_code != 200:
            continue
        data = resp.json()
        for table in data.get("tables", []):
            for row in table.get("rows", []):
                cols = row.get("columns", [])
                if len(cols) < 3:
                    continue
                ent = row.get("entityLink") or {}
                uri = ent.get("contentUri", "")
                web_url = ent.get("webUrl", "")
                if not uri:
                    continue
                match_id = uri.split("/")[-1]
                if match_id in matches:
                    continue
                home_abbr = cols[0].get("text", "")
                away_abbr = cols[2].get("text", "")
                home_full = _abbr_to_full(home_abbr)
                away_full = _abbr_to_full(away_abbr)
                page_url = f"https://www.foxsports.com{web_url}" if web_url else None
                matches[match_id] = {
                    "home_team": home_full,
                    "away_team": away_full,
                    "home_abbr": home_abbr,
                    "away_abbr": away_abbr,
                    "round": ROUND_MAP.get(seg_id, "Unknown"),
                    "page_url": page_url,
                }
    return matches


def extract_nuxt_match_stats(html: str) -> list:
    m = re.search(
        r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL
    )
    if not m:
        return []
    data = json.loads(m.group(1))
    stats = []
    for item in data:
        if not isinstance(item, dict):
            continue
        if "title" not in item or "leftStat" not in item or "rightStat" not in item:
            continue
        title_idx = item["title"]
        left_idx = item["leftStat"]
        right_idx = item["rightStat"]
        if (
            not isinstance(title_idx, int)
            or not isinstance(left_idx, int)
            or not isinstance(right_idx, int)
        ):
            continue
        if not (
            0 <= title_idx < len(data)
            and 0 <= left_idx < len(data)
            and 0 <= right_idx < len(data)
        ):
            continue
        title_raw = str(data[title_idx])
        stat_key = STAT_TITLE_MAP.get(title_raw)
        if not stat_key:
            continue
        left_val = data[left_idx]
        right_val = data[right_idx]
        stats.append(
            {
                "stat": stat_key,
                "title": title_raw,
                "home_value": str(left_val),
                "away_value": str(right_val),
            }
        )
    return stats


def fetch_match_stats(match_id: str, page_url: str = None) -> dict:
    if page_url:
        url = page_url
    else:
        url = f"https://www.foxsports.com/soccer/fifa-world-cup-men-{match_id}"
    resp = requests.get(
        url,
        timeout=15,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
    )
    if resp.status_code != 200:
        return None
    stats = extract_nuxt_match_stats(resp.text)
    if not stats:
        return None
    result = {}
    for s in stats:
        result[s["stat"]] = {
            "home": s["home_value"],
            "away": s["away_value"],
        }
    return result


def fetch_all_match_stats(cache_path: str = None) -> dict:
    if cache_path:
        path = Path(cache_path)
        if path.exists():
            print(f"       Loading cached per-match stats from {cache_path}")
            with open(path) as f:
                return json.load(f)

    matches = fetch_match_ids()
    total = len(matches)
    print(f"       Fetching per-match stats for {total} matches...")

    all_stats = {}
    for i, (mid, info) in enumerate(matches.items()):
        print(
            f"         [{i + 1}/{total}] Match {mid} ({info['home_team']} vs {info['away_team']})...",
            end=" ",
        )
        stats = fetch_match_stats(mid, info.get("page_url"))
        if stats:
            all_stats[mid] = {
                "home_team": info["home_team"],
                "away_team": info["away_team"],
                "round": info["round"],
                "stats": stats,
            }
            print("OK")
        else:
            print("no stats")
        time.sleep(0.5)

    if cache_path and all_stats:
        path = Path(cache_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(all_stats, f, indent=2)
        print(f"       Saved {len(all_stats)} match stats to {cache_path}")

    return all_stats


def load_per_match_stats(cache_path: str = None) -> dict:
    default_path = str(
        Path(__file__).parent.parent
        / "data"
        / "external"
        / "fox_sports_per_match_stats.json"
    )
    return fetch_all_match_stats(cache_path or default_path)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "ids":
        mids = fetch_match_ids()
        print(json.dumps(mids, indent=2, ensure_ascii=False))
    elif len(sys.argv) > 1 and sys.argv[1] == "match":
        mid = sys.argv[2]
        info = fetch_match_ids().get(mid, {})
        if info:
            stats = fetch_match_stats(mid, info.get("page_url"))
            print(json.dumps(stats, indent=2, ensure_ascii=False))
    else:
        stats = load_per_match_stats()
        if stats:
            print(f"Loaded {len(stats)} matches with per-match stats")
        else:
            print("Could not fetch per-match stats")
