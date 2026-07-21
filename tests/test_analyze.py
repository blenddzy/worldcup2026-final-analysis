import sys

sys.path.insert(0, ".")

import pandas as pd
from src.analyze import build_tournament_stats, match_head_to_head


def test_build_tournament_stats():
    df = pd.DataFrame(
        {
            "team_home": ["Spain", "Spain"],
            "team_away": ["Argentina", "France"],
            "score_ft_home": [1, 2],
            "score_ft_away": [0, 1],
        }
    )
    stats = build_tournament_stats(df)
    assert "team" in stats.columns
    assert "gf" in stats.columns
    assert "ga" in stats.columns
    spain = stats[stats["team"] == "Spain"].iloc[0]
    assert spain["gf"] == 3
    assert spain["ga"] == 1


def test_match_head_to_head():
    match = {
        "team1": "Spain",
        "team2": "Argentina",
        "score": {"et": [1, 0], "ft": [0, 0], "ht": [0, 0]},
        "goals1": [{"name": "Ferran Torres", "minute": "106"}],
        "goals2": [],
    }
    result = match_head_to_head(match)
    assert result["winner"] == "home"
    assert result["home_goals"] == 1
    assert result["away_goals"] == 0
    assert "Ferran Torres" in result["scorers_home"][0]
