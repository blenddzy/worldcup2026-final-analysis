import json
from pathlib import Path

import pandas as pd
import numpy as np

from src.fox_sports_client import load_per_match_stats as _load_per_match_stats


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


def load_real_team_stats(stats_path: str = "") -> dict:
    if stats_path:
        path = Path(stats_path)
    else:
        path = (
            Path(__file__).parent.parent
            / "data"
            / "external"
            / "fox_sports_team_stats.json"
        )
    if path.exists():
        with open(path) as f:
            raw = json.load(f)
        stats = {}
        for team in ["Spain", "Argentina"]:
            team_data = raw.get(team, {})
            stats[team] = {}
            for abbr, info in team_data.items():
                stats[team][abbr] = info["value"]
        return stats
    return {}


def _get_team_stats_from_fox(match, team, per_match_stats):
    """Extrae estadísticas reales de Fox Sports para un equipo en un partido."""
    if not per_match_stats:
        return None
    is_home = match["team_home"] == team
    for mdata in per_match_stats.values():
        if (
            mdata["home_team"] == match["team_home"]
            and mdata["away_team"] == match["team_away"]
        ):
            side = "home" if is_home else "away"
            result = {}
            for k, v in mdata["stats"].items():
                try:
                    result[k] = float(v[side])
                except (ValueError, TypeError):
                    result[k] = v[side]
            return result
    return None


def build_team_xg_df(matches_df, per_match_stats, teams=None):
    """Construye DataFrame con xG, goles, tiros por equipo para todo el torneo."""
    rows = []
    for _, m in matches_df.iterrows():
        for team in [m["team_home"], m["team_away"]]:
            if teams and team not in teams:
                continue
            real = _get_team_stats_from_fox(m, team, per_match_stats)
            if not real:
                continue
            is_home = m["team_home"] == team
            xg = real.get("expected_goals", 0)
            shots = real.get("total_shots", 0)
            sot = real.get("shots_on_goal", 0)
            poss = real.get("possession", 50)
            goals = float(m["score_ft_home"] if is_home else m["score_ft_away"])
            goals_conceded = float(
                m["score_ft_away"] if is_home else m["score_ft_home"]
            )
            rows.append(
                {
                    "team": team,
                    "opponent": m["team_away"] if is_home else m["team_home"],
                    "round": m["round"],
                    "xG": xg,
                    "goals": goals,
                    "goals_conceded": goals_conceded,
                    "shots": shots,
                    "shots_on_target": sot,
                    "possession": poss,
                }
            )
    return pd.DataFrame(rows)


def final_vs_tournament_avg(
    xg_df: pd.DataFrame, team: str, final_opponent: str
) -> dict:
    """Compara rendimiento de un equipo en la final vs su promedio del torneo."""
    team_df = xg_df[xg_df["team"] == team].copy()
    if team_df.empty:
        return {}
    final_mask = (team_df["opponent"] == final_opponent) & (team_df["round"] == "Final")
    final_row = team_df[final_mask]
    if final_row.empty:
        final_row = team_df[team_df["opponent"] == final_opponent].tail(1)
    tourney = team_df[~final_mask]
    if tourney.empty or final_row.empty:
        return {}
    metrics = ["possession", "shots", "shots_on_target", "xG", "goals"]
    result = {"team": team, "final_opponent": final_opponent}
    for m in metrics:
        avg = float(tourney[m].mean())
        std = float(tourney[m].std()) if len(tourney) > 1 else 0
        final_val = float(final_row[m].iloc[0])
        z = (final_val - avg) / std if std > 0 else 0
        result[f"{m}_avg"] = round(avg, 2)
        result[f"{m}_final"] = round(final_val, 2)
        result[f"{m}_z"] = round(z, 2)
    return result


def build_xg_table(xg_df: pd.DataFrame, teams: list) -> pd.DataFrame:
    """Tabla de xG vs goles reales para equipos dados (ej. semifinalistas)."""
    rows = []
    for team in teams:
        tdf = xg_df[xg_df["team"] == team]
        if tdf.empty:
            continue
        total_xg = tdf["xG"].sum()
        total_goals = tdf["goals"].sum()
        total_xga = tdf["goals_conceded"].sum()
        total_ga = tdf["goals_conceded"].sum()
        n = len(tdf)
        conv = round(total_goals / total_xg, 3) if total_xg > 0 else 0
        rows.append(
            {
                "team": team,
                "partidos": n,
                "xG": round(total_xg, 2),
                "goles": int(total_goals),
                "diff_goles_xg": round(total_goals - total_xg, 2),
                "xG_por_partido": round(total_xg / n, 2) if n else 0,
                "goles_por_partido": round(total_goals / n, 2) if n else 0,
                "eficiencia_ofensiva": conv,
                "goles_recibidos": int(total_ga),
            }
        )
    return pd.DataFrame(rows).sort_values("diff_goles_xg", ascending=False)


def conversion_efficiency(xg_df: pd.DataFrame, teams: list = None) -> pd.DataFrame:
    """Métrica de eficiencia de conversión por equipo."""
    if teams:
        tdf = xg_df[xg_df["team"].isin(teams)]
    else:
        tdf = xg_df
    grouped = (
        tdf.groupby("team")
        .agg(
            partidos=("xG", "count"),
            goles=("goals", "sum"),
            xG=("xG", "sum"),
            tiros=("shots", "sum"),
            tiros_arco=("shots_on_target", "sum"),
        )
        .reset_index()
    )
    grouped["conversion_tiros"] = round(grouped["goles"] / grouped["tiros"] * 100, 1)
    grouped["conversion_tiros_arco"] = round(
        grouped["goles"] / grouped["tiros_arco"] * 100, 1
    )
    grouped["eficiencia_xG"] = round(grouped["goles"] / grouped["xG"], 3)
    grouped["sobreperformance"] = round(grouped["goles"] - grouped["xG"], 2)
    grouped["tiros_por_gol"] = round(grouped["tiros"] / grouped["goles"], 1)
    grouped["xG_por_tiro"] = round(grouped["xG"] / grouped["tiros"], 3)
    return grouped.sort_values("sobreperformance", ascending=False)


def xg_predictor_accuracy(xg_df: pd.DataFrame) -> dict:
    """Evalúa qué tan seguido el equipo con mayor xG ganó el partido."""
    correct = 0
    total = 0
    by_round = {}
    for _, m in xg_df.iterrows():
        team = m["team"]
        opp = m["opponent"]
        rnd = m["round"]
        opp_row = xg_df[
            (xg_df["team"] == opp)
            & (xg_df["opponent"] == team)
            & (xg_df["round"] == rnd)
        ]
        if opp_row.empty:
            continue
        opp_xg = opp_row["xG"].iloc[0]
        team_goals = m["goals"]
        opp_goals = opp_row["goals"].iloc[0]
        if m["xG"] > opp_xg:
            predicted = team
            predicted_won = team_goals > opp_goals
        elif opp_xg > m["xG"]:
            predicted = opp
            predicted_won = opp_goals > team_goals
        else:
            predicted_won = team_goals == opp_goals
        actual_winner = (
            team
            if team_goals > opp_goals
            else (opp if opp_goals > team_goals else "draw")
        )
        if predicted_won or actual_winner == "draw":
            correct += 1
        total += 1
        by_round[rnd] = by_round.get(rnd, {"correct": 0, "total": 0})
        if predicted_won or actual_winner == "draw":
            by_round[rnd]["correct"] += 1
        by_round[rnd]["total"] += 1
    accuracy = round(correct / total * 100, 1) if total else 0
    by_round_summary = {
        r: round(v["correct"] / v["total"] * 100, 1)
        for r, v in sorted(by_round.items())
    }
    return {
        "accuracy_pct": accuracy,
        "correctos": correct,
        "total": total,
        "por_ronda": by_round_summary,
    }


def generate_synthetic_match_stats(
    matches_df: pd.DataFrame,
    teams: list[str],
    real_baselines: dict = None,
    real_match_stats: dict = None,
) -> pd.DataFrame:  # type: ignore[arg-type]
    np.random.seed(42)
    rows = []
    team_style = {
        "Spain": {"poss_base": 62, "poss_std": 5, "shots_base": 14, "shots_std": 4},
        "Argentina": {"poss_base": 55, "poss_std": 4, "shots_base": 13, "shots_std": 3},
    }
    corners_per_game = {}
    if real_baselines:
        for team in teams:
            tdata = real_baselines.get(team, {})
            style = team_style.get(team, {})
            if "POSS" in tdata:
                style["poss_base"] = int(tdata["POSS"])
            if "CK" in tdata:
                ck_total = int(tdata["CK"])
                n_matches = len(
                    matches_df[
                        (matches_df["team_home"] == team)
                        | (matches_df["team_away"] == team)
                    ]
                )
                corners_per_game[team] = ck_total / max(n_matches, 1)

    def _get_real(match, team):
        if not real_match_stats:
            return None
        is_home = match["team_home"] == team
        for mid, mdata in real_match_stats.items():
            if (
                mdata["home_team"] == match["team_home"]
                and mdata["away_team"] == match["team_away"]
            ):
                side = "home" if is_home else "away"
                return {
                    k: float(v[side])
                    if v[side].replace(".", "").replace("-", "").isdigit()
                    else v[side]
                    for k, v in mdata["stats"].items()
                }
        return None

    for _, m in matches_df.iterrows():
        for team in teams:
            if team not in (m["team_home"], m["team_away"]):
                continue
            style = team_style.get(
                team, {"poss_base": 50, "poss_std": 5, "shots_base": 10, "shots_std": 3}
            )
            real = _get_real(m, team)
            possession = max(
                35,
                min(75, int(np.random.normal(style["poss_base"], style["poss_std"]))),
            )
            if real and "possession" in real:
                possession = int(real["possession"])
            shots = max(
                3, int(np.random.normal(style["shots_base"], style["shots_std"]))
            )
            if real and "total_shots" in real:
                shots = int(real["total_shots"])
            shots_on_target = max(1, int(shots * np.random.uniform(0.3, 0.55)))
            if real and "shots_on_goal" in real:
                shots_on_target = int(real["shots_on_goal"])
            opponent = m["team_away"] if team == m["team_home"] else m["team_home"]
            goals = m["score_ft_home"] if team == m["team_home"] else m["score_ft_away"]
            goals_conceded = (
                m["score_ft_away"] if team == m["team_home"] else m["score_ft_home"]
            )
            if real and "corners" in real:
                corners = int(real["corners"])
            elif real_baselines:
                tdata = real_baselines.get(team, {})
                ck_per_game = corners_per_game.get(team, 4.5)
                corners = max(0, int(np.random.normal(ck_per_game, 2)))
            else:
                corners = max(0, int(possession / 15 + np.random.normal(0, 2)))
            fouls = max(3, int(20 - possession / 5 + np.random.normal(0, 3)))
            if real and "fouls" in real:
                fouls = int(real["fouls"])
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
                    "corners": corners,
                    "fouls": fouls,
                    "source": "real" if real else "synthetic",
                }
            )
    return pd.DataFrame(rows)
