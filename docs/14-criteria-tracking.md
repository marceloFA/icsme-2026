# Repository Criteria Tracking

## Overview

The `repositories` table now tracks three count fields to enable post-analysis queries about which repositories met specific collection criteria:

- `num_test_files` - Count of test files discovered in the repository
- `num_fixtures` - Count of fixture definitions detected in test files
- `num_mock_usages` - Count of mock framework usages detected in fixtures

These counts are populated during the extraction phase when a repository is marked as `analysed` or `skipped`.

## Schema

```sql
ALTER TABLE repositories ADD COLUMN num_test_files INTEGER DEFAULT 0;
ALTER TABLE repositories ADD COLUMN num_fixtures INTEGER DEFAULT 0;
ALTER TABLE repositories ADD COLUMN num_mock_usages INTEGER DEFAULT 0;
```

## Usage Examples

### Percentage of explored repos without test files

```sql
SELECT 
  COUNT(*) as repos_without_tests,
  COUNT(*) * 100.0 / (SELECT COUNT(*) FROM repositories WHERE status = 'analysed') as percentage
FROM repositories 
WHERE status = 'analysed' AND num_test_files = 0;
```

### Percentage of explored repos without fixtures (conditional on having tests)

```sql
SELECT 
  COUNT(*) as repos_without_fixtures,
  COUNT(*) * 100.0 / (SELECT COUNT(*) FROM repositories WHERE status = 'analysed' AND num_test_files > 0) as percentage
FROM repositories 
WHERE status = 'analysed' AND num_test_files > 0 AND num_fixtures = 0;
```

### Breakdown by language

```sql
SELECT 
  language,
  COUNT(*) as total_repos,
  SUM(CASE WHEN num_test_files = 0 THEN 1 ELSE 0 END) as repos_without_tests,
  SUM(CASE WHEN num_fixtures = 0 THEN 1 ELSE 0 END) as repos_without_fixtures,
  SUM(CASE WHEN num_mock_usages = 0 THEN 1 ELSE 0 END) as repos_without_mocks
FROM repositories 
WHERE status = 'analysed'
GROUP BY language
ORDER BY total_repos DESC;
```

### Repos that made it to analysis but failed the fixture threshold

```sql
SELECT 
  full_name,
  num_test_files,
  num_fixtures,
  num_mock_usages,
  error_message
FROM repositories 
WHERE status = 'skipped' 
  AND error_message LIKE '%fixtures found%'
ORDER BY num_fixtures DESC;
```

### Distribution of fixture counts

```sql
SELECT 
  CASE 
    WHEN num_fixtures = 0 THEN '0'
    WHEN num_fixtures BETWEEN 1 AND 5 THEN '1-5'
    WHEN num_fixtures BETWEEN 6 AND 20 THEN '6-20'
    WHEN num_fixtures BETWEEN 21 AND 50 THEN '21-50'
    ELSE '50+'
  END as fixture_range,
  COUNT(*) as count,
  COUNT(*) * 100.0 / (SELECT COUNT(*) FROM repositories WHERE status = 'analysed') as percentage
FROM repositories
WHERE status = 'analysed'
GROUP BY fixture_range
ORDER BY 
  CAST(SUBSTR(fixture_range, 1, INSTR(fixture_range, '-') - 1) as INTEGER);
```

## Implementation Details

### Extraction Phase

During the extraction phase in `collection/extractor.py`, when a repository is processed:

1. Test files are discovered using language-specific patterns
2. Fixtures are extracted from each test file
3. Mock usages are detected within each fixture
4. When the repo is marked as `analysed` or `skipped`, the counts are recorded

The counts are populated using the `set_repo_analysed()` function:

```python
def set_repo_analysed(
    conn: sqlite3.Connection,
    repo_id: int,
    num_test_files: int,
    num_fixtures: int,
    num_mock_usages: int,
) -> None:
    """Mark a repo as analysed and store the extraction counts."""
```

### Merits of Count-Based Tracking

Using counts instead of boolean flags provides:

- **Flexibility**: Can filter on any threshold (e.g., repos with >10 fixtures)
- **Granularity**: Can distinguish between "0 fixtures" and "has fixtures"
- **Analysis**: Can create detailed distributions and percentile analyses
- **Future-proofing**: Can be aggregated, averaged, or used in statistical tests

## Notes

- Counts are cumulative across all test files in a repository
- Repos marked as `error` or `discovered` status will have 0 counts
- Only repos that reach `analysed` or `skipped` status have populated counts
- The `MIN_FIXTURES_FOUND` threshold (configurable) determines which repos are skipped due to insufficient fixtures
