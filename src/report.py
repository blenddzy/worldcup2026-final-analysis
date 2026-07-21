import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from src.visualize import plot_goal_timeline, plot_tournament_path, plot_group_standings
from src.analyze import route_to_final, match_head_to_head, build_tournament_stats
from src.clean import extract_goals_by_team, standings_to_df


def generate_all_plots(
    final_match: dict, matches_df, standings, output_dir="reports/figures"
):
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    print("       Generating goal timeline...")
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

    print(f"       All plots saved to {out}/")
    return [
        str(out / f)
        for f in ["goal_timeline.png", "route_to_final.png", "group_standings.png"]
    ]


def generate_conclusion(final_match: dict, matches_df, standings) -> str:
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

    spain_opponents = " -> ".join(
        f"{r['opponent']} ({r['goals_for']}-{r['goals_against']})"
        for _, r in spain_route.iterrows()
    )
    arg_opponents = " -> ".join(
        f"{r['opponent']} ({r['goals_for'] - r['goals_against']})"
        for _, r in arg_route.iterrows()
    )
    arg_opponents = " → ".join(
        f"{r['opponent']} ({r['goals_for'] - r['goals_against']})"
        for _, r in arg_route.iterrows()
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
    lines.append(
        f"- Lionel Messi (39 años) disputó su último Mundial, cerrando con 8 goles y 4 asistencias en el torneo\n"
    )
    lines.append(
        f"- Luis de la Fuente (65 años) se convirtió en el entrenador de mayor edad en ganar un Mundial\n"
    )
    lines.append(
        f"- España completó un histórico doblete Eurocopa-Mundial (tras ganar la Euro 2024)\n"
    )
    lines.append("\n")

    lines.append("## Conclusión\n")
    lines.append(
        f"La final del Mundial 2026 quedará en la historia como un partido de extrema tensión táctica, donde España demostró una solidez defensiva absoluta (cero tiros a puerta recibidos) y aprovechó la calidad de su banquillo para resolver en el momento decisivo. "
    )
    lines.append(
        f"Ferran Torres, que había tenido un torneo discreto sin goles, se convirtió en héroe nacional con un golazo en el minuto 106 que recuerda al de Iniesta en 2010.\n\n"
    )
    lines.append(
        f"Argentina, campeona defensora, plantó cara durante 105 minutos con un Emiliano Martínez inspirado, pero la expulsión de Enzo Fernández y el cansancio acumulado terminaron pesando. "
    )
    lines.append(
        f"Para Lionel Messi, fue el final de una era: se retira de la Copa del Mundo con 8 goles en su última actuación, pero sin poder repetir la gloria de 2022.\n\n"
    )
    lines.append(
        f"España no solo ganó el Mundial, sino que estableció un récord de solidez: solo **1 gol recibido en todo el torneo**, demostrando que el equilibrio defensivo puede ser tan efectivo como el juego de ataque brillante. "
    )
    lines.append(
        f"Este título, el segundo en la historia de La Roja tras el de 2010, confirma a España como una de las potencias mundiales del fútbol.\n"
    )

    return "".join(lines)


def write_conclusion_to_file(conclusion_text: str, output_path="reports/conclusion.md"):
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(conclusion_text, encoding="utf-8")
    print(f"       Conclusion saved to {out}")
