"""
FixtureDB — Exploratory Data Analysis
======================================
Cleanup/Teardown Adoption by Framework (Phase 3)
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


def plot_teardown_adoption(conn, out_dir, show):
    """
    Analyze fixture cleanup/teardown adoption by language and testing framework.
    Shows resource management discipline and potential resource leak risks.
    """
    if not has_data(conn, "fixtures"):
        print("  [skip] No fixture data yet. Run `python pipeline.py extract`.")
        return

    fixtures = qdf(
        conn,
        """
        SELECT f.has_teardown_pair, r.language
        FROM fixtures f
        JOIN repositories r ON f.repo_id = r.id
        WHERE r.status = 'analysed'
    """,
    )
    if fixtures.empty or fixtures["has_teardown_pair"].isna().all():
        print("  [skip] No teardown pair data (run Phase 3 collection).")
        return

    present = [l for l in LANG_ORDER if l in fixtures["language"].values]
    fixtures = fixtures[fixtures["language"].isin(present)]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10), facecolor="#FAFAFA")
    fig.suptitle(
        "Fixture Cleanup/Teardown Adoption (Resource Management Discipline)",
        fontsize=14,
        fontweight="bold",
        y=0.995,
    )

    # ── 8f1: Stacked bar chart per language ────────────────────────────────────
    ax = axes[0, 0]

    teardown_counts = []
    lang_names = []
    for lang in present:
        lang_data = fixtures[fixtures["language"] == lang]["has_teardown_pair"]
        with_teardown = (lang_data == 1).sum()
        without_teardown = (lang_data == 0).sum()
        teardown_counts.append([without_teardown, with_teardown])
        lang_names.append(lang_display(lang))

    teardown_counts = np.array(teardown_counts)
    x = np.arange(len(lang_names))
    width = 0.6

    bars1 = ax.bar(
        x, teardown_counts[:, 0], width, label="No Teardown", color="#e74c3c", alpha=0.8
    )
    bars2 = ax.bar(
        x,
        teardown_counts[:, 1],
        width,
        bottom=teardown_counts[:, 0],
        label="With Teardown",
        color="#2ecc71",
        alpha=0.8,
    )

    ax.set_ylabel("Number of Fixtures")
    ax.set_title(
        "8f: Teardown Adoption by Language (Stacked)", fontsize=11, fontweight="bold"
    )
    ax.set_xticks(x)
    ax.set_xticklabels(lang_names, fontsize=9)
    ax.legend()
    ax.grid(alpha=0.3, axis="y")

    # ── 8f2: Percentage adoption per language ──────────────────────────────────
    ax = axes[0, 1]

    adoption_pct = []
    for lang in present:
        lang_data = fixtures[fixtures["language"] == lang]["has_teardown_pair"]
        pct = 100 * (lang_data == 1).sum() / len(lang_data) if len(lang_data) > 0 else 0
        adoption_pct.append(pct)

    colors = [
        "#2ecc71" if p >= 50 else "#f39c12" if p >= 25 else "#e74c3c"
        for p in adoption_pct
    ]
    bars = ax.barh(lang_names, adoption_pct, color=colors, alpha=0.8)

    # Add percentage labels
    for i, (bar, pct) in enumerate(zip(bars, adoption_pct)):
        ax.text(pct + 2, i, f"{pct:.1f}%", va="center", fontsize=9, fontweight="bold")

    ax.set_xlabel("Adoption Rate (%)")
    ax.set_title(
        "8f: Teardown Adoption Rate by Language", fontsize=11, fontweight="bold"
    )
    ax.set_xlim(0, 105)
    ax.grid(alpha=0.3, axis="x")
    ax.axvline(
        50, color="gray", linestyle="--", alpha=0.5, linewidth=1, label="50% threshold"
    )

    # ── 8f3: Distribution pie chart ────────────────────────────────────────────
    ax = axes[1, 0]

    total_with = (fixtures["has_teardown_pair"] == 1).sum()
    total_without = (fixtures["has_teardown_pair"] == 0).sum()

    sizes = [total_without, total_with]
    labels = [
        f"No Teardown\n{total_without:,} ({100*total_without/(total_without+total_with):.1f}%)",
        f"With Teardown\n{total_with:,} ({100*total_with/(total_without+total_with):.1f}%)",
    ]
    colors_pie = ["#e74c3c", "#2ecc71"]

    ax.pie(
        sizes,
        labels=labels,
        colors=colors_pie,
        autopct="",
        startangle=90,
        textprops={"fontsize": 10, "fontweight": "bold"},
    )
    ax.set_title("8f: Overall Teardown Adoption", fontsize=11, fontweight="bold")

    # ── 8f4: Summary statistics ────────────────────────────────────────────────
    ax = axes[1, 1]
    ax.axis("off")

    stat_text = "Summary Statistics:\n" + "─" * 40 + "\n"
    stat_text += f"Total Fixtures: {len(fixtures):,}\n"
    stat_text += (
        f"With Teardown: {total_with:,} ({100*total_with/len(fixtures):.1f}%)\n"
    )
    stat_text += f"Without Teardown: {total_without:,} ({100*total_without/len(fixtures):.1f}%)\n"

    stat_text += "\nAdoption by Language:\n" + "─" * 40 + "\n"
    for lang, pct in zip(present, adoption_pct):
        status = "✓ GOOD" if pct >= 50 else "⚠ OK" if pct >= 25 else "✗ LOW"
        stat_text += f"{lang_display(lang):12s}: {pct:6.1f}%  {status}\n"

    stat_text += "\nInterpretation:\n" + "─" * 40 + "\n"
    stat_text += "• High (>50%): Strong resource\n"
    stat_text += "  management discipline in language\n"
    stat_text += "• Moderate (25-50%): Mixed practices\n"
    stat_text += "• Low (<25%): Potential resource\n"
    stat_text += "  leak exposure in ecosystem\n"

    ax.text(
        0.05,
        0.95,
        stat_text,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment="top",
        fontfamily="monospace",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.3),
    )

    plt.tight_layout()
    save_or_show(fig, "08f_teardown_adoption", out_dir, show)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FixtureDB Teardown Adoption Analysis")
    parser.add_argument("--db", default=str(DB_PATH))
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Base output directory")
    parser.add_argument("--show", action="store_true")
    args = parser.parse_args()

    setup_style()
    conn = load_db(args.db)
    plot_teardown_adoption(
        conn, Path(args.out) / datetime.now().strftime("%Y-%m-%d_%H-%M-%S"), args.show
    )
