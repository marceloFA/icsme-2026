# Data Collection Process

**Collection Metadata**  
- **Collection Period**: April 1–2, 2026
- **Repositories Collected**: 160 (4 languages: Python, Java, JavaScript, TypeScript)
- **Total Fixtures Extracted**: 40,672
- **Extraction Timestamp Range**: 2026-04-01 20:16:59 to 2026-04-01 23:18:03 UTC
- **Reproducibility**: All collection parameters pinned in code; repos at specific commits preserved

## Tool Versions (for Reproducibility)

The following tool versions were used during extraction. To exactly replicate the corpus, use identical versions:

```
GitHub API:                    v3 REST API

AST Parsing:
  - Tree-sitter core:          v0.21.0+
  - tree-sitter-python         v0.21.0+
  - tree-sitter-java           v0.21.0+
  - tree-sitter-javascript     v0.21.0+
  - tree-sitter-typescript     v0.21.0+

Code Metrics:
  - Lizard                      v1.21.3+ (cyclomatic complexity, LOC, 
                                          parameters, external call count)
  - complexipy                  v5.0.0+ (Python cognitive complexity, SonarQube-standard)

Runtime:
  - Python                      3.8+
  - SQLite                      3.x
```

**Key Tools & Rationale:**

- **Lizard** (v1.21.3+): Handles cyclomatic complexity, cognitive complexity fallback, LOC, parameters, and external function call detection across all languages. Reduces custom metric code while maintaining reproducibility via industry-standard tool.

- **cognitive-complexity** (v1.3.0+): Python-specific SonarQube-standard cognitive complexity implementation. Provides accurate nesting-depth-weighted complexity for Python; other languages use Lizard-based formula fallback.

- **Tree-sitter** (v0.21.0+): AST parsing for fixture detection, scope analysis, and code structure metrics across 5 languages. Provides consistent abstract syntax representation independent of language syntax quirks.

See [requirements.txt](../requirements.txt) for exact pinned versions used in this execution.

## Collection Strategy

**Why This Matters for Reproducibility:**
- GitHub API evolves; newer versions may return different results
- Tree-sitter grammars receive updates that change AST structure
- Complexity metric implementations can change between versions
- We pinned all versions to ensure bit-for-bit reproducibility

**Time Window:**
Corpus was collected over ~3 hours (April 1–2, 2026 20:16–23:18 UTC). During this window:
- GitHub API availability was stable
- No major GitHub service incidents occurred
- All 160 repositories successfully cloned and analyzed (Go not included by design)

---

## Collection Pipeline

The pipeline runs in five sequential phases. Each phase is idempotent — if it
is interrupted and restarted, already-completed work is skipped.

## Phase 1 — Repository Loading from SEART-GHS (`load`)

Rather than querying GitHub directly, repositories are loaded from pre-scraped 
data provided by [SEART-GHS](https://seart-ghs.si.usi.ch/), a curated research 
dataset of GitHub repositories.

### Why SEART-GHS?

Direct GitHub API searching poses three challenges for reproducible research:

1. **Non-determinism**: GitHub API results can vary across queries depending on 
   indexing state, making it difficult to guarantee the same repos are collected 
   in replications.

2. **Temporal Instability**: Repositories are continuously created, deleted, and 
   modified on GitHub. A search result set from one date cannot be reliably 
   recreated months later.

3. **API Rate Limits**: Exhaustive collection requires extensive API calls, 
   consuming rate limit quota. Lower-quota accounts hit limits quickly.

**SEART-GHS solves all three** by:
- Publishing a **fixed, immutable dataset** of repositories scraped at a specific time
- Documenting **exact filters** used (language, stars, forks, etc.)
- Making data **freely downloadable** without rate limits

This makes FixtureDB reproducible: any researcher can download the same CSV 
files and replicate our exact collection 1:1.

### Data Source and Format

CSV files are obtained from https://seart-ghs.si.usi.ch/ and saved locally 
in the `github-search/` directory:

```
github-search/
  ├── python-results.csv.gz       # ~3000 Python repos
  ├── java-results.csv.gz         # ~2500 Java repos
  ├── javascript-results.csv.gz   # ~1800 JavaScript repos
  └── typescript-results.csv.gz   # ~800 TypeScript repos
```

Each CSV contains columns: `id`, `name`, `isFork`, `commits`, `stargazers`, 
`isArchived`, `mainLanguage`, `createdAt`, `pushedAt`, `clone_url`, and others 
provided by SEART-GHS export.

### Filtering on Load

Repositories loaded from the CSV are filtered using the same quality criteria 
as the original GitHub search approach:

- **Not archived** (`isArchived = false`)
- **Not a fork** (`isFork = false`)  
- **Minimum commits** (≥ 100 by default, configurable per language in `config.py`)
- **Not excluded by keyword** (repos with names/descriptions matching 
  `tutorial`, `homework`, `exercise`, `bootcamp`, `demo`, `awesome-`, etc. 
  are silently dropped)

Repositories passing these filters are written to the `repositories` table 
with `status = 'discovered'` and are ready for Phase 2 cloning.

### How to Update the Dataset

When SEART-GHS publishes newer versions or when you want to collect different 
languages:

1. **Visit** https://seart-ghs.si.usi.ch/
2. **Configure filters** (language, minimum stars, minimum commits, etc.)
3. **Download results** as CSV (gzip-compressed)
4. **Place in** `github-search/` folder with naming pattern: `{language}-results.csv.gz`
5. **Run** the pipeline: `python pipeline.py search --language python`

The pipeline will automatically detect the CSV, apply filters, and load 
repositories into the database. Existing repos are updated in-place; new repos 
are inserted.

### Command Reference

```bash
# Load all repos from python-results.csv.gz
python pipeline.py load --language python

# Load only first 1000 repos (useful for testing)
python pipeline.py load --language python --max 1000

# Load from all languages
python pipeline.py load
```

### Documentation References

- **SEART-GHS**: https://github.com/seart-group/ghs (GitHub repository)
- **SEART-GHS Web UI**: https://seart-ghs.si.usi.ch/ (Search and download interface)

## Phase 2 — Cloning (`clone`)

Repositories in `discovered` status are shallow-cloned (`git clone --depth 1`)
in parallel using a configurable thread pool (default: 4 workers).
After cloning, two **quality filters** are applied to ensure we capture
repositories with mature testing practices:

- **Commit count** ≥ 50: the pipeline fetches up to 500 commits of history
  to get a realistic count. This threshold filters out prototype and toy
  projects. Repos below the threshold are marked `skipped` and the clone is deleted.
- **Test file count** ≥ 5: path and suffix heuristics are used to count
  test files (Ahmed et al., 2025). Repos with fewer test files suggest
  minimal testing culture and are marked `skipped`. This aligns with observed
  patterns in large-scale test suite studies (Pan et al., 2025).

Repos passing both filters are marked `cloned`. The clone directory is kept
until extraction completes.

## Phase 3 — Extraction (`extract`)

For each `cloned` repository the extractor:

1. Walks all test files (identified by path and suffix heuristics,
   skipping `vendor/`, `node_modules/`, `dist/`, etc.)
2. Reads each file's source bytes
3. Parses it with the appropriate **Tree-sitter grammar**
4. Runs language-specific AST queries to find fixture definitions
5. For each fixture, runs regex-based mock detection over the fixture's
   source text
6. Writes results to `test_files`, `fixtures`, and `mock_usages`
7. Marks the repo `analysed` and deletes the local clone

Repos where zero fixtures are found after full extraction are marked `skipped`.

## Phase 4 — Domain Classification (`classify`)

A keyword-based heuristic assigns each repository a domain label by matching
against its name, description, and GitHub topics. Labels: `web`, `data`,
`cli`, `infra`, `library`, `other`. This runs in-database and takes seconds.

## Phase 5 — Export (`export`)

Produces a versioned zip file ready for Zenodo deposit. **This phase creates two complementary formats optimized for different use cases**:

**SQLite Database** (`fixturedb.sqlite`) — For reproducibility verification and raw source inspection:
- `fixturedb.sqlite` — the full database with all fields, internal classifications, and raw source code
- See [Database Schema — SQLite Section](../architecture/03-database-schema.md)

**CSV Exports** (`.csv` files) — For spreadsheet and statistical analysis:
- `repositories.csv`, `test_files.csv`, `fixtures.csv`, `mock_usages.csv` — core tables
- `fixtures_python.csv`, `fixtures_java.csv`, `fixtures_javascript.csv`, `fixtures_typescript.csv` — language-specific
- `stats.txt` — high-level statistics (per-language counts for paper tables)
- `README.txt` — schema documentation

**Key Difference**: The `raw_source` column (full fixture source code) is excluded from CSVs by default because it is large and already available in the SQLite file. Pass `--include-source` to include raw source in `fixtures.csv` if needed.

See [Database Schema — CSV Export Schema](../architecture/03-database-schema.md) for detailed column documentation and [Using the Dataset for Research](../usage/09-usage.md) for guidance on which format to use.
