"""
FixtureDB — Exploratory Data Analysis
======================================
Nesting Depth vs Complexity Correlation (Phase 3)
"""

import argparse
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats

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


def plot_nesting_complexity_correlation(conn, out_dir, show):
    """
    Analyze relationship between max_nesting_depth and complexity metrics.
    Shows whether nesting is independent descriptor of complexity.
    """
    if not has_data(conn, "fixtures"):
        print("  [skip] No fixture data yet. Run `python pipeline.py extract`.")
        return

    fixtures = qdf(
        conn,
        """
        SELECT f.max_nesting_depth, f.cyclomatic_complexity, 
               f.cognitive_complexity, f.loc, r.language
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
    fig.suptitle(
        "Nesting Depth vs Code Complexity Metrics",
        fontsize=14,
        fontweight="bold",
        y=0.995,
    )

    # ── 8b1: Nesting vs Cyclomatic Complexity ──────────────────────────────────
    ax = axes[0, 0]
    for lang in present:
        data = fixtures[fixtures["language"] == lang]
        ax.scatter(
            data["max_nesting_depth"],
            data["cyclomatic_complexity"],
            alpha=0.5,
            s=30,
            label=lang_display(lang),
            color=LANG_PALETTE[lang],
        )

    # Add trend line
    z = np.polyfit(fixtures["max_nesting_depth"], fixtures["cyclomatic_complexity"], 1)
    p = np.poly1d(z)
    x_line = np.linspace(
        fixtures["max_nesting_depth"].min(), fixtures["max_nesting_depth"].max(), 100
    )
    ax.plot(x_line, p(x_line), "r--", alpha=0.8, linewidth=2, label="Trend")

    corr = fixtures["max_nesting_depth"].corr(fixtures["cyclomatic_complexity"])
    ax.set_xlabel("Max Nesting Depth")
    ax.set_ylabel("Cyclomatic Complexity")
    ax.set_title(
        f"8b: Nesting vs Cyclomatic (r={corr:.2f})", fontsize=11, fontweight="bold"
    )
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(alpha=0.3)

    # ── 8b2: Nesting vs Cognitive Complexity ────────────────────────────────────
    ax = axes[0, 1]
    for lang in present:
        data = fixtures[fixtures["language"] == lang]
        ax.scatter(
            data["max_nesting_depth"],
            data["cognitive_complexity"],
            alpha=0.5,
            s=30,
            label=lang_display(lang),
            color=LANG_PALETTE[lang],
        )

    # Add trend line
    z = np.polyfit(fixtures["max_nesting_depth"], fixtures["cognitive_complexity"], 1)
    p = np.poly1d(z)
    x_line = np.linspace(
        fixtures["max_nesting_depth"].min(), fixtures["max_nesting_depth"].max(), 100
    )
    ax.plot(x_line, p(x_line), "r--", alpha=0.8, linewidth=2, label="Trend")

    corr = fixtures["max_nesting_depth"].corr(fixtures["cognitive_complexity"])
    ax.set_xlabel("Max Nesting Depth")
    ax.set_ylabel("Cognitive Complexity")
    ax.set_title(
        f"8b: Nesting vs Cognitive (r={corr:.2f})", fontsize=11, fontweight="bold"
    )
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(alpha=0.3)

    # ── 8b3: Nesting vs LOC ────────────────────────────────────────────────────
    ax = axes[1, 0]
    for lang in present:
        data = fixtures[fixtures["language"] == lang]
        ax.scatter(
            data["max_nesting_depth"],
            data["loc"],
            alpha=0.5,
            s=30,
            label=lang_display(lang),
            color=LANG_PALETTE[lang],
        )

    corr = fixtures["max_nesting_depth"].corr(fixtures["loc"])
    ax.set_xlabel("Max Nesting Depth")
    ax.set_ylabel("Lines of Code")
    ax.set_title(f"8b: Nesting vs LOC (r={corr:.2f})", fontsize=11, fontweight="bold")
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(alpha=0.3)

    # ── 8b4: Correlation heatmap ───────────────────────────────────────────────
    ax = axes[1, 1]
    corr_matrix = fixtures[
        ["max_nesting_depth", "cyclomatic_complexity", "cognitive_complexity", "loc"]
    ].corr()

    sns.heatmap(
        corr_matrix,
        annot=True,
        fmt=".2f",
        cmap="RdYlGn",
        center=0,
        cbar_kws={"label": "Correlation"},
        ax=ax,
        vmin=-1,
        vmax=1,
    )
    ax.set_title("8b: Correlation Matrix", fontsize=11, fontweight="bold")

    plt.tight_layout()
    save_or_show(fig, "08b_nesting_complexity_correlation", out_dir, show)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="FixtureDB Nesting-Complexity Correlation"
    )
    parser.add_argument("--db", default=str(DB_PATH))
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Base output directory")
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()

    setup_style()
    conn = load_db(args.db)
    plot_nesting_complexity_correlation(
        conn, Path(args.out) / datetime.now().strftime("%Y-%m-%d_%H-%M-%S"), args.show
    )
