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
