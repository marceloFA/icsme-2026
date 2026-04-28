# Using the Dataset for Research

FixtureDB offers two complementary analysis pathways, suited to different research needs and tool preferences:

## Two Main Use Cases

### **Use Case 1: SQLite Database** (`fixtures.db`)
**Best for:** Complex queries, joins across tables, reproducibility verification, custom analysis  
**Access methods:** `sqlite3` CLI, Python (`sqlite3` module), R (`RSQLite` package), SQL IDE (DBeaver, SQLiteStudio)  
**Data scope:** Full database with all fields, internal infrastructure, complete extraction history  
**Advantages:**
- Powerful joins across repositories, test files, fixtures, and mock usages
- Filter by multiple criteria simultaneously (language, star tier, complexity, domain)
- Verify extraction decisions and explore raw source code
- No data loss—nothing is filtered out

### **Use Case 2: CSV Exports** (`fixtures.csv`, `mock_usages.csv`, language-specific CSVs)
**Best for:** Quick analysis, non-SQL users, Excel/Python/R workflows, reproducible papers  
**Access methods:** Excel, Google Sheets, Python (pandas, polars), R (readr, data.table), SQL imports  
**Data scope:** Curated quantitative metrics only (no raw source code)  
**Advantages:**
- No database knowledge required
- Works in any spreadsheet application
- Language-specific exports pre-filtered for convenience
- Column documentation in [docs/csv-export-guide.md](../data/csv-export-guide.md)

---

## Use Case 1: Querying the SQLite Database

Query directly with `sqlite3` CLI, Python, R, or SQL IDE (DBeaver, SQLiteStudio).

**Example: Python + Pandas**

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect("fixtures.db")

# All Python fixtures with complexity metrics
df = pd.read_sql("""
    SELECT f.name, f.fixture_type, f.scope, f.loc,
           f.cyclomatic_complexity, f.num_external_calls,
           r.full_name, r.domain, r.stars
    FROM fixtures f
    JOIN repositories r ON f.repo_id = r.id
    WHERE r.language = 'python' AND r.status = 'analysed'
""", conn)

# Mock adoption rate
pd.read_sql("""
    SELECT r.language,
           COUNT(DISTINCT f.id) AS total_fixtures,
           ROUND(COUNT(DISTINCT m.fixture_id) * 100.0
                 / COUNT(DISTINCT f.id), 1) AS pct_with_mocks
    FROM fixtures f
    JOIN repositories r ON f.repo_id = r.id
    LEFT JOIN mock_usages m ON m.fixture_id = f.id
    WHERE r.status = 'analysed'
    GROUP BY r.language
""", conn)
```

**Raw source inspection:**

```python
# Retrieve full source code for a specific fixture
df = pd.read_sql("""
    SELECT f.name, f.fixture_type, f.raw_source, r.full_name
    FROM fixtures f
    JOIN repositories r ON f.repo_id = r.id
    WHERE f.name = 'setup_database' AND r.language = 'python'
""", conn)
print(df['raw_source'].iloc[0])

---

## Use Case 2: Analyzing CSV Exports

Pre-filtered, denormalized CSVs for spreadsheet and statistical software. Quantitative metrics only; raw source available in SQLite database.

**Available files:**
- `fixtures.csv` — All fixtures across all languages
- `fixtures_python.csv`, `fixtures_java.csv`, `fixtures_javascript.csv`, `fixtures_typescript.csv` — Language-specific pre-filtered exports
- `mock_usages.csv`, `repositories.csv`, `test_files.csv` — Related metadata

See [csv-export-guide.md](../data/csv-export-guide.md) for full column documentation.

**Example: Python + Pandas**

```python
import pandas as pd

# Load full fixtures dataset
fixtures = pd.read_csv("fixtures.csv")
repos = pd.read_csv("repositories.csv")

# Join with repository metadata
fixtures_with_repo = fixtures.merge(repos, left_on='repo_id', right_on='id', suffixes=('_fixture', '_repo'))

# Complex fixtures (cyclomatic complexity > 5)
complex_fixtures = fixtures[fixtures['cyclomatic_complexity'] > 5]

# Mock adoption rate per language
mocks = pd.read_csv("mock_usages.csv")
mock_stats = fixtures.merge(mocks[['fixture_id']].drop_duplicates(), 
                            left_on='id', right_on='fixture_id', how='left')
print(mock_stats.groupby(fixtures['language']).apply(
    lambda g: (g['fixture_id'].notna().sum() / len(g) * 100)))
```

**Excel / Spreadsheet:**
- Open `fixtures.csv` directly
- Use Pivot Tables to summarize by language, fixture_type, scope
- Use VLOOKUP to join with `repositories.csv` for star counts and domains

---

## Key Differences: SQLite vs. CSV

| Aspect | SQLite | CSV |
|--------|--------|-----|
| **Setup** | None; just open the `.db` file | None; just open `.csv` file |
| **Querying** | SQL joins across 4 tables | Spreadsheet operations or pandas/R imports |
| **Data completeness** | Full: all fields, raw source code, extraction metadata | Curated: quantitative metrics only |
| **Filtering complexity** | Easy: complex WHERE clauses and aggregations | Moderate: requires spreadsheet functions or code |
| **Performance** | Fast even for large queries | Good for files <100k rows; slower for full dataset |
| **Best for** | Verification, custom analysis, reproducibility | Quick summaries, Excel workflows, sharing with colleagues |

---

## Common Analyses

### "What percentage of Python fixtures use mocks?"

**SQLite:**
```sql
SELECT 
    COUNT(DISTINCT f.id) as total,
    COUNT(DISTINCT m.fixture_id) as with_mocks,
    ROUND(100.0 * COUNT(DISTINCT m.fixture_id) / COUNT(DISTINCT f.id), 1) as pct
FROM fixtures f
JOIN repositories r ON f.repo_id = r.id
LEFT JOIN mock_usages m ON f.id = m.fixture_id
WHERE r.language = 'python' AND r.status = 'analysed';
```

**CSV (Python):**
```python
fixtures = pd.read_csv("fixtures_python.csv")
mocks = pd.read_csv("mock_usages.csv")
with_mocks = fixtures.merge(mocks, left_on='id', right_on='fixture_id', how='inner')['id'].nunique()
pct = (with_mocks / len(fixtures)) * 100
print(f"{pct:.1f}%")
```

---

## Need help?

- **CSV column meanings:** See [docs/csv-export-guide.md](../data/csv-export-guide.md)
- **Full CSV guide with tool-specific walkthrough:** See [docs/csv-user-guide.md](../data/csv-user-guide.md)
- **Schema details:** See [docs/database-schema.md](../architecture/database-schema.md)
