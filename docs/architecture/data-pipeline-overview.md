# Data Pipeline: Collection → Counting → Export

## Overview Diagram

```
GitHub Repositories
        ↓
    Search & Clone
        ↓
    Extract Fixtures
        ↓
  Calculate Counts  ← NEW: num_test_files, num_fixtures, num_mock_usages
        ↓
  Store in Database
    (SQLite)
        ↓
    Export Dataset
        ├── fixtures.db (full database)
        ├── repositories.csv
        ├── test_files.csv
        ├── fixtures.csv
        ├── mock_usages.csv
        └── fixtures_{language}.csv  ← NEW: language-specific, reader-friendly
                ↓
           Zenodo Archive
```

## 1. Database Schema

The `repositories` table includes three count fields populated during extraction:

```sql
CREATE TABLE repositories (
    id              INTEGER PRIMARY KEY,
    github_id       INTEGER UNIQUE,
    full_name       TEXT,
    language        TEXT,
    stars           INTEGER,
    status          TEXT,  -- discovered|cloned|analysed|skipped|error
    num_test_files  INTEGER DEFAULT 0,
    num_fixtures    INTEGER DEFAULT 0,
    num_mock_usages INTEGER DEFAULT 0,
    collected_at    TEXT
);
```

## 2. Extraction Process

Extraction counts test files and fixtures per repository, stores in `repositories` table. See [collection/extractor.py](../../collection/detector.py) for implementation.

**Key counts set during extraction:**
- `num_test_files` — total test files found
- `num_fixtures` — aggregated fixture count across all test files  
- `num_mock_usages` — aggregated mock usage count

## 3. Querying the Data

**Example: Per-language statistics**

```sql
SELECT 
    language,
    COUNT(*) as num_repos,
    SUM(num_fixtures) as total_fixtures,
    AVG(num_fixtures) as avg_per_repo
FROM repositories
WHERE status = 'analysed'
GROUP BY language
ORDER BY total_fixtures DESC;
```

## 4. CSV Export

Export phase generates queryable database (`fixtures.db`) and user-friendly CSVs. See [collection/exporter.py](../../collection/exporter.py) for implementation.

**Generated files:**
- `fixtures.db` — Full SQLite database
- `repositories.csv`, `test_files.csv`, `fixtures.csv`, `mock_usages.csv` — Main tables
- `fixtures_{language}.csv` — Language-specific fixture views (python, java, javascript, typescript)

## 5. Data Flow

```
_find_test_files(repo) → num_test_files
    ↓
extract_fixtures() per file → aggregate to num_fixtures
    ↓
extract_mocks() per fixture → aggregate to num_mock_usages
    ↓
set_repo_analysed() → UPDATE repositories table
    ↓
During export: Query database → CSV language-specific views
```

Counts are computed once at extraction time and stored atomically. CSV exports are derived views with pre-aggregated mock counts.

## 6. Why This Design?

**Counts in Database** — Computed once at extraction, stored atomically. Fast queries, no repeated aggregation.

**Language-Specific CSVs** — Pre-aggregated views; accessible without database software.

**Both Database + CSVs** — Database is authoritative source; CSVs are published views. Enables both reproducibility (SQL) and accessibility (CSV).

## 7. See Also

- [language-specific-csv-export.md](../data/language-specific-csv-export.md) — CSV format and example analysis
