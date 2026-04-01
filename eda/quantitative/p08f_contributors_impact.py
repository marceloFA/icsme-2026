"""
FixtureDB — Exploratory Data Analysis
======================================
Project Team Size vs Fixture Quality (Phase 3)
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


def plot_contributors_impact(conn, out_dir, show):
    """
    Analyze relationship between project team size (contributors) and fixture quality metrics.
    Questions: Do team projects have different fixture practices? Does team size predict quality?
    """
    if not has_data(conn, "fixtures"):
        print("  [skip] No fixture data yet. Run `python pipeline.py extract`.")
        return

    # Aggregate fixture metrics to repo level
    repos = qdf(
        conn,
        """
        SELECT r.id, r.num_contributors, r.language,
               AVG(f.cyclomatic_complexity) as avg_cc,
               AVG(f.cognitive_complexity) as avg_cog,
               AVG(f.max_nesting_depth) as avg_nesting,
               AVG(f.reuse_count) as avg_reuse,
               SUM(f.has_teardown_pair) as count_with_teardown,
               COUNT(f.id) as total_fixtures
        FROM repositories r
        LEFT JOIN fixtures f ON r.id = f.repo_id
        WHERE r.status = 'analysed' AND r.num_contributors > 0
        GROUP BY r.id
    """,
    )

    if repos.empty or repos["num_contributors"].isna().all():
        print("  [skip] No contributor data (run Phase 3 collection).")
        return

    # Filter to languages we have good data for
    present = [l for l in LANG_ORDER if l in repos["language"].values]
    repos = repos[repos["language"].isin(present)]

    # Calculate teardown adoption rate per repo
    repos["teardown_adoption"] = (
        100 * repos["count_with_teardown"] / repos["total_fixtures"]
    )

    # Create team size categories
    repos["team_category"] = pd.cut(
        repos["num_contributors"],
        bins=[0, 1, 5, 10, np.inf],
        labels=["Solo\n(1)", "Small\n(2-5)", "Medium\n(6-10)", "Large\n(11+)"],
    )

    fig, axes = plt.subplots(2, 2, figsize=(14, 10), facecolor="#FAFAFA")
    fig.suptitle(
        "Project Team Size vs Fixture Quality Metrics",
        fontsize=14,
        fontweight="bold",
        y=0.995,
    )

    # ── 8g1: Team size vs Cyclomatic Complexity ────────────────────────────────
    ax = axes[0, 0]
    for lang in present:
        data = repos[repos["language"] == lang]
        ax.scatter(
            data["num_contributors"],
            data["avg_cc"],
            alpha=0.6,
            s=50,
            label=lang_display(lang),
            color=LANG_PALETTE[lang],
        )

    corr = repos["num_contributors"].corr(repos["avg_cc"])
    ax.set_xlabel("Number of Contributors")
    ax.set_ylabel("Avg Cyclomatic Complexity")
    ax.set_title(
        f"8g: Contributors vs Cyclomatic (r={corr:.2f})", fontsize=11, fontweight="bold"
    )
    ax.legend(fontsize=8, loc="best")
    ax.grid(alpha=0.3)
    ax.set_xscale("log")

    # ── 8g2: Team size vs Nesting Depth ────────────────────────────────────────
    ax = axes[0, 1]
    for lang in present:
        data = repos[repos["language"] == lang]
        ax.scatter(
            data["num_contributors"],
            data["avg_nesting"],
            alpha=0.6,
            s=50,
            label=lang_display(lang),
            color=LANG_PALETTE[lang],
        )

    corr = repos["num_contributors"].corr(repos["avg_nesting"])
    ax.set_xlabel("Number of Contributors")
    ax.set_ylabel("Avg Max Nesting Depth")
    ax.set_title(
        f"8g: Contributors vs Nesting (r={corr:.2f})", fontsize=11, fontweight="bold"
    )
    ax.legend(fontsize=8, loc="best")
    ax.grid(alpha=0.3)
    ax.set_xscale("log")

    # ── 8g3: Team size vs Fixture Reuse ────────────────────────────────────────
    ax = axes[1, 0]
    for lang in present:
        data = repos[repos["language"] == lang]
        ax.scatter(
            data["num_contributors"],
            data["avg_reuse"],
            alpha=0.6,
            s=50,
            label=lang_display(lang),
            color=LANG_PALETTE[lang],
        )

    corr = repos["num_contributors"].corr(repos["avg_reuse"])
    ax.set_xlabel("Number of Contributors")
    ax.set_ylabel("Avg Fixture Reuse Count")
    ax.set_title(
        f"8g: Contributors vs Reuse (r={corr:.2f})", fontsize=11, fontweight="bold"
    )
    ax.legend(fontsize=8, loc="best")
    ax.grid(alpha=0.3)
    ax.set_xscale("log")

    # ── 8g4: Team category comparison ──────────────────────────────────────────
    ax = axes[1, 1]

    category_stats = repos.groupby("team_category", observed=True).agg(
        {
            "avg_cc": "mean",
            "avg_nesting": "mean",
            "avg_reuse": "mean",
            "teardown_adoption": "mean",
        }
    )

    x = np.arange(len(category_stats))
    width = 0.2

    ax.bar(
        x - 1.5 * width,
        category_stats["avg_cc"],
        width,
        label="Avg CC",
        color="#3498db",
        alpha=0.8,
    )
    ax.bar(
        x - 0.5 * width,
        category_stats["avg_nesting"],
        width,
        label="Avg Nesting",
        color="#e74c3c",
        alpha=0.8,
    )
    ax.bar(
        x + 0.5 * width,
        category_stats["avg_reuse"],
        width,
        label="Avg Reuse",
        color="#2ecc71",
        alpha=0.8,
    )
    ax.bar(
        x + 1.5 * width,
        category_stats["teardown_adoption"] / 20,
        width,
        label="Teardown Rate/20",
        color="#f39c12",
        alpha=0.8,
    )

    ax.set_xlabel("Project Team Category")
    ax.set_ylabel("Mean Metric Value")
    ax.set_title(
        "8g: Quality Metrics by Team Size Category", fontsize=11, fontweight="bold"
    )
    ax.set_xticks(x)
    ax.set_xticklabels(category_stats.index, fontsize=9)
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(alpha=0.3, axis="y")

    plt.tight_layout()
    save_or_show(fig, "08g_contributors_impact", out_dir, show)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="FixtureDB Contributors Impact Analysis"
    )
    parser.add_argument("--db", default=str(DB_PATH))
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Base output directory")
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()

    setup_style()
    conn = load_db(args.db)
    plot_contributors_impact(
        conn, Path(args.out) / datetime.now().strftime("%Y-%m-%d_%H-%M-%S"), args.show
    )
