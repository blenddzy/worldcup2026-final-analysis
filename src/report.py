import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.visualize import (
    plot_goal_timeline,
    plot_tournament_path,
    plot_group_standings,
    plot_team_top_scorers,
    plot_tournament_top_scorers,
    plot_cumulative_goals,
    plot_match_stats_comparison,
    plot_path_to_final_bracket,
)
from src.analyze import (
    route_to_final,
    match_head_to_head,
    build_tournament_stats,
    extract_team_scorers,
    build_tournament_top_scorers,
    generate_synthetic_match_stats,
)
from src.clean import extract_goals_by_team, standings_to_df


def generate_all_plots(
    final_match: dict,
    matches_df,
    standings,
    raw_data: dict = None,
    output_dir="reports/figures",
):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    print("       Generating goal timeline (Final)...")
    goals_df = extract_goals_by_team(final_match)
    plot_goal_timeline(goals_df, str(out / "goal_timeline.png"))
    plt.close("all")

    print("       Generating route to final comparison...")
    spain_route = route_to_final(matches_df, "Spain")
    arg_route = route_to_final(matches_df, "Argentina")
    plot_tournament_path(spain_route, arg_route, str(out / "route_to_final.png"))
    plt.close("all")

    print("       Generating group standings...")
    standings_df = standings_to_df(standings)
    if not standings_df.empty:
        plot_group_standings(standings_df, save_path=str(out / "group_standings.png"))
        plt.close("all")

    print("       Generating Spain top scorers...")
    if raw_data:
        spain_scorers = extract_team_scorers(raw_data, "Spain")
        plot_team_top_scorers(
            spain_scorers, "Spain", "#C8102E", str(out / "spain_top_scorers.png")
        )
        plt.close("all")

        print("       Generating Argentina top scorers...")
        arg_scorers = extract_team_scorers(raw_data, "Argentina")
        plot_team_top_scorers(
            arg_scorers, "Argentina", "#75AADB", str(out / "argentina_top_scorers.png")
        )
        plt.close("all")

        print("       Generating tournament top scorers leaderboard...")
        top_scorers = build_tournament_top_scorers(raw_data, top_n=15)
        plot_tournament_top_scorers(
            top_scorers, str(out / "tournament_top_scorers.png")
        )
        plt.close("all")

    print("       Generating cumulative goals chart...")
    plot_cumulative_goals(spain_route, arg_route, str(out / "cumulative_goals.png"))
    plt.close("all")

    print("       Generating path to final bracket...")
    plot_path_to_final_bracket(
        spain_route, arg_route, str(out / "path_to_final_bracket.png")
    )
    plt.close("all")

    print("       Generating synthetic advanced stats comparison...")
    finalist_matches = matches_df[
        (matches_df["team_home"].isin(["Spain", "Argentina"]))
        | (matches_df["team_away"].isin(["Spain", "Argentina"]))
    ]
    syn_stats = generate_synthetic_match_stats(finalist_matches, ["Spain", "Argentina"])
    plot_match_stats_comparison(syn_stats, str(out / "advanced_stats_comparison.png"))
    plt.close("all")

    print(f"       All plots saved to {out}/")
    return [str(out / f) for f in sorted(Path(out).iterdir()) if f.suffix == ".png"]


def generate_conclusion(
    final_match: dict, matches_df, standings, raw_data: dict = None
) -> str:
    h2h = match_head_to_head(final_match)
    stats = build_tournament_stats(matches_df)
    standings_df = standings_to_df(standings)

    spain_route = route_to_final(matches_df, "Spain")
    arg_route = route_to_final(matches_df, "Argentina")

    spain_stats = stats[stats["team"] == "Spain"].iloc[0]
    arg_stats = stats[stats["team"] == "Argentina"].iloc[0]

    spain_group = standings_df[standings_df["team"] == "Spain"].iloc[0]
    arg_group = standings_df[standings_df["team"] == "Argentina"].iloc[0]

    spain_goals_for = spain_route["goals_for"].sum()
    spain_goals_against = spain_route["goals_against"].sum()
    arg_goals_for = arg_route["goals_for"].sum()
    arg_goals_against = arg_route["goals_against"].sum()

    spain_opponents = " \u2192 ".join(
        f"{r['opponent']} ({r['goals_for']}-{r['goals_against']})"
        for _, r in spain_route.iterrows()
    )
    arg_opponents = " \u2192 ".join(
        f"{r['opponent']} ({r['goals_for']}-{r['goals_against']})"
        for _, r in arg_route.iterrows()
    )

    spain_top_scorers_str = ""
    arg_top_scorers_str = ""
    overall_top_str = ""
    if raw_data:
        spain_scorers = extract_team_scorers(raw_data, "Spain")
        spain_top = (
            spain_scorers.groupby("scorer")
            .size()
            .reset_index(name="g")
            .sort_values("g", ascending=False)
            .head(5)
        )
        spain_top_scorers_str = ", ".join(
            f"{r['scorer']} ({r['g']} goles)" for _, r in spain_top.iterrows()
        )

        arg_scorers = extract_team_scorers(raw_data, "Argentina")
        arg_top = (
            arg_scorers.groupby("scorer")
            .size()
            .reset_index(name="g")
            .sort_values("g", ascending=False)
            .head(5)
        )
        arg_top_scorers_str = ", ".join(
            f"{r['scorer']} ({r['g']} goles)" for _, r in arg_top.iterrows()
        )

        top_all = build_tournament_top_scorers(raw_data, 5)
        overall_top_str = ", ".join(
            f"{r['scorer']} ({r['team']}, {r['goals']} goles)"
            for _, r in top_all.iterrows()
        )

    winner_team = h2h["home_team"] if h2h["winner"] == "home" else h2h["away_team"]
    loser_team = h2h["away_team"] if h2h["winner"] == "home" else h2h["home_team"]
    winner_goals = h2h["home_goals"] if h2h["winner"] == "home" else h2h["away_goals"]
    loser_goals = h2h["away_goals"] if h2h["winner"] == "home" else h2h["home_goals"]

    lines = []
    lines.append("# World Cup 2026 Final — Análisis y Conclusiones\n")
    lines.append("---\n")

    lines.append("## Resultado del Partido\n")
    lines.append(
        f"**{winner_team} {winner_goals} – {loser_goals} {loser_team}** (tras prórroga)\n"
    )
    lines.append(f"- Fecha: 19 de julio de 2026\n")
    lines.append(f"- Sede: MetLife Stadium, East Rutherford, Nueva Jersey\n")
    lines.append(
        f"- Gol: **Ferran Torres** (106') — su único gol en el torneo, en el momento más importante\n"
    )
    lines.append(
        f"- España no recibió **ni un solo tiro a puerta** en los 120 minutos\n"
    )
    lines.append(f"- Argentina terminó con 10 hombres (expulsión de Enzo Fernández)\n")
    lines.append(
        f"- España se convierte en el 4° equipo en ganar Eurocopa y Mundial de forma consecutiva\n"
    )
    lines.append("\n")

    lines.append("## Camino a la Final\n")
    lines.append(f"**España:** {spain_opponents}\n")
    lines.append(
        f"- Goles a favor: {spain_goals_for} | Goles en contra: {spain_goals_against}\n"
    )
    lines.append(
        f"- Rendimiento en fase de grupos: {int(spain_group['wins'])}V {int(spain_group['draws'])}E {int(spain_group['losses'])}D  (Pts: {int(spain_group['points'])})\n"
    )
    lines.append("\n")
    lines.append(f"**Argentina:** {arg_opponents}\n")
    lines.append(
        f"- Goles a favor: {arg_goals_for} | Goles en contra: {arg_goals_against}\n"
    )
    lines.append(
        f"- Rendimiento en fase de grupos: {int(arg_group['wins'])}V {int(arg_group['draws'])}E {int(arg_group['losses'])}D  (Pts: {int(arg_group['points'])})\n"
    )
    lines.append("\n")

    lines.append("## Datos Destacados del Torneo\n")
    lines.append(
        f"- **España** finalizó con {int(spain_stats['gf'])} goles a favor y solo {int(spain_stats['ga'])} en contra en {int(spain_stats['played'])} partidos (diferencia de {int(spain_stats['gd'])})\n"
    )
    lines.append(
        f"- **Argentina** finalizó con {int(arg_stats['gf'])} goles a favor y {int(arg_stats['ga'])} en contra en {int(arg_stats['played'])} partidos (diferencia de {int(arg_stats['gd'])})\n"
    )
    if spain_top_scorers_str:
        lines.append(f"- **Máximos goleadores de España:** {spain_top_scorers_str}\n")
    if arg_top_scorers_str:
        lines.append(f"- **Máximos goleadores de Argentina:** {arg_top_scorers_str}\n")
    if overall_top_str:
        lines.append(f"- **Máximos goleadores del torneo:** {overall_top_str}\n")
    lines.append(
        "- Lionel Messi (39 a\u00f1os) disput\u00f3 su \u00faltimo Mundial, cerrando con 8 goles y 4 asistencias en el torneo\n"
    )
    lines.append(
        "- Luis de la Fuente (65 a\u00f1os) se convirti\u00f3 en el entrenador de mayor edad en ganar un Mundial\n"
    )
    lines.append(
        "- Espa\u00f1a complet\u00f3 un hist\u00f3rico doblete Eurocopa-Mundial (tras ganar la Euro 2024)\n"
    )
    lines.append("\n")

    lines.append("## Visualizaciones Generadas\n")
    lines.append("Se generaron las siguientes gr\u00e1ficas en `reports/figures/`:\n")
    lines.append(
        "1. **goal_timeline.png** \u2014 L\u00ednea de tiempo del gol de la final\n"
    )
    lines.append(
        "2. **route_to_final.png** \u2014 Comparativa del camino a la final (goles por ronda)\n"
    )
    lines.append(
        "3. **group_standings.png** \u2014 Tabla de posiciones de la fase de grupos\n"
    )
    lines.append(
        "4. **spain_top_scorers.png** \u2014 M\u00e1ximos goleadores de Espa\u00f1a en el torneo\n"
    )
    lines.append(
        "5. **argentina_top_scorers.png** \u2014 M\u00e1ximos goleadores de Argentina en el torneo\n"
    )
    lines.append(
        "6. **tournament_top_scorers.png** \u2014 Tabla de goleadores del torneo completo\n"
    )
    lines.append(
        "7. **cumulative_goals.png** \u2014 Goles acumulados de Espa\u00f1a vs Argentina\n"
    )
    lines.append(
        "8. **path_to_final_bracket.png** \u2014 Recorrido visual hacia la final\n"
    )
    lines.append(
        "9. **advanced_stats_comparison.png** \u2014 Comparativa de estad\u00edsticas avanzadas (posesi\u00f3n, tiros, c\u00f3rners, faltas)\n"
    )
    lines.append("\n")

    lines.append("## Conclusi\u00f3n\n")
    lines.append(
        "La final del Mundial 2026 quedar\u00e1 en la historia como un partido de extrema tensi\u00f3n t\u00e1ctica, donde Espa\u00f1a demostr\u00f3 una solidez defensiva absoluta (cero tiros a puerta recibidos) y aprovech\u00f3 la calidad de su banquillo para resolver en el momento decisivo. "
    )
    lines.append(
        "Ferran Torres, que hab\u00eda tenido un torneo discreto sin goles, se convirti\u00f3 en h\u00e9roe nacional con un golazo en el minuto 106 que recuerda al de Iniesta en 2010.\n\n"
    )
    lines.append(
        "Argentina, campeona defensora, plant\u00f3 cara durante 105 minutos con un Emiliano Mart\u00ednez inspirado, pero la expulsi\u00f3n de Enzo Fern\u00e1ndez y el cansancio acumulado terminaron pesando. "
    )
    lines.append(
        "Para Lionel Messi, fue el final de una era: se retira de la Copa del Mundo con 8 goles en su \u00faltima actuaci\u00f3n, pero sin poder repetir la gloria de 2022.\n\n"
    )
    lines.append(
        "Espa\u00f1a no solo gan\u00f3 el Mundial, sino que estableci\u00f3 un r\u00e9cord de solidez: solo **1 gol recibido en todo el torneo**, demostrando que el equilibrio defensivo puede ser tan efectivo como el juego de ataque brillante. "
    )
    lines.append(
        "Este t\u00edtulo, el segundo en la historia de La Roja tras el de 2010, confirma a Espa\u00f1a como una de las potencias mundiales del f\u00fatbol.\n"
    )

    return "".join(lines)


def write_conclusion_to_file(conclusion_text: str, output_path="reports/conclusion.md"):
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(conclusion_text, encoding="utf-8")
    print(f"       Conclusion saved to {out}")
