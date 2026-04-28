# Database Schema

FixtureDB provides data in two formats optimized for different use cases:

## Data Formats Comparison

| Aspect | **SQLite** (`fixtures.db`) | **CSV Exports** |
|--------|--------|---------|
| **Purpose** | Complete reproducible dataset with all fields | Curated quantitative metrics for analysis |
| **Tables** | 4 normalized (repositories, test_files, fixtures, mock_usages) | 5 denormalized CSVs (fixtures, mock_usages, repositories, test_files) + language-specific variants |
| **Includes** | Raw source, internal classifications, error logs | Quantitative metrics only (no raw_source, categories, classifications) |
| **Best for** | Verification, reproducibility, source inspection | Paper analysis, spreadsheet workflows, pandas/R |

---

## SQLite Database (fixtures.db)

**Setup:** Standard SQLite 3 with WAL mode (safe read-only access during writes)

### Table Overview

| Table | Rows | Relationship | Columns |
|-------|------|--------------|---------|
| `repositories` | 160 | Root | github_id, full_name, language, stars, forks, domain, status, pinned_commit, num_test_files, num_fixtures, num_mock_usages |
| `test_files` | ~228K | FK → repositories.id | repo_id, relative_path, language, file_loc, num_fixtures, total_fixture_loc |
| `fixtures` | ~40.7K | FK → test_files.id, repo_id | file_id, name, fixture_type, scope, loc, cyclomatic_complexity, cognitive_complexity, max_nesting_depth, num_objects_instantiated, num_external_calls, num_parameters, reuse_count, has_teardown_pair, raw_source, category, framework |
| `mock_usages` | ~12.8K | FK → fixtures.id, repo_id | fixture_id, framework, mock_style, target_identifier, target_layer, num_interactions_configured, raw_snippet |

**Entity Relationship:**
```
repositories (1) ──< test_files (1) ──< fixtures (1) ──< mock_usages
      │                                      │
      └──────────────── repo_id ─────────────┘  (denormalized FK)
```

### Key Columns for Analysis

**fixtures table (primary analysis table):**
- **structure:** `loc`, `cyclomatic_complexity` (via Lizard), `cognitive_complexity` (via complexipy)
- **design:** `scope`, `num_parameters`, `reuse_count`, `has_teardown_pair`
- **context:** `fixture_type`, `framework`, `name`
- **internal (excluded from CSV):** `raw_source`, `category`, `max_nesting_depth`, `num_objects_instantiated`, `num_external_calls`

**mock_usages table:**
- `framework` (detection pattern: unittest_mock, pytest_mock, mockito, jest, sinon, etc.)
- `target_identifier` (string passed to mock call)
- `num_interactions_configured` (behavior configuration count)
- **internal (excluded from CSV):** `mock_style`, `target_layer`, `raw_snippet`

**Metric Details:** See [Metrics Reference](metrics-reference.md) for calculation methodology and tool documentation.

---

## CSV Exports

### Files Generated

```
export/fixturedb_v<version>_<date>/
├── fixtures.db                      ← SQLite database
├── fixtures.csv                     ← All fixtures, all languages
├── fixtures_python.csv              ← Python only (~4.9K rows)
├── fixtures_java.csv                ← Java only (~11.2K rows)
├── fixtures_javascript.csv          ← JavaScript only (~5.5K rows)
├── fixtures_typescript.csv          ← TypeScript only (~19K rows)
├── mock_usages.csv                  ← All mock calls (~12.8K rows)
├── repositories.csv                 ← Repository metadata (160 rows)
├── test_files.csv                   ← Test files analyzed (~228K rows)
└── README.txt
```

### What's Excluded

**Never exported to CSV:** `raw_source`, `category`, `mock_style`, `target_layer`, `raw_snippet`  
(Use SQLite database if you need to inspect original code or internal classifications)

### Key Tables

**fixtures.csv** — Main analysis table; one row per fixture
- **ID columns:** id, repo_id, file_id
- **Description:** name, fixture_type, scope, language, framework
- **Structure metrics:** loc, cyclomatic_complexity, cognitive_complexity, max_nesting_depth
- **Design metrics:** num_objects_instantiated, num_external_calls, num_parameters, reuse_count, has_teardown_pair
- **Context:** repo_full_name, stars, domain

**mock_usages.csv** — One row per mock framework call; join to fixtures.csv via fixture_id
- **ID columns:** id, fixture_id, repo_id
- **Detection:** framework, target_identifier, num_interactions_configured

**repositories.csv** — One row per analyzed repository
- **Metadata:** full_name, language, stars, forks, created_at, pushed_at, domain
- **Counts:** num_test_files, num_fixtures, num_mock_usages, num_contributors

**test_files.csv** — One row per test file analyzed
- **Path:** relative_path, language
- **Metrics:** file_loc, num_test_funcs, num_fixtures, total_fixture_loc

---

## Usage Guidelines

**Use CSVs if:**
- Analyzing with Excel, Tableau, pandas, or R
- Writing a paper (clean, quantitative-only format)
- You don't need raw source code or internal details

**Use SQLite if:**
- Verifying extraction decisions (inspect raw_source)
- Performing complex joins across tables
- Tracing fixture → mock → repository relationships
- Reproducing results (includes error_message, pinned_commit)
