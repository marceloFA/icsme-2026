"""
FixtureDB — Exploratory Data Analysis
======================================
Generates publication-quality plots for advisor review.

Usage:
    python eda.py                        # all available plots → output/eda/
    python eda.py --out figures/         # custom output directory
    python eda.py --show                 # display interactively instead of saving

The script detects which pipeline phases have completed and only generates
plots for data that exists. Run it at any stage.
"""

import argparse
import json
import sqlite3
import sys
import warnings
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
import seaborn as sns

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).parent
DB_PATH = ROOT / "data" / "50-repo-corpus.db"
DEFAULT_OUT = ROOT / "output" / "eda"   # timestamped subfolder added at runtime

# ---------------------------------------------------------------------------
# Language colour palette — consistent across all plots
# Per-language colours chosen to be distinct and print-friendly
# ---------------------------------------------------------------------------

LANG_PALETTE = {
    "python":     "#4C9BE8",   # blue
    "java":       "#E8834C",   # orange
    "javascript": "#E8C94C",   # yellow
    "typescript": "#4CE8A0",   # teal
    "go":         "#A04CE8",   # purple
}

LANG_ORDER = ["python", "java", "javascript", "typescript", "go"]

STATUS_PALETTE = {
    "discovered": "#B0BEC5",
    "cloned":     "#64B5F6",
    "analysed":   "#81C784",
    "skipped":    "#FFB74D",
    "error":      "#E57373",
}

DOMAIN_PALETTE = {
    "web":     "#4C9BE8",
    "library": "#81C784",
    "data":    "#FFB74D",
    "cli":     "#E8834C",
    "infra":   "#A04CE8",
    "other":   "#B0BEC5",
}

# ---------------------------------------------------------------------------
# Global aesthetics
# ---------------------------------------------------------------------------

def setup_style() -> None:
    sns.set_theme(
        style="whitegrid",
        context="paper",
        font="DejaVu Sans",
        rc={
            "figure.facecolor":   "#FAFAFA",
            "axes.facecolor":     "#FAFAFA",
            "grid.color":         "#E0E0E0",
            "grid.linewidth":     0.7,
            "axes.spines.top":    False,
            "axes.spines.right":  False,
            "axes.spines.left":   False,
            "axes.spines.bottom": True,
            "axes.linewidth":     0.8,
            "xtick.bottom":       True,
            "ytick.left":         False,
            "font.size":          10,
            "axes.titlesize":     12,
            "axes.titleweight":   "bold",
            "axes.labelsize":     10,
            "legend.frameon":     False,
            "figure.dpi":         150,
        },
    )


def save_or_show(fig: plt.Figure, name: str,
                 out_dir: Path | None, show: bool) -> None:
    if show:
        plt.show()
    else:
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / f"{name}.png"
        fig.savefig(path, bbox_inches="tight", dpi=180, facecolor=fig.get_facecolor())
        try:
            display = path.relative_to(ROOT)
        except ValueError:
            display = path
        print(f"  ✓ {display}")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Data loading helpers
# ---------------------------------------------------------------------------

def load_db(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        print(f"[error] Database not found at {db_path}")
        print("        Run `python pipeline.py init` and at least one search phase.")
        sys.exit(1)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def has_table(conn: sqlite3.Connection, table: str) -> bool:
    r = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    ).fetchone()
    return r is not None


def has_data(conn: sqlite3.Connection, table: str,
             condition: str = "1=1") -> bool:
    if not has_table(conn, table):
        return False
    r = conn.execute(f"SELECT COUNT(*) n FROM {table} WHERE {condition}").fetchone()
    return r["n"] > 0


def df(conn: sqlite3.Connection, query: str) -> pd.DataFrame:
    return pd.read_sql_query(query, conn)


# ---------------------------------------------------------------------------
# SECTION 1 — Corpus Composition
# ---------------------------------------------------------------------------

def plot_corpus_composition(conn, out_dir, show):
    """
    1a. Repos per language coloured by star tier (core vs extended).
    1b. Pipeline status funnel — shows collection health at a glance.
    """
    repos = df(conn, "SELECT language, star_tier, status FROM repositories")
    if repos.empty:
        print("  [skip] No repositories in DB yet.")
        return

    fig, axes = plt.subplots(1, 2, figsize=(13, 5), facecolor="#FAFAFA")
    fig.suptitle("Corpus Composition", fontsize=14, fontweight="bold", y=1.01)

    # --- 1a: repos by language + star tier ---
    ax = axes[0]
    tier_counts = (
        repos.groupby(["language", "star_tier"])
        .size()
        .reset_index(name="count")
    )

    tier_order   = ["core", "extended"]
    tier_colours = {"core": "#3D7FCC", "extended": "#A8CAEA"}

    present_langs = [l for l in LANG_ORDER if l in tier_counts["language"].values]
    x = range(len(present_langs))
    width = 0.35

    bottom_vals = {lang: 0 for lang in present_langs}
    for tier in tier_order:
        vals = [
            tier_counts.query("language==@lang and star_tier==@tier")["count"].sum()
            for lang in present_langs
        ]
        bars = ax.bar(x, vals, width=0.6, bottom=[bottom_vals[l] for l in present_langs],
                      color=tier_colours[tier], label=f"{'≥500' if tier=='core' else '100–499'} stars",
                      zorder=3)
        for rect, v in zip(bars, vals):
            if v > 0:
                ax.text(
                    rect.get_x() + rect.get_width() / 2,
                    rect.get_y() + rect.get_height() / 2,
                    str(int(v)), ha="center", va="center",
                    fontsize=8, color="white", fontweight="bold"
                )
        for i, lang in enumerate(present_langs):
            bottom_vals[lang] += vals[i]

    ax.set_xticks(list(x))
    ax.set_xticklabels([l.capitalize() for l in present_langs])
    ax.set_ylabel("Repositories")
    ax.set_title("Repos by Language & Star Tier")
    ax.legend(title="Star tier", loc="upper right")
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))

    # --- 1b: pipeline status funnel ---
    ax2 = axes[1]
    status_order = ["discovered", "cloned", "analysed", "skipped", "error"]
    status_counts = repos["status"].value_counts().reindex(status_order, fill_value=0)

    colours = [STATUS_PALETTE[s] for s in status_order]
    bars = ax2.barh(status_order[::-1],
                    [status_counts[s] for s in status_order[::-1]],
                    color=colours[::-1], zorder=3, height=0.55)

    for bar, s in zip(bars, status_order[::-1]):
        v = int(bar.get_width())
        if v > 0:
            ax2.text(bar.get_width() + max(status_counts) * 0.01, bar.get_y() + bar.get_height() / 2,
                     str(v), va="center", fontsize=9)

    ax2.set_xlabel("Repositories")
    ax2.set_title("Pipeline Status Funnel")
    ax2.set_xlim(0, max(status_counts) * 1.18)

    plt.tight_layout()
    save_or_show(fig, "01_corpus_composition", out_dir, show)


# ---------------------------------------------------------------------------
# SECTION 2 — Star Distribution
# ---------------------------------------------------------------------------

def plot_star_distribution(conn, out_dir, show):
    """
    Star counts on a log scale per language.
    Reveals whether the corpus is dominated by mega-repos or well-spread.
    """
    repos = df(conn, """
        SELECT language, stars
        FROM repositories
        WHERE stars IS NOT NULL
    """)
    if repos.empty or repos["language"].nunique() < 1:
        print("  [skip] No star data.")
        return

    present = [l for l in LANG_ORDER if l in repos["language"].values]
    palette  = {l: LANG_PALETTE[l] for l in present}

    fig, ax = plt.subplots(figsize=(10, 5), facecolor="#FAFAFA")

    sns.violinplot(
        data=repos[repos["language"].isin(present)],
        x="language", y="stars",
        order=present,
        palette=palette,
        inner="quartile",
        linewidth=0.8,
        ax=ax,
    )
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: f"{int(v):,}"
    ))
    ax.axhline(500, color="#555", linewidth=0.8, linestyle="--", alpha=0.6,
               label="500★ (core tier threshold)")
    ax.axhline(100, color="#999", linewidth=0.8, linestyle=":",  alpha=0.6,
               label="100★ (minimum threshold)")
    ax.set_xticklabels([l.capitalize() for l in present])
    ax.set_xlabel("")
    ax.set_ylabel("Stars (log scale)")
    ax.set_title("Star Distribution per Language")
    ax.legend(fontsize=8)

    plt.tight_layout()
    save_or_show(fig, "02_star_distribution", out_dir, show)


# ---------------------------------------------------------------------------
# SECTION 3 — Repository Age & Activity
# ---------------------------------------------------------------------------

def plot_age_and_activity(conn, out_dir, show):
    """
    3a. KDE of repo creation year per language — are we studying recent or legacy code?
    3b. KDE of months since last push — how active are these projects?
    """
    repos = df(conn, """
        SELECT language, created_at, pushed_at
        FROM repositories
        WHERE created_at IS NOT NULL
    """)
    if repos.empty:
        print("  [skip] No date data.")
        return

    repos["created_year"] = pd.to_datetime(repos["created_at"], errors="coerce").dt.year
    repos["months_since_push"] = (
        (pd.Timestamp.now(tz='UTC') - pd.to_datetime(repos["pushed_at"], errors="coerce", utc=True))
        .dt.days / 30
    ).clip(0, 60)

    present = [l for l in LANG_ORDER if l in repos["language"].values]
    palette  = {l: LANG_PALETTE[l] for l in present}

    fig, axes = plt.subplots(1, 2, figsize=(13, 5), facecolor="#FAFAFA")
    fig.suptitle("Repository Age & Activity", fontsize=14, fontweight="bold", y=1.01)

    # --- 3a: creation year KDE ---
    ax = axes[0]
    for lang in present:
        sub = repos[repos["language"] == lang]["created_year"].dropna()
        if len(sub) > 3:
            sns.kdeplot(sub, ax=ax, label=lang.capitalize(),
                        color=LANG_PALETTE[lang], linewidth=1.8, fill=True, alpha=0.15)
    ax.set_xlabel("Creation Year")
    ax.set_ylabel("Density")
    ax.set_title("When Were These Repos Created?")
    ax.legend(title="Language")
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))

    # --- 3b: months since last push ---
    ax2 = axes[1]
    for lang in present:
        sub = repos[repos["language"] == lang]["months_since_push"].dropna()
        if len(sub) > 3:
            sns.kdeplot(sub, ax=ax2, label=lang.capitalize(),
                        color=LANG_PALETTE[lang], linewidth=1.8, fill=True, alpha=0.15)
    ax2.set_xlabel("Months Since Last Push (capped at 60)")
    ax2.set_ylabel("Density")
    ax2.set_title("How Recently Were Repos Active?")
    ax2.legend(title="Language")
    ax2.axvline(12, color="#999", linewidth=0.8, linestyle="--", alpha=0.6,
                label="1 year")

    plt.tight_layout()
    save_or_show(fig, "03_age_and_activity", out_dir, show)


# ---------------------------------------------------------------------------
# SECTION 4 — Domain Distribution
# ---------------------------------------------------------------------------

def plot_domain_distribution(conn, out_dir, show):
    """
    Heatmap: language × domain normalised by row (language).
    Shows whether domain coverage is balanced or skewed.
    """
    repos = df(conn, """
        SELECT language, domain
        FROM repositories
        WHERE domain IS NOT NULL AND status NOT IN ('discovered')
    """)
    if repos.empty or repos["domain"].nunique() < 2:
        print("  [skip] Domain data not yet classified. Run `python pipeline.py classify`.")
        return

    domain_order = ["web", "library", "data", "cli", "infra", "other"]
    present_langs   = [l for l in LANG_ORDER   if l in repos["language"].values]
    present_domains = [d for d in domain_order if d in repos["domain"].values]

    pivot = (
        repos.groupby(["language", "domain"])
        .size()
        .unstack(fill_value=0)
        .reindex(index=present_langs, columns=present_domains, fill_value=0)
    )
    # Normalise per language
    pivot_norm = pivot.div(pivot.sum(axis=1), axis=0) * 100

    fig, axes = plt.subplots(1, 2, figsize=(14, 5), facecolor="#FAFAFA")
    fig.suptitle("Domain Distribution", fontsize=14, fontweight="bold", y=1.01)

    # Heatmap: % per language
    ax = axes[0]
    sns.heatmap(
        pivot_norm,
        annot=True, fmt=".0f", cmap="Blues",
        linewidths=0.4, linecolor="#E0E0E0",
        cbar_kws={"label": "% of language repos"},
        ax=ax,
    )
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_title("Domain Share per Language (%)")
    ax.set_yticklabels([l.capitalize() for l in present_langs], rotation=0)
    ax.set_xticklabels([d.capitalize() for d in present_domains], rotation=30, ha="right")

    # Absolute stacked bar
    ax2 = axes[1]
    bottom = [0] * len(present_langs)
    x = range(len(present_langs))
    for domain in present_domains:
        vals = [pivot.loc[l, domain] if domain in pivot.columns else 0
                for l in present_langs]
        ax2.bar(x, vals, bottom=bottom, color=DOMAIN_PALETTE.get(domain, "#CCC"),
                label=domain.capitalize(), zorder=3)
        bottom = [b + v for b, v in zip(bottom, vals)]

    ax2.set_xticks(list(x))
    ax2.set_xticklabels([l.capitalize() for l in present_langs])
    ax2.set_ylabel("Repositories")
    ax2.set_title("Absolute Counts by Domain")
    ax2.legend(title="Domain", bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=8)

    plt.tight_layout()
    save_or_show(fig, "04_domain_distribution", out_dir, show)


# ---------------------------------------------------------------------------
# SECTION 5 — Fork-to-Star Ratio
# ---------------------------------------------------------------------------

def plot_fork_star_ratio(conn, out_dir, show):
    """
    Fork/star ratio per language on log scale.
    High ratio → collaborative, contribution-driven project.
    Low ratio  → reference/showcase project (bookmarked, rarely forked).
    """
    repos = df(conn, """
        SELECT language, stars, forks
        FROM repositories
        WHERE stars > 0 AND forks IS NOT NULL
    """)
    if repos.empty:
        print("  [skip] No fork/star data.")
        return

    repos["fork_ratio"] = repos["forks"] / repos["stars"]
    present = [l for l in LANG_ORDER if l in repos["language"].values]
    palette  = {l: LANG_PALETTE[l] for l in present}

    fig, ax = plt.subplots(figsize=(9, 5), facecolor="#FAFAFA")

    sns.boxplot(
        data=repos[repos["language"].isin(present)],
        x="language", y="fork_ratio",
        order=present,
        palette=palette,
        linewidth=0.8,
        flierprops={"marker": "o", "markersize": 2,
                    "alpha": 0.4, "markeredgewidth": 0},
        ax=ax,
    )
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: f"{v:.2f}".rstrip("0").rstrip(".")
    ))
    ax.axhline(1.0, color="#888", linewidth=0.8, linestyle="--", alpha=0.7,
               label="forks = stars")
    ax.set_xticklabels([l.capitalize() for l in present])
    ax.set_xlabel("")
    ax.set_ylabel("Forks / Stars (log scale)")
    ax.set_title("Fork-to-Star Ratio by Language\n"
                 "(proxy for contribution culture vs. reference usage)")
    ax.legend(fontsize=8)

    plt.tight_layout()
    save_or_show(fig, "05_fork_star_ratio", out_dir, show)


# ---------------------------------------------------------------------------
# SECTION 6 — Fixture Overview (only if extraction has run)
# ---------------------------------------------------------------------------

def plot_fixture_overview(conn, out_dir, show):
    """
    6a. Fixture count per repo distribution (violin) per language.
    6b. Fixture type breakdown per language (stacked bar).
    """
    if not has_data(conn, "fixtures"):
        print("  [skip] No fixture data yet. Run `python pipeline.py extract`.")
        return

    fixtures = df(conn, """
        SELECT f.fixture_type, r.language, r.full_name
        FROM fixtures f
        JOIN repositories r ON f.repo_id = r.id
        WHERE r.status = 'analysed'
    """)
    if fixtures.empty:
        print("  [skip] Fixture table is empty.")
        return

    present = [l for l in LANG_ORDER if l in fixtures["language"].values]
    palette  = {l: LANG_PALETTE[l] for l in present}

    fig, axes = plt.subplots(1, 2, figsize=(14, 5), facecolor="#FAFAFA")
    fig.suptitle("Fixture Overview", fontsize=14, fontweight="bold", y=1.01)

    # --- 6a: fixtures per repo ---
    ax = axes[0]
    per_repo = (
        fixtures.groupby(["language", "full_name"])
        .size()
        .reset_index(name="fixture_count")
    )
    per_repo = per_repo[per_repo["language"].isin(present)]

    sns.violinplot(
        data=per_repo, x="language", y="fixture_count",
        order=present, palette=palette,
        inner="quartile", linewidth=0.8,
        ax=ax,
    )
    ax.set_xticklabels([l.capitalize() for l in present])
    ax.set_xlabel("")
    ax.set_ylabel("Fixtures per Repository")
    ax.set_title("How Many Fixtures Does Each Repo Have?")

    # --- 6b: fixture type stacked bar ---
    ax2 = axes[1]
    type_counts = (
        fixtures[fixtures["language"].isin(present)]
        .groupby(["language", "fixture_type"])
        .size()
        .reset_index(name="n")
    )
    pivot = (
        type_counts.pivot(index="language", columns="fixture_type", values="n")
        .reindex(present)
        .fillna(0)
    )
    pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100

    cmap = plt.get_cmap("Set2")
    types = list(pivot_pct.columns)
    colours = [cmap(i / max(len(types) - 1, 1)) for i in range(len(types))]
    bottom = [0.0] * len(present)
    x = range(len(present))

    for ftype, colour in zip(types, colours):
        vals = pivot_pct[ftype].tolist()
        ax2.bar(x, vals, bottom=bottom, color=colour,
                label=ftype.replace("_", " "), zorder=3)
        bottom = [b + v for b, v in zip(bottom, vals)]

    ax2.set_xticks(list(x))
    ax2.set_xticklabels([l.capitalize() for l in present])
    ax2.set_ylabel("% of fixtures")
    ax2.set_title("Fixture Type Distribution")
    ax2.legend(title="Type", bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=7)

    plt.tight_layout()
    save_or_show(fig, "06_fixture_overview", out_dir, show)


# ---------------------------------------------------------------------------
# SECTION 7 — Mock Prevalence (only if extraction has run)
# ---------------------------------------------------------------------------

def plot_mock_prevalence(conn, out_dir, show):
    """
    7a. % of fixtures containing at least one mock, per language.
    7b. Mock framework market share per language.
    """
    if not has_data(conn, "mock_usages"):
        print("  [skip] No mock data yet. Run `python pipeline.py extract`.")
        return

    fixtures = df(conn, """
        SELECT f.id, r.language,
               (SELECT COUNT(*) FROM mock_usages m WHERE m.fixture_id = f.id) AS mock_count
        FROM fixtures f
        JOIN repositories r ON f.repo_id = r.id
        WHERE r.status = 'analysed'
    """)
    if fixtures.empty:
        print("  [skip] Fixture table is empty.")
        return

    mocks = df(conn, """
        SELECT m.framework, r.language
        FROM mock_usages m
        JOIN repositories r ON m.repo_id = r.id
        WHERE r.status = 'analysed'
    """)

    present = [l for l in LANG_ORDER if l in fixtures["language"].values]
    palette  = {l: LANG_PALETTE[l] for l in present}

    fig, axes = plt.subplots(1, 2, figsize=(13, 5), facecolor="#FAFAFA")
    fig.suptitle("Mocking Practices", fontsize=14, fontweight="bold", y=1.01)

    # --- 7a: prevalence ---
    ax = axes[0]
    fixtures["has_mock"] = fixtures["mock_count"] > 0
    prevalence = (
        fixtures[fixtures["language"].isin(present)]
        .groupby("language")["has_mock"]
        .mean()
        .reindex(present) * 100
    )
    bars = ax.bar(
        range(len(present)),
        prevalence.values,
        color=[LANG_PALETTE[l] for l in present],
        zorder=3, width=0.55,
    )
    for bar, pct in zip(bars, prevalence.values):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.8,
                f"{pct:.1f}%", ha="center", va="bottom", fontsize=9)
    ax.set_xticks(range(len(present)))
    ax.set_xticklabels([l.capitalize() for l in present])
    ax.set_ylabel("% of fixtures with ≥1 mock")
    ax.set_ylim(0, min(100, prevalence.max() * 1.25 + 5))
    ax.set_title("Mock Prevalence Inside Fixtures")

    # --- 7b: framework share ---
    ax2 = axes[1]
    if not mocks.empty:
        fw_counts = (
            mocks[mocks["language"].isin(present)]
            .groupby(["language", "framework"])
            .size()
            .reset_index(name="n")
        )
        pivot = (
            fw_counts.pivot(index="language", columns="framework", values="n")
            .reindex(present)
            .fillna(0)
        )
        pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100

        cmap2 = plt.get_cmap("tab10")
        fws = list(pivot_pct.columns)
        bottom = [0.0] * len(present)
        for i, fw in enumerate(fws):
            vals = pivot_pct[fw].tolist()
            ax2.bar(range(len(present)), vals, bottom=bottom,
                    color=cmap2(i / max(len(fws) - 1, 1)),
                    label=fw.replace("_", " "), zorder=3)
            bottom = [b + v for b, v in zip(bottom, vals)]

        ax2.set_xticks(range(len(present)))
        ax2.set_xticklabels([l.capitalize() for l in present])
        ax2.set_ylabel("% of mock usages")
        ax2.set_title("Mock Framework Share")
        ax2.legend(title="Framework", bbox_to_anchor=(1.01, 1),
                   loc="upper left", fontsize=7)

    plt.tight_layout()
    save_or_show(fig, "07_mock_prevalence", out_dir, show)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="FixtureDB EDA plots")
    parser.add_argument("--db",   default=str(DB_PATH),
                        help="Path to corpus.db")
    parser.add_argument("--out",  default=str(DEFAULT_OUT),
                        help="Base output directory (a timestamped subfolder is created inside)")
    parser.add_argument("--show", action="store_true",
                        help="Display plots interactively instead of saving")
    args = parser.parse_args()

    if args.show:
        out_dir = None
    else:
        # Each run gets its own subfolder: output/eda/2026-03-21_14-05-32/
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        out_dir = Path(args.out) / timestamp
        out_dir.mkdir(parents=True, exist_ok=True)

        # Keep output/eda/latest/ pointing to the most recent run
        latest = Path(args.out) / "latest"
        if latest.exists() or latest.is_symlink():
            latest.unlink()
        try:
            latest.symlink_to(timestamp)   # relative symlink
        except (OSError, NotImplementedError):
            pass   # Windows without developer mode — skip symlink silently
    conn = load_db(Path(args.db))
    setup_style()

    total = df(conn, "SELECT COUNT(*) n FROM repositories").iloc[0]["n"]
    analysed = df(conn, "SELECT COUNT(*) n FROM repositories WHERE status='analysed'").iloc[0]["n"]
    print(f"\nFixtureDB EDA — {int(total):,} repos in DB  ({int(analysed):,} analysed)")
    print(f"Output → {out_dir or 'screen'}\n")

    plots = [
        ("Corpus Composition",    plot_corpus_composition),
        ("Star Distribution",     plot_star_distribution),
        ("Age & Activity",        plot_age_and_activity),
        ("Domain Distribution",   plot_domain_distribution),
        ("Fork/Star Ratio",       plot_fork_star_ratio),
        ("Fixture Overview",      plot_fixture_overview),
        ("Mock Prevalence",       plot_mock_prevalence),
    ]

    for name, fn in plots:
        print(f"[{name}]")
        fn(conn, out_dir, args.show)

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()