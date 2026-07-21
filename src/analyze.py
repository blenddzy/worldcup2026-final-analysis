import pandas as pd
import numpy as np


def build_tournament_stats(matches_df: pd.DataFrame) -> pd.DataFrame:
    home = matches_df[["team_home", "score_ft_home", "score_ft_away"]].rename(
        columns={"team_home": "team", "score_ft_home": "gf", "score_ft_away": "ga"}
    )
    away = matches_df[["team_away", "score_ft_away", "score_ft_home"]].rename(
        columns={"team_away": "team", "score_ft_away": "gf", "score_ft_home": "ga"}
    )
    all_games = pd.concat([home, away], ignore_index=True)
    all_games = all_games.dropna(subset=["gf"])

    stats = (
        all_games.groupby("team")
        .agg(
            played=("gf", "count"),
            gf=("gf", "sum"),
            ga=("ga", "sum"),
            avg_gf=("gf", "mean"),
            avg_ga=("ga", "mean"),
        )
        .reset_index()
    )
    stats["gd"] = stats["gf"] - stats["ga"]
    return stats.sort_values("gd", ascending=False)


def route_to_final(matches_df: pd.DataFrame, team: str) -> pd.DataFrame:
    mask = (matches_df["team_home"] == team) | (matches_df["team_away"] == team)
    team_matches = matches_df[mask].copy()
    team_matches["opponent"] = team_matches.apply(
        lambda r: r["team_away"] if r["team_home"] == team else r["team_home"],
        axis=1,
    )
    team_matches["goals_for"] = team_matches.apply(
        lambda r: r["score_ft_home"] if r["team_home"] == team else r["score_ft_away"],
        axis=1,
    )
    team_matches["goals_against"] = team_matches.apply(
        lambda r: r["score_ft_away"] if r["team_home"] == team else r["score_ft_home"],
        axis=1,
    )
    knockout_rounds = [
        "Round of 32",
        "Round of 16",
        "Quarter-final",
        "Semi-final",
        "Final",
    ]
    team_matches["round_order"] = team_matches["round"].apply(
        lambda r: knockout_rounds.index(r) if r in knockout_rounds else -1
    )
    return team_matches.sort_values("round_order")


def match_head_to_head(match: dict) -> dict:
    score = match.get("score", {})
    return {
        "home_team": match.get("team1"),
        "away_team": match.get("team2"),
        "home_goals": score.get("et", [None, None])[0]
        or score.get("ft", [None, None])[0],
        "away_goals": score.get("et", [None, None])[1]
        or score.get("ft", [None, None])[1],
        "home_goals_ht": score.get("ht", [None, None])[0],
        "away_goals_ht": score.get("ht", [None, None])[1],
        "winner": (
            "home"
            if (score.get("et", [None, None])[0] or score.get("ft", [None, None])[0])
            > (score.get("et", [None, None])[1] or score.get("ft", [None, None])[1])
            else "away"
        ),
        "scorers_home": [
            f"{g['name']} ({g['minute']}')" for g in match.get("goals1", [])
        ],
        "scorers_away": [
            f"{g['name']} ({g['minute']}')" for g in match.get("goals2", [])
        ],
    }


def extract_team_scorers(raw_data: dict, team: str) -> pd.DataFrame:
    rows = []
    for match in raw_data.get("matches", []):
        t1, t2 = match.get("team1"), match.get("team2")
        if t1 == team:
            for g in match.get("goals1", []):
                rows.append(
                    {
                        "scorer": g["name"],
                        "minute": g.get("minute"),
                        "opponent": t2,
                        "round": match.get("round"),
                    }
                )
        if t2 == team:
            for g in match.get("goals2", []):
                rows.append(
                    {
                        "scorer": g["name"],
                        "minute": g.get("minute"),
                        "opponent": t1,
                        "round": match.get("round"),
                    }
                )
    return pd.DataFrame(rows)


def build_tournament_top_scorers(raw_data: dict, top_n: int = 20) -> pd.DataFrame:
    rows = []
    for match in raw_data.get("matches", []):
        for side in ["goals1", "goals2"]:
            for g in match.get(side, []):
                team = match["team1"] if side == "goals1" else match["team2"]
                rows.append(
                    {
                        "scorer": g["name"],
                        "team": team,
                        "minute": g.get("minute"),
                        "round": match.get("round"),
                    }
                )
    df = pd.DataFrame(rows)
    return (
        df.groupby(["scorer", "team"])
        .size()
        .reset_index(name="goals")
        .sort_values("goals", ascending=False)
        .head(top_n)
    )


def generate_synthetic_match_stats(
    matches_df: pd.DataFrame, teams: list[str]
) -> pd.DataFrame:
    np.random.seed(42)
    rows = []
    team_style = {
        "Spain": {"poss_base": 62, "poss_std": 5, "shots_base": 14, "shots_std": 4},
        "Argentina": {"poss_base": 55, "poss_std": 4, "shots_base": 13, "shots_std": 3},
    }
    for _, m in matches_df.iterrows():
        for team in teams:
            if team not in (m["team_home"], m["team_away"]):
                continue
            style = team_style.get(
                team, {"poss_base": 50, "poss_std": 5, "shots_base": 10, "shots_std": 3}
            )
            possession = max(
                35,
                min(75, int(np.random.normal(style["poss_base"], style["poss_std"]))),
            )
            shots = max(
                3, int(np.random.normal(style["shots_base"], style["shots_std"]))
            )
            shots_on_target = max(1, int(shots * np.random.uniform(0.3, 0.55)))
            opponent = m["team_away"] if team == m["team_home"] else m["team_home"]
            goals = m["score_ft_home"] if team == m["team_home"] else m["score_ft_away"]
            goals_conceded = (
                m["score_ft_away"] if team == m["team_home"] else m["score_ft_home"]
            )
            rows.append(
                {
                    "team": team,
                    "opponent": opponent,
                    "round": m["round"],
                    "possession": possession,
                    "shots": shots,
                    "shots_on_target": shots_on_target,
                    "goals": goals,
                    "goals_conceded": goals_conceded,
                    "corners": max(0, int(possession / 15 + np.random.normal(0, 2))),
                    "fouls": max(3, int(20 - possession / 5 + np.random.normal(0, 3))),
                }
            )
    return pd.DataFrame(rows)
