# CSV User Guide

**Quick reference for analyzing FixtureDB without SQL.** For full schema details, see [Database Schema](../architecture/database-schema.md). For code examples, see [Using the Dataset](../usage/usage.md).

---

## CSV Files

```
fixturedb_export/
├── fixtures.csv                    ← Main table: 1 row per fixture (40.7K)
├── fixtures_python.csv             ← Python only (4.9K)
├── fixtures_java.csv               ← Java only (11.2K)
├── fixtures_javascript.csv         ← JavaScript only (5.5K)
├── fixtures_typescript.csv         ← TypeScript only (19K)
├── mock_usages.csv                 ← 1 row per mock call (12.8K)
├── repositories.csv                ← Repository metadata (160)
├── test_files.csv                  ← Test file listing (228K)
└── README.txt
```

---

## Quick Import

| Tool | Command |
|------|---------|
| **Excel** | Open → fixtures.csv (auto-import) |
| **Python** | `pd.read_csv('fixtures.csv')` |
| **R** | `read.csv('fixtures.csv')` |
| **SQL (SQLite)** | See [usage.md](../usage/usage.md) |

---

## Fixtures Table (Main Analysis)

| Column | Type | Meaning |
|--------|------|---------|
| **IDs** | | |
| `id` | Integer | Fixture ID (primary key) |
| `repo_id` | Integer | Repository ID |
| `file_id` | Integer | Test file ID |
| **Description** | | |
| `name` | Text | Fixture function name |
| `language` | Text | `python`, `java`, `javascript`, `typescript` |
| `fixture_type` | Text | Detection pattern (e.g., `pytest_decorator`, `junit5_before_each`) |
| `scope` | Text | `per_test`, `per_class`, `per_module`, `global` |
| `framework` | Text | Testing framework (pytest, unittest, jest, etc.) |
| **Location** | | |
| `start_line`, `end_line` | Integer | Line numbers in source |
| `loc` | Integer | Lines of code |
| **Complexity** | | |
| `cyclomatic_complexity` | Integer | McCabe complexity (1 = simple, 10+ = very complex) |
| `cognitive_complexity` | Integer | SonarQube-standard cognitive complexity (nesting-weighted) |
| `max_nesting_depth` | Integer | Maximum nested block depth |
| **Design** | | |
| `num_parameters` | Integer | Function parameters |
| `num_objects_instantiated` | Integer | Object creations (heuristic) |
| `num_external_calls` | Integer | I/O and external API calls (heuristic) |
| `reuse_count` | Integer | Number of tests using this fixture |
| `has_teardown_pair` | Boolean | Has cleanup logic |

---

## Mock Usages Table

| Column | Meaning |
|--------|---------|
| `id` | Mock usage ID |
| `fixture_id` | Fixture this mock is in (join key) |
| `repo_id` | Repository ID |
| `framework` | Mock framework (`unittest_mock`, `mockito`, `jest`, `sinon`, etc.) |
| `target_identifier` | What's being mocked (e.g., `"mymodule.HttpClient"`) |
| `num_interactions_configured` | Behavior configurations found (return_value, side_effect, etc.) |

**Usage:** Join to `fixtures.csv` on `fixture_id` to analyze mock patterns by fixture characteristics.

---

## Repositories Table

| Column | Meaning |
|--------|---------|
| `full_name` | GitHub slug (e.g., `"pytest-dev/pytest"`) |
| `language` | `python`, `java`, `javascript`, `typescript` |
| `stars` | Star count at collection time |
| `domain` | Category: `web`, `data`, `cli`, `infra`, `library`, `other` |
| `pinned_commit` | Git SHA analyzed (for reproducibility) |
| `num_fixtures` | Fixtures in repository |
| `num_mock_usages` | Mock calls in repository |

---

## Test Files Table

| Column | Meaning |
|--------|---------|
| `relative_path` | Path within repository (e.g., `tests/test_app.py`) |
| `file_loc` | Total lines of code |
| `num_fixtures` | Fixtures defined in file |
| `language` | Programming language |

---

## Common Analysis Patterns

**Distribution of complexity by language:**
```sql
SELECT language, 
       ROUND(AVG(cyclomatic_complexity), 1) as avg_cc,
       COUNT(*) as fixture_count
FROM fixtures
GROUP BY language;
```

**Fixtures with high reuse:**
```sql
SELECT name, fixture_type, reuse_count, cyclomatic_complexity
FROM fixtures
WHERE reuse_count > 10
ORDER BY reuse_count DESC;
```

**Mock frameworks by language:**
```sql
SELECT f.language, m.framework, COUNT(*) as count
FROM mock_usages m
JOIN fixtures f ON m.fixture_id = f.id
GROUP BY f.language, m.framework
ORDER BY f.language, count DESC;
```

---

## Data Notes

- **Complexity NULL:** Error during calculation (< 0.1%); safe to exclude
- **Count = 0:** Legitimate (no objects/calls in that fixture)
- **Scope options:** `per_test` (most common) → `per_class` → `per_module` → `global` (rare)
- **Pinned commits:** Use `repositories.pinned_commit` to check out exact code versions analyzed

See [Limitations](../reference/limitations.md) for known constraints and validation status.

