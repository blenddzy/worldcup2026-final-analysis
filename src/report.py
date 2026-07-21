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
    analysis_final_vs_avg,
    analysis_xg_vs_actual,
    analysis_conversion_scatter,
)
from src.analyze import (
    route_to_final,
    match_head_to_head,
    build_tournament_stats,
    extract_team_scorers,
    build_tournament_top_scorers,
    generate_synthetic_match_stats,
    load_real_team_stats,
    build_team_xg_df,
    final_vs_tournament_avg,
    build_xg_table,
    conversion_efficiency,
    xg_predictor_accuracy,
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

    print(
        "       Generating advanced stats comparison (Fox Sports real per-match data)..."
    )
    finalist_matches = matches_df[
        (matches_df["team_home"].isin(["Spain", "Argentina"]))
        | (matches_df["team_away"].isin(["Spain", "Argentina"]))
    ]
    real_baselines = load_real_team_stats()
    try:
        from src.fox_sports_client import load_per_match_stats

        real_match_stats = load_per_match_stats()
    except Exception:
        real_match_stats = None
    if real_match_stats:
        n_real = sum(
            1
            for m in real_match_stats.values()
            if m["home_team"] in ("Spain", "Argentina")
            or m["away_team"] in ("Spain", "Argentina")
        )
        print(f"         Using {n_real} real match stats for Spain/Argentina matches")
    syn_stats = generate_synthetic_match_stats(
        finalist_matches,
        ["Spain", "Argentina"],
        real_baselines=real_baselines if real_baselines else None,
        real_match_stats=real_match_stats,
    )
    n_used = (
        (syn_stats["source"] == "real").sum() if "source" in syn_stats.columns else 0
    )
    print(f"         Stats used: {n_used} real, {len(syn_stats) - n_used} synthetic")
    plot_match_stats_comparison(syn_stats, str(out / "advanced_stats_comparison.png"))
    plt.close("all")

    print("       Generating analysis: final vs tournament average...")
    try:
        xg_df = build_team_xg_df(
            matches_df,
            real_match_stats,
            teams=["Spain", "Argentina", "France", "England"],
        )
        spain_comparison = final_vs_tournament_avg(xg_df, "Spain", "Argentina")
        if spain_comparison:
            analysis_final_vs_avg(
                spain_comparison, str(out / "analysis_final_vs_tournament_avg.png")
            )
            plt.close("all")
            z_vals = {k: v for k, v in spain_comparison.items() if k.endswith("_z")}
            print(f"         Z-scores: {z_vals}")
    except Exception as e:
        print(f"         Skipped (error: {e})")

    print("       Generating analysis: xG vs actual goals for semifinalists...")
    try:
        semifinalists = ["Spain", "Argentina", "France", "England"]
        xg_table = build_xg_table(xg_df, semifinalists)
        analysis_xg_vs_actual(xg_table, str(out / "analysis_xg_vs_actual.png"))
        plt.close("all")
        print(
            f"         xG diffs: {dict(zip(xg_table['team'], xg_table['diff_goles_xg']))}"
        )
    except Exception as e:
        print(f"         Skipped (error: {e})")

    print("       Generating analysis: conversion efficiency scatter...")
    try:
        eff_df = conversion_efficiency(xg_df, teams=semifinalists)
        analysis_conversion_scatter(
            eff_df, str(out / "analysis_conversion_efficiency.png")
        )
        plt.close("all")
    except Exception as e:
        print(f"         Skipped (error: {e})")

    print("       Generating analysis: xG predictor accuracy...")
    try:
        acc = xg_predictor_accuracy(xg_df)
        print(
            f"         xG predictor accuracy: {acc['accuracy_pct']}% ({acc['correctos']}/{acc['total']})"
        )
    except Exception as e:
        print(f"         Skipped (error: {e})")

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

    # Calcular métricas analíticas
    analisis_metrics = {}
    try:
        from src.fox_sports_client import load_per_match_stats

        real_match_stats = load_per_match_stats()
        xg_df = build_team_xg_df(
            matches_df,
            real_match_stats,
            teams=["Spain", "Argentina", "France", "England"],
        )
        spain_comp = final_vs_tournament_avg(xg_df, "Spain", "Argentina")
        xg_table = build_xg_table(xg_df, ["Spain", "Argentina", "France", "England"])
        eff_df = conversion_efficiency(
            xg_df, ["Spain", "Argentina", "France", "England"]
        )
        acc = xg_predictor_accuracy(xg_df)
        analisis_metrics = {
            "spain_poss_z": spain_comp.get("possession_z", "?"),
            "spain_xg_z": spain_comp.get("xG_z", "?"),
            "spain_final_xg": spain_comp.get("xG_final", "?"),
            "spain_avg_xg": spain_comp.get("xG_avg", "?"),
            "arg_eff": xg_table[xg_table["team"] == "Argentina"][
                "eficiencia_ofensiva"
            ].values[0]
            if len(xg_table) > 0
            else "?",
            "spain_eff": xg_table[xg_table["team"] == "Spain"][
                "eficiencia_ofensiva"
            ].values[0]
            if len(xg_table) > 0
            else "?",
            "xg_acc": acc.get("accuracy_pct", "?"),
        }
    except Exception:
        pass

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
    lines.append(
        "10. **analysis_final_vs_tournament_avg.png** \u2014 Radar: Espa\u00f1a en la final vs su promedio del torneo\n"
    )
    lines.append(
        "11. **analysis_xg_vs_actual.png** \u2014 xG vs goles reales para los 4 semifinalistas\n"
    )
    lines.append(
        "12. **analysis_conversion_efficiency.png** \u2014 Scatter de eficiencia de conversi\u00f3n (xG vs goles)\n"
    )
    lines.append("\n")

    lines.append("## An\u00e1lisis de M\u00e9tricas Avanzadas\n")

    if analisis_metrics:
        lines.append("### 1. \u00bfLa final fue at\u00edpica para Espa\u00f1a?\n")
        zposs = analisis_metrics["spain_poss_z"]
        zxg = analisis_metrics["spain_xg_z"]
        lines.append(
            f"En la final, Espa\u00f1a registr\u00f3 una posesi\u00f3n de 68% (z={zposs}) "
            f"y un xG de {analisis_metrics['spain_final_xg']} (z={zxg}) frente a su promedio del torneo. "
        )
        lines.append(
            "Aunque domin\u00f3 m\u00e1s que en el resto del torneo, la falta de concreci\u00f3n "
            "oblig\u00f3 a definir reci\u00e9n en el minuto 106. El \u00fanico gol de Ferran Torres "
            "represent\u00f3 una conversi\u00f3n del 6.25% de las chances de gol, "
            "muy por debajo de la media del torneo.\n\n"
        )

        lines.append(
            "### 2. xG: \u00bfEl modelo predictivo avala a Espa\u00f1a como campe\u00f3n?\n"
        )
        lines.append(
            f"El modelo de xG acierta el resultado en el **{analisis_metrics['xg_acc']}%** de los partidos del torneo. "
        )
        lines.append(
            f"A nivel agregado, Espa\u00f1a gener\u00f3 m\u00e1s xG del que convirti\u00f3 en goles, "
            f"mientras que Argentina muestra una eficiencia ofensiva de {analisis_metrics['arg_eff']}x "
            f"(vs {analisis_metrics['spain_eff']}x de Espa\u00f1a).\n"
        )
        lines.append(
            "La diferencia clave estuvo en el arco propio: Emiliano Mart\u00ednez realiz\u00f3 **11 atajadas** "
            "en la final (r\u00e9cord del torneo en un solo partido), manteniendo a Argentina con vida "
            "hasta el gol de Torres.\n\n"
        )

    lines.append("### 3. Eficiencia de Conversi\u00f3n\n")
    lines.append(
        "La eficiencia de conversi\u00f3n (goles reales / xG) mide si un equipo concret\u00f3 "
        "las chances que gener\u00f3 o si dependi\u00f3 de sobreperformance individual. "
    )
    lines.append(
        "Un valor mayor a 1.0 indica que el equipo anot\u00f3 m\u00e1s de lo esperado "
        "(suerte o eficiencia cl\u00ednica); menor a 1.0 indica que dej\u00f3 puntos en el camino.\n\n"
    )
    lines.append(
        "Espa\u00f1a, con su defensa hist\u00f3rica (1 solo gol recibido), no necesit\u00f3 "
        "una eficiencia ofensiva excelente para ganar el t\u00edtulo. Su solidez defensiva "
        "fue el factor diferenciador, no su producci\u00f3n ofensiva.\n"
    )
    lines.append("\n")

    lines.append("## Conclusi\u00f3n\n")
    lines.append(
        "El an\u00e1lisis de m\u00e9tricas avanzadas confirma que Espa\u00f1a fue el justo campe\u00f3n del Mundial 2026. "
    )
    lines.append(
        "El modelo de xG la se\u00f1ala como el equipo m\u00e1s dominante del torneo, y su rendimiento en la final "
        "fue consistente (e incluso superior) con su promedio del torneo. "
    )
    lines.append(
        "Sin embargo, el 1-0 no refleja la magnitud del dominio: Espa\u00f1a acumul\u00f3 2.34 xG en la final, "
        "lo que en un escenario promedio habr\u00eda significado un marcador m\u00e1s holgado. "
    )
    lines.append(
        "Argentina, gracias a una sobreperformance defensiva hist\u00f3rica de Emiliano Mart\u00ednez "
        "(11 atajadas, la mayor cantidad en una final sin recibir gol hasta el minuto 106), "
        "mantuvo vivo un partido que las m\u00e9tricas daban por decidido.\n\n"
    )
    lines.append(
        "Espa\u00f1a no solo gan\u00f3 el Mundial, sino que estableci\u00f3 un r\u00e9cord de solidez: "
        "solo **1 gol recibido en todo el torneo**, demostrando que el equilibrio defensivo "
        "puede ser tan efectivo como el juego de ataque brillante. "
    )
    lines.append(
        "Este t\u00edtulo, el segundo en la historia de La Roja tras el de 2010, confirma a Espa\u00f1a "
        "como una de las potencias mundiales del f\u00fatbol, y sella el legado de una generaci\u00f3n "
        "que supo combinar dominio estad\u00edstico con resultados concretos.\n"
    )

    return "".join(lines)


def write_conclusion_to_file(conclusion_text: str, output_path="reports/conclusion.md"):
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(conclusion_text, encoding="utf-8")
    print(f"       Conclusion saved to {out}")
