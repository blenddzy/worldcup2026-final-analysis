import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import seaborn as sns


def plot_pitch(ax, color="green", line_color="white"):
    ax.set_xlim(0, 105)
    ax.set_ylim(0, 68)
    ax.set_facecolor(color)
    ax.set_aspect("equal")

    rect = mpatches.Rectangle(
        (0, 0), 105, 68, linewidth=2, edgecolor=line_color, facecolor="none"
    )
    ax.add_patch(rect)
    ax.plot([52.5, 52.5], [0, 68], color=line_color, linewidth=2)
    centre_circle = mpatches.Circle(
        (52.5, 34), 9.15, linewidth=2, edgecolor=line_color, facecolor="none"
    )
    ax.add_patch(centre_circle)

    for x, y, width, height in [
        (0, 13.84, 16.5, 40.32),
        (105 - 16.5, 13.84, 16.5, 40.32),
    ]:
        ax.add_patch(
            mpatches.Rectangle(
                (x, y),
                width,
                height,
                linewidth=2,
                edgecolor=line_color,
                facecolor="none",
            )
        )

    for x, y, width, height in [(0, 24.84, 5.5, 18.32), (105 - 5.5, 24.84, 5.5, 18.32)]:
        ax.add_patch(
            mpatches.Rectangle(
                (x, y),
                width,
                height,
                linewidth=2,
                edgecolor=line_color,
                facecolor="none",
            )
        )

    ax.add_patch(
        mpatches.Arc(
            (11, 34),
            18.3,
            18.3,
            angle=0,
            theta1=300,
            theta2=60,
            linewidth=2,
            edgecolor=line_color,
        )
    )
    ax.add_patch(
        mpatches.Arc(
            (94, 34),
            18.3,
            18.3,
            angle=0,
            theta1=120,
            theta2=240,
            linewidth=2,
            edgecolor=line_color,
        )
    )

    for x, y in [(52.5, 34)]:
        ax.plot(x, y, "o", color=line_color, markersize=6)
    for x, y in [(11, 34), (94, 34)]:
        ax.plot(x, y, "o", color=line_color, markersize=3)

    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)


def plot_shot_map(
    shots_home: list,
    shots_away: list,
    home_team: str,
    away_team: str,
    save_path: str = None,
):
    fig, ax = plt.subplots(figsize=(12, 8))
    plot_pitch(ax)

    for shot in shots_home:
        ax.scatter(
            shot.get("x", 0),
            shot.get("y", 0),
            s=shot.get("xG", 0) * 300 + 50,
            c="blue",
            alpha=0.6,
            edgecolors="darkblue",
            linewidth=1,
        )

    for shot in shots_away:
        ax.scatter(
            shot.get("x", 0),
            shot.get("y", 0),
            s=shot.get("xG", 0) * 300 + 50,
            c="red",
            alpha=0.6,
            edgecolors="darkred",
            linewidth=1,
        )

    ax.set_title(
        f"Shot Map: {home_team} vs {away_team}", fontsize=14, fontweight="bold"
    )
    ax.legend(
        handles=[
            mpatches.Patch(color="blue", label=home_team),
            mpatches.Patch(color="red", label=away_team),
        ],
        loc="upper right",
    )
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    if plt.get_backend() != "Agg":
        plt.show()


def plot_tournament_path(
    spain_matches: pd.DataFrame, arg_matches: pd.DataFrame, save_path: str = None
):
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    for ax, df, team, color in zip(
        axes,
        [spain_matches, arg_matches],
        ["Spain", "Argentina"],
        ["#C8102E", "#75AADB"],
    ):
        rounds = df["round"].tolist()
        gf = df["goals_for"].tolist()
        ga = df["goals_against"].tolist()
        opponents = df["opponent"].tolist()

        x = range(len(rounds))
        ax.bar(x, gf, 0.35, label="Goals For", color=color, alpha=0.8)
        ax.bar(
            [i + 0.35 for i in x],
            ga,
            0.35,
            label="Goals Against",
            color="gray",
            alpha=0.5,
        )
        ax.set_xticks([i + 0.175 for i in x])
        ax.set_xticklabels(rounds, rotation=45, ha="right", fontsize=9)
        ax.set_ylabel("Goals")
        ax.set_title(f"{team}: Route to Final", fontsize=13, fontweight="bold")
        for i, (o, g) in enumerate(zip(opponents, gf)):
            ax.annotate(
                f"vs {o}\n{g}-{ga[i]}",
                (i + 0.175, max(gf + ga) * 0.7),
                ha="center",
                fontsize=7,
                rotation=0,
            )
        ax.legend(fontsize=8)

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    if plt.get_backend() != "Agg":
        plt.show()


def plot_group_standings(
    standings_df: pd.DataFrame, n_groups: int = 6, save_path: str = None
):
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    axes = axes.flatten()
    groups = standings_df["group"].unique()[:n_groups]

    for ax, group in zip(axes, groups):
        grp_df = standings_df[standings_df["group"] == group].sort_values(
            "points", ascending=False
        )
        colors = [
            "#2ecc71" if i < 2 else "#e74c3c" if i == len(grp_df) - 1 else "#95a5a6"
            for i in range(len(grp_df))
        ]
        bars = ax.barh(
            grp_df["team"], grp_df["points"], color=colors, edgecolor="white"
        )
        ax.set_title(f"Group {group}", fontsize=12, fontweight="bold")
        ax.set_xlabel("Points")
        ax.invert_yaxis()
        for bar, pts in zip(bars, grp_df["points"]):
            ax.text(
                bar.get_width() + 0.3,
                bar.get_y() + bar.get_height() / 2,
                str(int(pts)),
                va="center",
                fontsize=10,
            )

    plt.suptitle(
        "World Cup 2026 - Group Stage Standings", fontsize=14, fontweight="bold"
    )
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    if plt.get_backend() != "Agg":
        plt.show()


def plot_goal_timeline(goals_df: pd.DataFrame, save_path: str = None):
    fig, ax = plt.subplots(figsize=(12, 4))
    teams_order = ["Spain", "Argentina"]
    colors = {"Spain": "#C8102E", "Argentina": "#75AADB"}

    for i, team in enumerate(teams_order):
        team_goals = goals_df[goals_df["team"] == team]
        ax.scatter(
            team_goals["minute"].astype(int),
            [i + 1] * len(team_goals),
            s=200,
            c=colors.get(team, "gray"),
            label=team,
            zorder=5,
            edgecolors="white",
            linewidth=2,
        )
        for _, g in team_goals.iterrows():
            ax.annotate(
                f"{g['scorer']}\n{g['minute']}'",
                (int(g["minute"]), i + 1.2),
                ha="center",
                fontsize=8,
                fontweight="bold",
            )

    ax.set_yticks([1, 2])
    ax.set_yticklabels(teams_order)
    ax.set_xlabel("Minute")
    ax.set_title("Goal Timeline - World Cup 2026 Final", fontsize=14, fontweight="bold")
    ax.set_xlim(0, 120)
    ax.axvline(45, color="gray", linestyle="--", alpha=0.5, label="HT")
    ax.axvline(90, color="gray", linestyle="--", alpha=0.5, label="FT")
    ax.axvline(105, color="gray", linestyle=":", alpha=0.5, label="ET HT")
    ax.legend()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
    if plt.get_backend() != "Agg":
        plt.show()
