from pathlib import Path
import yaml
from src.openfootball_client import (
    fetch_openfootball_data,
    get_final_match,
    parse_match_summary,
)
from src.wcup_client import fetch_matches, fetch_standings
from src.clean import load_openfootball, extract_goals_by_team, standings_to_df
from src.report import generate_all_plots, generate_conclusion, write_conclusion_to_file


def load_config(config_path="config.yaml"):
    with open(config_path) as f:
        return yaml.safe_load(f)


def run_pipeline(config_path="config.yaml"):
    cfg = load_config(config_path)
    base = Path(cfg["project"]["name"].lower().replace(" ", "_"))

    openfootball_cfg = cfg["data_sources"]["openfootball"]
    print("[1/6] Fetching openfootball data...")
    of_data = fetch_openfootball_data(
        openfootball_cfg["url"], openfootball_cfg["raw_path"]
    )

    final = get_final_match(of_data)
    summary = parse_match_summary(final)
    print(
        f"       Final: {summary['team1']} {summary['score_et'] or summary['score_ft']} {summary['team2']}"
    )

    print("[2/6] Loading tournament matches...")
    matches_df = load_openfootball(openfootball_cfg["raw_path"])
    matches_df.to_csv(
        Path(openfootball_cfg["raw_path"]).parent.parent
        / "processed"
        / "all_matches.csv",
        index=False,
    )
    print(f"       {len(matches_df)} matches loaded")

    print("[3/6] Extracting final goals...")
    goals_df = extract_goals_by_team(final)
    goal_strs = [f"{r.scorer} ({r.minute}')" for _, r in goals_df.iterrows()]
    print(f"       {len(goals_df)} goals: {', '.join(goal_strs)}")

    print("[4/6] Fetching standings...")
    standings = fetch_standings(openfootball_cfg["raw_path"])
    standings_df = standings_to_df(standings)
    print(
        f"       {len(standings_df)} teams across {standings_df['group'].nunique()} groups"
    )

    print("[5/6] Generating plots...")
    plot_paths = generate_all_plots(final, matches_df, standings, raw_data=of_data)

    print("[6/6] Generating conclusion...")
    conclusion = generate_conclusion(final, matches_df, standings, raw_data=of_data)
    write_conclusion_to_file(conclusion, "reports/conclusion.md")
    print(conclusion.encode("ascii", errors="replace").decode("ascii"))

    print("\n=== PIPELINE COMPLETE ===")
    print(f"  - {len(matches_df)} matches loaded")
    print(
        f"  - {len(standings_df)} teams across {standings_df['group'].nunique()} groups"
    )
    print(f"  - {len(plot_paths)} plots saved to reports/figures/")
    print(f"  - Conclusion saved to reports/conclusion.md")
    return {
        "final_match": final,
        "match_summary": summary,
        "goals": goals_df,
        "matches": matches_df,
        "standings": standings_df,
        "plots": plot_paths,
        "conclusion": conclusion,
    }


if __name__ == "__main__":
    run_pipeline()
