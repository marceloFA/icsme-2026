"""
FixtureDB — Exploratory Data Analysis
======================================
Nesting Depth Distribution (Phase 3 metric)
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


def plot_nesting_depth(conn, out_dir, show):
    """
    Visualize max_nesting_depth distribution across languages.
    Shows structural code complexity independent of branching.
    """
    if not has_data(conn, "fixtures"):
        print("  [skip] No fixture data yet. Run `python pipeline.py extract`.")
        return

    fixtures = qdf(
        conn,
        """
        SELECT f.max_nesting_depth, f.cyclomatic_complexity, r.language
        FROM fixtures f
        JOIN repositories r ON f.repo_id = r.id
        WHERE r.status = 'analysed'
    """,
    )
    if fixtures.empty or fixtures["max_nesting_depth"].isna().all():
        print("  [skip] No nesting depth data (run Phase 3 collection).")
        return

    present = [l for l in LANG_ORDER if l in fixtures["language"].values]
    fixtures = fixtures[fixtures["language"].isin(present)]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10), facecolor="#FAFAFA")
    fig.suptitle("Structural Code Complexity: Max Nesting Depth Analysis", 
                 fontsize=14, fontweight="bold", y=0.995)

    # ── 8a1: Distribution per language (violin) ───────────────────────────────
    ax = axes[0, 0]
    data_for_violin = [
        fixtures[fixtures["language"] == lang]["max_nesting_depth"].values
        for lang in present
    ]
    parts = ax.violinplot(
        data_for_violin,
        positions=range(len(present)),
        widths=0.6,
        showmeans=True,
        showmedians=True,
    )
    
    for pc in parts['bodies']:
        pc.set_facecolor('#888888')
        pc.set_alpha(0.5)
    
    ax.set_xticks(range(len(present)))
    ax.set_xticklabels([lang_display(l) for l in present], rotation=45, ha='right')
    ax.set_ylabel("Max Nesting Depth")
    ax.set_title("8a: Distribution by Language", fontsize=11, fontweight='bold')
    ax.grid(axis='y', alpha=0.3, zorder=0)
    ax.set_ylim(bottom=0)

    # ── 8a2: Histogram (all languages combined) ────────────────────────────────
    ax = axes[0, 1]
    ax.hist(
        fixtures["max_nesting_depth"],
        bins=range(1, int(fixtures["max_nesting_depth"].max()) + 2),
        edgecolor='black',
        alpha=0.7,
        color='steelblue',
        zorder=3,
    )
    ax.set_xlabel("Max Nesting Depth")
    ax.set_ylabel("Count of Fixtures")
    ax.set_title("8a: Overall Distribution", fontsize=11, fontweight='bold')
    ax.grid(axis='y', alpha=0.3, zorder=0)

    # ── 8a3: Box plot per language ─────────────────────────────────────────────
    ax = axes[1, 0]
    plot_data = [
        fixtures[fixtures["language"] == lang]["max_nesting_depth"].values
        for lang in present
    ]
    bp = ax.boxplot(
        plot_data,
        labels=[lang_display(l) for l in present],
        patch_artist=True,
        showmeans=True,
    )
    
    for patch, lang in zip(bp['boxes'], present):
        patch.set_facecolor(LANG_PALETTE[lang])
        patch.set_alpha(0.6)
    
    ax.set_ylabel("Max Nesting Depth")
    ax.set_title("8a: Box Plot by Language", fontsize=11, fontweight='bold')
    ax.tick_params(axis='x', rotation=45)
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
    ax.grid(axis='y', alpha=0.3, zorder=0)

    # ── 8a4: Summary statistics ────────────────────────────────────────────────
    ax = axes[1, 1]
    ax.axis('off')
    
    stats_text = "Summary Statistics\n" + "="*30 + "\n\n"
    stats_text += f"Total Fixtures: {len(fixtures)}\n"
    stats_text += f"Mean Nesting Depth: {fixtures['max_nesting_depth'].mean():.2f}\n"
    stats_text += f"Median Nesting Depth: {fixtures['max_nesting_depth'].median():.1f}\n"
    stats_text += f"Std Dev: {fixtures['max_nesting_depth'].std():.2f}\n"
    stats_text += f"Min: {fixtures['max_nesting_depth'].min():.0f}\n"
    stats_text += f"Max: {fixtures['max_nesting_depth'].max():.0f}\n"
    stats_text += f"\nShallowly nested (depth=1): {(fixtures['max_nesting_depth'] == 1).sum()}\n"
    stats_text += f"Moderately nested (2-3): {((fixtures['max_nesting_depth'] >= 2) & (fixtures['max_nesting_depth'] <= 3)).sum()}\n"
    stats_text += f"Deeply nested (depth≥4): {(fixtures['max_nesting_depth'] >= 4).sum()}\n"
    
    ax.text(0.1, 0.9, stats_text, transform=ax.transAxes, fontsize=10,
            verticalalignment='top', family='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))

    plt.tight_layout()
    save_or_show(fig, "08a_nesting_depth", out_dir, show)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FixtureDB Nesting Depth Analysis")
    parser.add_argument("--db", default=str(DB_PATH))
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Base output directory")
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()

    setup_style()
    conn = load_db(args.db)
    plot_nesting_depth(
        conn, Path(args.out) / datetime.now().strftime("%Y-%m-%d_%H-%M-%S"), args.show
    )
