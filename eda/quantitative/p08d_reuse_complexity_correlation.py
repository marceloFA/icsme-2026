"""
FixtureDB — Exploratory Data Analysis
======================================
Fixture Reuse vs Complexity Correlation (Phase 3)
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


def plot_reuse_complexity_correlation(conn, out_dir, show):
    """
    Analyze relationship between fixture reuse and complexity metrics.
    Answers: Are simple fixtures reused more? Do complex fixtures get specialized?
    """
    if not has_data(conn, "fixtures"):
        print("  [skip] No fixture data yet. Run `python pipeline.py extract`.")
        return

    fixtures = qdf(
        conn,
        """
        SELECT f.reuse_count, f.cyclomatic_complexity, f.cognitive_complexity,
               f.loc, r.language
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
    fig.suptitle(
        "Fixture Reuse vs Complexity (How Complex Are Reused Fixtures?)",
        fontsize=14,
        fontweight="bold",
        y=0.995,
    )

    # ── 8e1: Reuse vs Cyclomatic Complexity ────────────────────────────────────
    ax = axes[0, 0]
    for lang in present:
        data = fixtures[fixtures["language"] == lang]
        ax.scatter(
            data["reuse_count"],
            data["cyclomatic_complexity"],
            alpha=0.5,
            s=30,
            label=lang_display(lang),
            color=LANG_PALETTE[lang],
        )

    corr = fixtures["reuse_count"].corr(fixtures["cyclomatic_complexity"])
    ax.set_xlabel("Reuse Count (# tests using fixture)")
    ax.set_ylabel("Cyclomatic Complexity")
    ax.set_title(
        f"8e: Reuse vs Cyclomatic (r={corr:.2f})", fontsize=11, fontweight="bold"
    )
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(alpha=0.3)

    # ── 8e2: Reuse vs Cognitive Complexity ─────────────────────────────────────
    ax = axes[0, 1]
    for lang in present:
        data = fixtures[fixtures["language"] == lang]
        ax.scatter(
            data["reuse_count"],
            data["cognitive_complexity"],
            alpha=0.5,
            s=30,
            label=lang_display(lang),
            color=LANG_PALETTE[lang],
        )

    corr = fixtures["reuse_count"].corr(fixtures["cognitive_complexity"])
    ax.set_xlabel("Reuse Count")
    ax.set_ylabel("Cognitive Complexity")
    ax.set_title(
        f"8e: Reuse vs Cognitive (r={corr:.2f})", fontsize=11, fontweight="bold"
    )
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(alpha=0.3)

    # ── 8e3: Reuse vs LOC ──────────────────────────────────────────────────────
    ax = axes[1, 0]
    for lang in present:
        data = fixtures[fixtures["language"] == lang]
        ax.scatter(
            data["reuse_count"],
            data["loc"],
            alpha=0.5,
            s=30,
            label=lang_display(lang),
            color=LANG_PALETTE[lang],
        )

    corr = fixtures["reuse_count"].corr(fixtures["loc"])
    ax.set_xlabel("Reuse Count")
    ax.set_ylabel("Lines of Code")
    ax.set_title(f"8e: Reuse vs LOC (r={corr:.2f})", fontsize=11, fontweight="bold")
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(alpha=0.3)

    # ── 8e4: Mean complexity by reuse category ─────────────────────────────────
    ax = axes[1, 1]

    # Create reuse categories
    fixtures["reuse_category"] = pd.cut(
        fixtures["reuse_count"],
        bins=[-0.5, 0.5, 1.5, 5.5, np.inf],
        labels=[
            "Unused\n(0)",
            "Single-Use\n(1)",
            "Moderate\n(2-5)",
            "High Reuse\n(>5)",
        ],
    )

    # Calculate mean complexity per category
    category_complexity = fixtures.groupby("reuse_category", observed=True).agg(
        {
            "cyclomatic_complexity": "mean",
            "cognitive_complexity": "mean",
            "loc": "mean",
        }
    )

    x = np.arange(len(category_complexity))
    width = 0.35

    ax2 = ax.twinx()

    bars1 = ax.bar(
        x - width / 2,
        category_complexity["cyclomatic_complexity"],
        width,
        label="Cyclomatic",
        color="#3498db",
        alpha=0.8,
    )
    bars2 = ax.bar(
        x + width / 2,
        category_complexity["cognitive_complexity"],
        width,
        label="Cognitive",
        color="#e74c3c",
        alpha=0.8,
    )
    line = ax2.plot(
        x,
        category_complexity["loc"],
        marker="o",
        color="#2ecc71",
        linewidth=2.5,
        markersize=8,
        label="LOC",
    )

    ax.set_xlabel("Fixture Reuse Category")
    ax.set_ylabel("Mean Complexity Score")
    ax2.set_ylabel("Mean Lines of Code", color="#2ecc71")
    ax2.tick_params(axis="y", labelcolor="#2ecc71")
    ax.set_title(
        "8e: Mean Complexity by Reuse Category", fontsize=11, fontweight="bold"
    )
    ax.set_xticks(x)
    ax.set_xticklabels(category_complexity.index, fontsize=9)
    ax.legend(loc="upper left", fontsize=9)
    ax2.legend(loc="upper right", fontsize=9)
    ax.grid(alpha=0.3, axis="y")

    plt.tight_layout()
    save_or_show(fig, "08e_reuse_complexity_correlation", out_dir, show)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="FixtureDB Reuse-Complexity Correlation"
    )
    parser.add_argument("--db", default=str(DB_PATH))
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Base output directory")
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()

    setup_style()
    conn = load_db(args.db)
    plot_reuse_complexity_correlation(
        conn, Path(args.out) / datetime.now().strftime("%Y-%m-%d_%H-%M-%S"), args.show
    )
