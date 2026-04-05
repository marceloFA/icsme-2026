# CSV User Guide

**For researchers who want to analyze FixtureDB without using SQL or SQLite**

---

## Overview

FixtureDB provides CSV exports of the main analysis tables across 4 programming languages. This guide explains:
- What each column means
- How to use them in Excel, Python (pandas), or R
- How to link tables together
- Common analyses and their queries

**Go Language Note**: By configuration, FixtureDB contains **zero Go data** in all CSV exports and database tables. Go repositories are excluded due to unvalidated fixture detection heuristics. The collection code (`detector.py`, `config.py`) retains Go extraction logic for reference, but no Go data is present in the published dataset. All CSV files below contain only 4 languages: Python, Java, JavaScript, and TypeScript. See [Data Collection — Go Language Handling](04-data-collection.md#go-language-handling) and [Limitations](12-limitations.md#go-language-exclusion-v2) for details.

---

## Getting Started

### Where to Find CSV Files

In the Zenodo archive (or in your export directory if building locally):
```
fixturedb.zip
├── fixtures.csv                    ← Main table (1 row per fixture)
├── mock_usages.csv                 ← Mock calls (1 row per mock)
├── repositories.csv                ← Repository metadata
├── test_files.csv                  ← Test file listing
├── fixtures_python.csv             ← Python fixtures only
├── fixtures_java.csv               ← Java fixtures only
├── fixtures_javascript.csv         ← JavaScript fixtures only
├── fixtures_typescript.csv         ← TypeScript fixtures only
└── README.txt                      ← Quick reference
```

### Quick Import

**Excel:**
- Right-click → Open With → Excel
- Data will auto-import

**Python (pandas):**
```python
import pandas as pd
df = pd.read_csv('fixtures.csv')
print(df.head())
```

**R:**
```r
df <- read.csv('fixtures.csv')
head(df)
```

---

## Table 1: fixtures.csv (Main Analysis Table)

**What it contains:** One row per test fixture definition (40,672 rows)

### Column Reference

| Column | Type | Units | Description | Example |
|--------|------|-------|-------------|---------|
| `id` | Integer | — | Unique fixture identifier (primary key) | 12345 |
| `repo_id` | Integer | — | Repository ID (links to repositories.csv) | 42 |
| `file_id` | Integer | — | Test file ID (links to test_files.csv) | 987 |
| `name` | Text | — | Fixture function name | `setup_database` |
| `language` | Text | — | Programming language | `python`, `java`, `javascript`, `typescript` |
| `fixture_type` | Text | — | Detection pattern used | See "Fixture Types" below |
| `scope` | Text | — | When fixture runs relative to tests | `per_test`, `per_class`, `per_module`, `global` |
| `start_line` | Integer | lines | First line of fixture in source file (1-indexed) | 150 |
| `end_line` | Integer | lines | Last line of fixture in source file (1-indexed) | 165 |
| `loc` | Integer | lines | **L**ines **O**f **C**ode (non-blank, non-comment) | 12 |
| `cyclomatic_complexity` | Integer | complexity | **McCabe cyclomatic complexity** (1 = no branching) | 3 |
| `cognitive_complexity` | Integer | complexity | **SonarQube cognitive complexity** (nesting-weighted) | 5 |
| `max_nesting_depth` | Integer | levels | Maximum block nesting (if/for/while/try statements) | 2 |
| `num_objects_instantiated` | Integer | count | Estimated object creations in fixture | 4 |
| `num_external_calls` | Integer | count | Estimated I/O/API calls (DB, HTTP, files, env) | 2 |
| `num_parameters` | Integer | count | Number of function parameters | 1 |
| `reuse_count` | Integer | count | How many test functions use this fixture | 12 |

### Complexity Metrics Explained

**McCabe Cyclomatic Complexity** (`cyclomatic_complexity`)
- Measures branching: 1 = straight line, no branches
- Formula: 1 + (number of decision points: if, switch, for, while)
- Range in FixtureDB: 1–36
- Interpretation:
  - 1–2: Simple, easy to understand
  - 3–5: Moderate complexity, acceptable
  - 6–10: Complex, consider refactoring
  - 10+: Very complex, recommend refactoring

**SonarQube Cognitive Complexity** (`cognitive_complexity`)
- Refinement of cyclomatic that penalizes nested structures harder
- Better correlates with developer cognition
- Typically lower than cyclomatic (nesting reduces it)
- Range in FixtureDB: 0–22

**Max Nesting Depth** (`max_nesting_depth`)
- How deeply nested are the control structures?
- 1 = no nesting (just sequential code)
- 3+ = significant nesting
- Correlates strongly with cyclomatic (see RQ5 in docs/18-example-analyses.md)

### Fixture Types

| Value | Language | Trigger | Meaning |
|-------|----------|---------|---------|
| `pytest_decorator` | Python | `@pytest.fixture` | pytest decorator-syntax fixture |
| `unittest_setup` | Python | `setUp`, `tearDown`, etc. | unittest class setup methods |
| `junit5_before_each` | Java | `@BeforeEach` | JUnit 5: per-test setup |
| `junit5_before_all` | Java | `@BeforeAll` | JUnit 5: per-class setup |
| `junit4_before` | Java | `@Before` | JUnit 4: per-test setup |
| `before_each` | JS/TS | `beforeEach(...)` | Modern test framework |
| `before_all` | JS/TS | `beforeAll(...)` | Modern test framework |
| `test_main` | Go | `func TestMain(...)` | Go's test initialization |
| `go_helper` | Go | Heuristic | Non-test function called by ≥2 tests |

(See [docs/11-detection.md](11-detection.md) for complete list and detection methodology)

#### ⚠️ Important Note on Go Helper Detection
The `go_helper` fixture type is detected using a heuristic pattern (non-test functions called by ≥2 test functions) because Go lacks explicit fixture syntax. **This detection has not yet been formally validated for precision/recall.** 

When filtering on `fixture_type = 'go_helper'`:
- Precision/recall are unknown (validation in progress)
- Results may include false positives (regular helper functions mistaken for fixtures)
- Results may include false negatives (actual fixtures missed)
- For precise Go fixture analysis, consider additional manual review or contact authors for validation results

**Recommendation**: Do not use Go fixtures alone for quantitative comparisons without understanding this limitation. Include validation status caveats in any publications using `go_helper` fixtures.

### Scope Values Explained

| Scope | Meaning | When It Runs | Use Case |
|-------|---------|--------------|----------|
| `per_test` | Within test | Before each individual test | Most common; isolated setup |
| `per_class` | Within class/suite | Before each test class/suite | Shared setup for class tests |
| `per_module` | Entire module | Once per test module/file | Expensive setup (DB connection) |
| `global` | Application | Once at startup | Very rare; global state setup |

### Missing Values

- **`NULL`** in complexity columns: Indicates error during metric calculation
  - Rare (< 0.1% of fixtures)
  - Safe to exclude or set to 0 for aggregates
- **`0`** in count columns: Legitimate (fixture doesn't instantiate objects, call external APIs, etc.)
  - Use `IS NULL` to find errors, not `= 0`

### Row Count by Language

From FixtureDB (40,672 total after excluding Go):
- Python: 4,915
- Java: 11,287
- JavaScript: 5,521
- TypeScript: 18,949

---

## Table 2: mock_usages.csv

**What it contains:** One row per mock/stub/spy/fake call detected in a fixture (9,202 rows)

### Column Reference

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `id` | Integer | Unique mock usage ID | 45678 |
| `fixture_id` | Integer | Fixture this mock is in (links to fixtures.csv) | 12345 |
| `repo_id` | Integer | Repository this mock is in | 42 |
| `framework` | Text | Mock framework detected | `unittest_mock`, `mockito`, `jest`, etc. |
| `target_identifier` | Text | What's being mocked (class/module name) | `"mymodule.HttpClient"` |

### Key Points

- Join to `fixtures.csv` on `fixture_id`
- Multiple rows per fixture if fixture uses multiple mocks
- `target_identifier` is a string; may need parsing for analysis
- `framework` values: see RQ4 in [docs/18-example-analyses.md](18-example-analyses.md)

### Common Analyses

**Q: What fraction of fixtures use mocking?**
```sql-like (Excel/pandas logic):
COUNT(DISTINCT fixture_id) / (SELECT COUNT(*) FROM fixtures) as adoption_rate
```

**Q: Which mock frameworks are most common?**
```
GROUP BY framework
COUNT(*) as count
ORDER BY count DESC
```

---

## Table 3: repositories.csv

**What it contains:** Metadata about the 160 analyzed repositories (4 languages)

### Key Columns

| Column | Description | Example |
|--------|-------------|---------|
| `id` | Unique repo ID | 42 |
| `full_name` | GitHub slug | `"pytest-dev/pytest"` |
| `language` | Programming language | `python` |
| `stars` | Star count at collection time | 54000 |
| `forks` | Fork count | 8500 |
| `domain` | Inferred category | `web`, `data`, `cli`, `infra`, `library`, `other` |
| `star_tier` | `core` (≥500 stars) or `extended` (100–499) | `core` |
| `pinned_commit` | Git commit SHA we analyzed | `abc123def456...` |
| `status` | Collection status | Usually `analysed` |
| `num_fixtures` | How many fixtures in this repo | 187 |
| `num_mock_usages` | How many mock calls | 42 |
| `created_at` | Repo creation date (ISO 8601) | `2015-03-12` |
| `pushed_at` | Last commit date | `2026-03-31` |

---

## Table 4: test_files.csv

**What it contains:** Metadata about test files analyzed (228,971 rows)

**Key columns:**
- `id`: File ID
- `repo_id`: Repository ID (link to repositories.csv)
- `relative_path`: Path within repo (e.g., `src/tests/test_app.py`)
- `file_loc`: Total lines of code in file
- `num_fixtures`: Fixtures found in this file
- `language`: Same as repo language

---

## Language-Specific CSVs

For convenience, language-specific CSVs are provided:
- `fixtures_python.csv` (4,915 rows)
- `fixtures_java.csv` (11,287 rows)
- `fixtures_javascript.csv` (5,521 rows)
- `fixtures_typescript.csv` (18,949 rows)

Only contains fixtures for that language; all columns identical to `fixtures.csv`.

---

## How to Use CSVs in Excel

### Task 1: Find the most complex fixtures

1. Open `fixtures.csv` in Excel
2. Click any cell in the data
3. Data → Sort & Filter → Sort
4. Sort by `cyclomatic_complexity` (Descending)
5. Top 20 rows show most complex fixtures

### Task 2: Analysis by language

1. Data → Pivot Table
2. Rows: `language`
3. Values: `cyclomatic_complexity` (Average), `loc` (Average), `reuse_count` (Sum)
4. See complexity & patterns by language

### Task 3: Fixtures using mocking

1. Use `mock_usages.csv`
2. Count unique `fixture_id` values
3. Compare to total fixtures in `fixtures.csv`
4. Calculate adoption rate = mocking fixtures / total fixtures

---

## How to Use CSVs in Python (pandas)

### Basic Import
```python
import pandas as pd

# Load fixtures
fixtures = pd.read_csv('fixtures.csv')
mocks = pd.read_csv('mock_usages.csv')
repos = pd.read_csv('repositories.csv')

# Quick overview
print(fixtures.info())
print(fixtures.describe())
```

### Complexity Analysis by Language
```python
# Average complexity by language
complexity_by_lang = fixtures.groupby('language').agg({
    'cyclomatic_complexity': 'mean',
    'loc': 'mean',
    'num_parameters': 'mean'
}).round(2)

print(complexity_by_lang)
```

### Mock Adoption
```python
# Count fixtures with mocks
mock_fixture_ids = set(mocks['fixture_id'].unique())
total_fixtures = len(fixtures)
fixtures_with_mocks = len(mock_fixture_ids)

adoption_rate = fixtures_with_mocks / total_fixtures
print(f"Mock adoption: {adoption_rate:.1%}")

# By language
for lang in fixtures['language'].unique():
    lang_fixtures = fixtures[fixtures['language'] == lang]
    lang_mock_ids = mock_fixture_ids & set(lang_fixtures['id'])
    rate = len(lang_mock_ids) / len(lang_fixtures)
    print(f"{lang:12} {rate:.1%}")
```

### Correlation Analysis
```python
# Is nesting depth a good predictor of cyclomatic complexity?
correlation = fixtures['max_nesting_depth'].corr(fixtures['cyclomatic_complexity'])
print(f"Correlation(nesting, CC): {correlation:.3f}")

# Fixtures with unusually high nesting
outliers = fixtures[fixtures['max_nesting_depth'] > 5]
print(f"Fixtures with nesting > 5: {len(outliers)}")
print(outliers[['name', 'language', 'max_nesting_depth', 'cyclomatic_complexity']])
```

### Find Top Reused Fixtures
```python
# Most frequently reused fixtures
top_reused = fixtures.nlargest(10, 'reuse_count')[
    ['name', 'language', 'reuse_count', 'loc', 'cyclomatic_complexity']
]
print(top_reused)
```

### Linking Tables
```python
# Get complexity stats by repository
repo_stats = fixtures.merge(
    repos[['id', 'full_name', 'stars', 'domain']], 
    left_on='repo_id', 
    right_on='id'
).groupby('full_name').agg({
    'cyclomatic_complexity': 'mean',
    'loc': 'sum',
    'stars': 'first'
}).sort_values('cyclomatic_complexity', ascending=False)

print(repo_stats.head(10))
```

---

## How to Use CSVs in R

### Basic Import
```r
library(tidyverse)

fixtures <- read_csv('fixtures.csv')
mocks <- read_csv('mock_usages.csv')
repos <- read_csv('repositories.csv')

# Overview
head(fixtures)
summary(fixtures)
```

### Complexity by Language
```r
fixtures %>%
  group_by(language) %>%
  summarize(
    mean_cc = mean(cyclomatic_complexity, na.rm = TRUE),
    mean_loc = mean(loc, na.rm = TRUE),
    mean_params = mean(num_parameters, na.rm = TRUE)
  ) %>%
  arrange(desc(mean_cc))
```

### Mock Adoption
```r
mock_fixture_ids <- unique(mocks$fixture_id)
total_fixtures <- nrow(fixtures)
adoption_rate <- length(mock_fixture_ids) / total_fixtures

cat(sprintf("Mock adoption: %.1f%%\n", adoption_rate * 100))

# By language
fixtures %>%
  mutate(has_mock = id %in% mock_fixture_ids) %>%
  group_by(language) %>%
  summarize(
    adoption_rate = mean(has_mock),
    .groups = 'drop'
  ) %>%
  arrange(desc(adoption_rate))
```

### Visualization
```r
# Complexity distribution by language
ggplot(fixtures, aes(x = language, y = cyclomatic_complexity)) +
  geom_boxplot() +
  labs(title = "Fixture Complexity by Language",
       x = "Language",
       y = "Cyclomatic Complexity") +
  theme_minimal()

# Scatter: LOC vs Complexity
ggplot(fixtures, aes(x = loc, y = cyclomatic_complexity, color = language)) +
  geom_point(alpha = 0.3) +
  geom_smooth(method = 'lm', se = FALSE) +
  labs(title = "LOC vs Complexity by Language") +
  theme_minimal()
```

---

## Common Analyses

### Q1: What's the distribution of fixture complexity?
```excel: Data → Pivot Table → Values: cyclomatic_complexity (Count, Binned by ranges)
pandas: pd.cut(fixtures['cyclomatic_complexity'], bins=[0,2,5,10,50]).value_counts()
R: cut(fixtures$cyclomatic_complexity, breaks = c(0, 2, 5, 10, 50)) %>% table()
```

### Q2: Do more complex fixtures get reused more?
```excel: Create scatter plot: X=cyclomatic_complexity, Y=reuse_count
pandas: pd.scatter(fixtures, x='cyclomatic_complexity', y='reuse_count')
R: plot(fixtures$cyclomatic_complexity, fixtures$reuse_count)
```

### Q3: Which repositories have the most complex fixtures on average?
```pandas: 
fixtures.merge(repos[['id', 'full_name']], left_on='repo_id', right_on='id') \
  .groupby('full_name')['cyclomatic_complexity'].mean() \
  .sort_values(ascending=False) \
  .head(10)
```

### Q4: What's the relationship between nesting depth and cognitive complexity?
```pandas: 
correlation = fixtures['max_nesting_depth'].corr(fixtures['cognitive_complexity'])
print(f"Correlation: {correlation:.3f}")
```

### Q5: How many fixtures perform I/O (external calls)?
```pandas:
fixtures[fixtures['num_external_calls'] > 0].shape[0]
# And by language:
fixtures.groupby('language')['num_external_calls'].apply(lambda x: (x > 0).sum())
```

---

## Data Quality Notes

**Missing Values:**
- `NULL` in complexity fields: Mathematical error during calculation (< 0.1%)
- `0` in count fields: Legitimate (fixture doesn't instantiate objects)
- Missing `target_identifier` in mocks: Rare, indicates detection ambiguity

**Consistency Checks:**
- All `fixture_id` in `mock_usages.csv` should exist in `fixtures.csv`
- All `repo_id` references should exist in `repositories.csv`
- No duplicate (fixture_id, fixture_name) pairs

**Detection Reliability:**
- **All languages** (Python, Java, JavaScript, TypeScript): Syntax-based detection, high confidence (~95%+)

**Limitations:**
- Snapshot at one commit per repository (no time series)
- Mock detection uses pattern matching (may miss unusual patterns)
- Go repositories excluded by design (dataset uses 4 languages only; see [docs/12-limitations.md](12-limitations.md))

---

## Need Help?

- **Database access needed?** Use SQLite viewer or SQL commands (see [docs/09-usage.md](09-usage.md))
- **Want raw source code?** Available in SQLite database (`fixtures.raw_source`)
- **Specific research question?** See [docs/18-example-analyses.md](18-example-analyses.md) for 5 exemplar analyses
- **Schema details?** See [docs/03-database-schema.md](03-database-schema.md)

---

## Citation

If you use FixtureDB CSVs in your research, cite:

```bibtex
@data{fixturedb2026,
  title={FixtureDB: A Multi-Language Dataset of Test Fixture Definitions},
  author={Almeida, João and Hora, Andre},
  year={2026},
  publisher={Zenodo},
  doi={TODO}
}
```

