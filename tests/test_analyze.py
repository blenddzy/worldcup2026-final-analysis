import sys

sys.path.insert(0, ".")

import pandas as pd
import numpy as np
from src.analyze import (
    build_tournament_stats,
    match_head_to_head,
    build_team_xg_df,
    final_vs_tournament_avg,
    build_xg_table,
    conversion_efficiency,
    xg_predictor_accuracy,
)
from src.fox_sports_client import extract_nuxt_match_stats
from src.clean import extract_goals_by_team, standings_to_df


def _make_xg_fixture():
    matches = pd.DataFrame(
        {
            "team_home": ["Spain", "Spain", "Spain"],
            "team_away": ["Argentina", "France", "Germany"],
            "round": ["Final", "Semi-final", "Group stage"],
            "score_ft_home": [1, 2, 3],
            "score_ft_away": [0, 1, 0],
        }
    )
    per_match = {
        "1": {
            "home_team": "Spain",
            "away_team": "Argentina",
            "stats": {
                "expected_goals": {"home": "2.34", "away": "0.17"},
                "total_shots": {"home": "20", "away": "3"},
                "shots_on_goal": {"home": "11", "away": "0"},
                "possession": {"home": "68", "away": "32"},
            },
        },
        "2": {
            "home_team": "Spain",
            "away_team": "France",
            "stats": {
                "expected_goals": {"home": "1.50", "away": "0.80"},
                "total_shots": {"home": "14", "away": "8"},
                "shots_on_goal": {"home": "5", "away": "3"},
                "possession": {"home": "60", "away": "40"},
            },
        },
        "3": {
            "home_team": "Spain",
            "away_team": "Germany",
            "stats": {
                "expected_goals": {"home": "1.80", "away": "0.50"},
                "total_shots": {"home": "12", "away": "6"},
                "shots_on_goal": {"home": "6", "away": "2"},
                "possession": {"home": "65", "away": "35"},
            },
        },
    }
    return matches, per_match


# ── Existing tests ──


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


# ── New analytical function tests ──


def test_build_team_xg_df():
    matches, per_match = _make_xg_fixture()
    xg_df = build_team_xg_df(matches, per_match, teams=["Spain"])
    assert not xg_df.empty
    assert "team" in xg_df.columns
    assert "xG" in xg_df.columns
    assert "goals" in xg_df.columns
    assert all(xg_df["team"] == "Spain")
    assert len(xg_df) == 3
    spain_xg_total = xg_df["xG"].sum()
    assert abs(spain_xg_total - (2.34 + 1.50 + 1.80)) < 0.01


def test_final_vs_tournament_avg():
    matches, per_match = _make_xg_fixture()
    xg_df = build_team_xg_df(matches, per_match, teams=["Spain", "Argentina", "France"])
    result = final_vs_tournament_avg(xg_df, "Spain", "Argentina")
    assert result["team"] == "Spain"
    assert "possession_z" in result
    assert "xG_z" in result
    assert result["xG_final"] == 2.34
    assert result["goals_final"] == 1
    assert isinstance(result["possession_z"], float)


def test_build_xg_table():
    matches, per_match = _make_xg_fixture()
    xg_df = build_team_xg_df(matches, per_match, teams=["Spain", "Argentina"])
    table = build_xg_table(xg_df, ["Spain", "Argentina"])
    assert not table.empty
    assert "xG" in table.columns
    assert "goles" in table.columns
    assert "eficiencia_ofensiva" in table.columns
    assert "diff_goles_xg" in table.columns
    spain_row = table[table["team"] == "Spain"].iloc[0]
    assert abs(spain_row["xG"] - (2.34 + 1.50 + 1.80)) < 0.01


def test_conversion_efficiency():
    matches, per_match = _make_xg_fixture()
    xg_df = build_team_xg_df(matches, per_match, teams=["Spain", "Argentina"])
    eff = conversion_efficiency(xg_df, teams=["Spain", "Argentina"])
    assert not eff.empty
    assert "conversion_tiros" in eff.columns
    assert "eficiencia_xG" in eff.columns
    assert "sobreperformance" in eff.columns
    assert "tiros_por_gol" in eff.columns
    spain = eff[eff["team"] == "Spain"].iloc[0]
    assert spain["goles"] == 6
    assert spain["tiros"] == 46


def test_xg_predictor_accuracy():
    matches, per_match = _make_xg_fixture()
    xg_df = build_team_xg_df(matches, per_match, teams=["Spain", "Argentina", "France"])
    acc = xg_predictor_accuracy(xg_df)
    assert "accuracy_pct" in acc
    assert "correctos" in acc
    assert "total" in acc
    assert acc["total"] > 0
    assert 0 <= acc["accuracy_pct"] <= 100


# ── Parser tests ──


def test_extract_nuxt_match_stats():
    html = """
    <html><body>
    <script id="__NUXT_DATA__" type="application/json">
    ["POSSESSION (%)",{"title":0,"leftStat":2,"rightStat":3},"68","32"]
    </script>
    </body></html>
    """
    stats = extract_nuxt_match_stats(html)
    assert len(stats) == 1
    assert stats[0]["stat"] == "possession"
    assert stats[0]["home_value"] == "68"
    assert stats[0]["away_value"] == "32"


# ── Clean module tests ──


def test_extract_goals_by_team():
    match = {
        "team1": "Spain",
        "team2": "Argentina",
        "goals1": [{"name": "Ferran Torres", "minute": "106"}],
        "goals2": [],
    }
    df = extract_goals_by_team(match)
    assert len(df) == 1
    assert df.iloc[0]["team"] == "Spain"
    assert df.iloc[0]["scorer"] == "Ferran Torres"


def test_standings_to_df():
    standings = {
        "A": [
            {
                "team": "Spain",
                "p": 3,
                "w": 2,
                "d": 1,
                "l": 0,
                "gf": 5,
                "ga": 1,
                "gd": 4,
                "pts": 7,
            }
        ]
    }
    df = standings_to_df(standings)
    assert not df.empty
    assert "played" in df.columns
    assert "wins" in df.columns
    assert df.iloc[0]["team"] == "Spain"
    assert df.iloc[0]["points"] == 7
