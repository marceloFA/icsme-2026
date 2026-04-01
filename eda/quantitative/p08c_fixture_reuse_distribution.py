"""
FixtureDB — Exploratory Data Analysis
======================================
Fixture Reuse Distribution Analysis (Phase 3)
"""

import argparse
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from ..eda_common import (
    ROOT,
    DB_PATH,
    DEFAULT_OUT,
    LANG_PALETTE,
    LANG_ORDER,
    setup_style,
    save_or_show,
    load_db,
    has_data,
    qdf,
    lang_display,
)


def plot_fixture_reuse_distribution(conn, out_dir, show):
    """
    Analyze fixture reuse patterns - how many tests share individual fixtures?
    Shows modularity and fixture design confidence across languages.
    """
    if not has_data(conn, "fixtures"):
        print("  [skip] No fixture data yet. Run `python pipeline.py extract`.")
        return

    fixtures = qdf(
        conn,
        """
        SELECT f.reuse_count, r.language
        FROM fixtures f
        JOIN repositories r ON f.repo_id = r.id
        WHERE r.status = 'analysed'
    """,
    )
    if fixtures.empty or fixtures["reuse_count"].isna().all():
        print("  [skip] No reuse count data (run Phase 3 collection).")
        return

    present = [l for l in LANG_ORDER if l in fixtures["language"].values]
    fixtures = fixtures[fixtures["language"].isin(present)]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10), facecolor="#FAFAFA")
    fig.suptitle("Fixture Reuse Distribution (How Many Tests Share Each Fixture?)", 
                 fontsize=14, fontweight="bold", y=0.995)

    # ── 8d1: Violin plot per language ──────────────────────────────────────────
    ax = axes[0, 0]
    plot_data = []
    for lang in present:
        lang_data = fixtures[fixtures["language"] == lang]["reuse_count"]
        plot_data.append({
            "language": lang_display(lang),
            "reuse_count": lang_data,
            "color": LANG_PALETTE[lang]
        })
    
    # Create violin plot data
    df_plot = pd.DataFrame([
        {"Language": d["language"], "Reuse Count": val}
        for d in plot_data
        for val in d["reuse_count"]
    ])
    
    sns.violinplot(
        data=df_plot,
        x="Language",
        y="Reuse Count",
        palette={d["language"]: d["color"] for d in plot_data},
        ax=ax,
    )
    ax.set_xlabel("")
    ax.set_ylabel("Reuse Count (# tests using fixture)")
    ax.set_title("8d: Reuse Count Distribution per Language", fontsize=11, fontweight='bold')
    ax.grid(alpha=0.3, axis='y')

    # ── 8d2: Histogram of overall distribution ─────────────────────────────────
    ax = axes[0, 1]
    ax.hist(
        fixtures["reuse_count"],
        bins=40,
        color="#3498db",
        alpha=0.7,
        edgecolor="black",
    )
    ax.axvline(
        fixtures["reuse_count"].mean(),
        color="red",
        linestyle="--",
        linewidth=2,
        label=f"Mean: {fixtures['reuse_count'].mean():.2f}",
    )
    ax.axvline(
        fixtures["reuse_count"].median(),
        color="green",
        linestyle="--",
        linewidth=2,
        label=f"Median: {fixtures['reuse_count'].median():.0f}",
    )
    ax.set_xlabel("Reuse Count")
    ax.set_ylabel("Number of Fixtures")
    ax.set_title("8d: Overall Reuse Count Distribution", fontsize=11, fontweight='bold')
    ax.legend()
    ax.grid(alpha=0.3, axis='y')

    # ── 8d3: Box plots per language ────────────────────────────────────────────
    ax = axes[1, 0]
    sns.boxplot(
        data=df_plot,
        x="Language",
        y="Reuse Count",
        palette={d["language"]: d["color"] for d in plot_data},
        ax=ax,
    )
    ax.set_xlabel("")
    ax.set_ylabel("Reuse Count")
    ax.set_title("8d: Reuse Count Box Plots by Language", fontsize=11, fontweight='bold')
    ax.grid(alpha=0.3, axis='y')

    # ── 8d4: Summary statistics ────────────────────────────────────────────────
    ax = axes[1, 1]
    ax.axis("off")
    
    # Overall stats
    stat_text = "Overall Statistics:\n" + "─" * 35 + "\n"
    stat_text += f"Total Fixtures: {len(fixtures):,}\n"
    stat_text += f"Mean Reuse: {fixtures['reuse_count'].mean():.2f}\n"
    stat_text += f"Median Reuse: {fixtures['reuse_count'].median():.0f}\n"
    stat_text += f"Std Dev: {fixtures['reuse_count'].std():.2f}\n"
    stat_text += f"Min: {fixtures['reuse_count'].min():.0f}\n"
    stat_text += f"Max: {fixtures['reuse_count'].max():.0f}\n"
    stat_text += "\nReuse Categories:\n" + "─" * 35 + "\n"
    
    # Categorization
    unused = (fixtures["reuse_count"] == 0).sum()
    single = (fixtures["reuse_count"] == 1).sum()
    moderate = ((fixtures["reuse_count"] > 1) & (fixtures["reuse_count"] <= 5)).sum()
    high = (fixtures["reuse_count"] > 5).sum()
    
    stat_text += f"Unused (0 uses): {unused:,} ({100*unused/len(fixtures):.1f}%)\n"
    stat_text += f"Single-Use (1): {single:,} ({100*single/len(fixtures):.1f}%)\n"
    stat_text += f"Moderate (2-5): {moderate:,} ({100*moderate/len(fixtures):.1f}%)\n"
    stat_text += f"High Reuse (>5): {high:,} ({100*high/len(fixtures):.1f}%)\n"
    
    stat_text += "\nPer-Language Mean Reuse:\n" + "─" * 35 + "\n"
    for lang in present:
        mean_reuse = fixtures[fixtures["language"] == lang]["reuse_count"].mean()
        stat_text += f"{lang_display(lang):12s}: {mean_reuse:6.2f}\n"

    ax.text(
        0.05, 0.95,
        stat_text,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment="top",
        fontfamily="monospace",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.3),
    )

    plt.tight_layout()
    save_or_show(fig, "08d_fixture_reuse_distribution", out_dir, show)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FixtureDB Fixture Reuse Distribution")
    parser.add_argument("--db", default=str(DB_PATH))
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Base output directory")
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()

    setup_style()
    conn = load_db(args.db)
    plot_fixture_reuse_distribution(
        conn, Path(args.out) / datetime.now().strftime("%Y-%m-%d_%H-%M-%S"), args.show
    )
