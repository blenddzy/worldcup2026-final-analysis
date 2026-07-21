import json
import pandas as pd
from pathlib import Path


def load_openfootball(path: str) -> pd.DataFrame:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    rows = []
    for match in data.get("matches", []):
        score = match.get("score", {})
        rows.append(
            {
                "round": match.get("round"),
                "num": match.get("num"),
                "date": match.get("date"),
                "time": match.get("time"),
                "team_home": match.get("team1"),
                "team_away": match.get("team2"),
                "score_ht_home": score.get("ht", [None, None])[0],
                "score_ht_away": score.get("ht", [None, None])[1],
                "score_ft_home": score.get("ft", [None, None])[0],
                "score_ft_away": score.get("ft", [None, None])[1],
                "score_et_home": score.get("et", [None, None])[0],
                "score_et_away": score.get("et", [None, None])[1],
                "venue": match.get("ground"),
            }
        )
    return pd.DataFrame(rows)


def extract_goals_by_team(match: dict) -> pd.DataFrame:
    rows = []
    for side, team_name in [("goals1", match["team1"]), ("goals2", match["team2"])]:
        for goal in match.get(side, []):
            rows.append(
                {
                    "team": team_name,
                    "scorer": goal.get("name"),
                    "minute": goal.get("minute"),
                }
            )
    return pd.DataFrame(rows)


def standings_to_df(standings: dict) -> pd.DataFrame:
    rows = []
    for group, teams in standings.items():
        for t in teams:
            t["group"] = group
            rows.append(t)
    return pd.DataFrame(rows).rename(
        columns={
            "team": "team",
            "p": "played",
            "w": "wins",
            "d": "draws",
            "l": "losses",
            "gf": "goals_for",
            "ga": "goals_against",
            "gd": "goal_diff",
            "pts": "points",
        }
    )
