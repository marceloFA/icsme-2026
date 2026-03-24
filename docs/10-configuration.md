# Configuration Reference

All collection parameters live in `corpus/config.py`.

## Per-language targets

| Language       | `min_stars` | `target_repos` | Rationale |
|----------------|-------------|----------------|----------|
| Python         | 100         | 1,000          | Large ecosystem, high test culture |
| Java           | 100         | 1,000          | Direct comparability with Hamster |
| JavaScript     | 100         | 800            | Frontend repos often yield few fixtures |
| TypeScript     | 100         | 600            | Younger ecosystem |
| Go             | 100         | 600            | Smaller ecosystem |
| C#             | 100         | 800            | .NET ecosystem with diverse test frameworks |

## Star tiers

| Tier       | `stars` range | Comparable to |
|------------|---------------|---------------|
| `core`     | ≥ 500         | Hamster (arXiv:2509.26204) selection criterion |
| `extended` | 100–499       | Common MSR floor; adds diversity |

## Quality filters (post-clone)

| Parameter             | Default | Effect |
|-----------------------|---------|--------|
| `MIN_TEST_FILES`      | 5       | Repos with fewer test files are marked `skipped` |
| `MIN_COMMITS`         | 50      | Repos with fewer commits are marked `skipped` |
| `MIN_FIXTURES_FOUND`  | 1       | Repos where extraction finds zero fixtures are marked `skipped` |

## Pipeline tuning

| Parameter                          | Default | Notes |
|------------------------------------|---------|-------|
| `CLONE_WORKERS`                    | 12      | Parallel clone threads |
| `CLONE_BATCH_SIZE`                 | 50      | Repos per `clone` invocation (incremental mode) |
| `EXTRACT_WORKERS`                  | 3       | Parallel extraction workers (respects SQLite single-writer limit) |
| `MAX_REPOS_PER_ITERATION`          | 500     | Cap on repos processed per collection iteration (all languages) |
| `MAX_DISCOVERIES_PER_ITERATION`    | 3,000   | Max repos discovered per iteration (disk space management) |
| `DISCOVERY_SURVIVAL_RATE`          | 0.09    | Fallback discovery→analyzed conversion rate |
| `DISCOVERY_SAFETY_BUFFER`          | 1.25    | 25% safety buffer on discovery estimates |
| `REQUEST_DELAY`                    | 2.0 s   | Pause between GitHub Search API pages |
