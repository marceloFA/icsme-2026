# Configuration Reference

All collection parameters live in `collection/config.py`.

## Per-language targets

| Language       | `min_stars` | `target_repos` | Rationale |
|----------------|-------------|----------------|----------|
| Python         | 100         | 1,000          | Large ecosystem, high test culture |
| Java           | 100         | 1,000          | Direct comparability with Hamster |
| JavaScript     | 100         | 800            | Frontend repos often yield few fixtures |
| TypeScript     | 100         | 600            | Younger ecosystem |

## Star tiers

| Tier       | `stars` range | Rationale |
|------------|---------------|----------|
| `core`     | ≥ 500         | Threshold used in Hamster study (Pan et al., 2025). High-quality, mature projects with established testing practices. |
| `extended` | 100–499       | Adds diversity and smaller/emerging projects. 100-star floor aligns with MSR empirical study conventions and balances between popularity and novelty. |

## Language Survival Rates

**Survival rate** = (discovered repos with ≥1 analyzed fixture) / (repos fetched from GitHub API)

Used for discovery forecasting during collection runs. Empirical rates will be populated as each language collection completes.

| Language       | Survival Rate | Status |
|----------------|---------------|--------|
| Python         | *Pending* | Collection in progress |
| Java           | *Pending* | Collection in progress |
| JavaScript     | *Pending* | Collection in progress |
| TypeScript     | *Pending* | Collection in progress |
| **Default**    | 0.09 (9%)    | Fallback estimate used during collection planning |

Survival rates are empirically determined as collection completes for each language.
Lower rates = harder to find qualifying repos; higher rates = abundant fixture usage.

## Quality filters (post-clone)

| Parameter             | Default | Rationale |
|-----------------------|---------|----------|
| `MIN_TEST_FILES`      | 5       | Empirical threshold; repos with fewer test files likely lack testing culture. Aligned with Ahmed et al. (2025) observations on test project characteristics. |
| `MIN_COMMITS`         | 50      | Ensures repositories have sufficient history and are non-trivial projects. Avoids prototype/example repos. |
| `MIN_FIXTURES_FOUND`  | 1       | Only repositories with at least one fixture definition are included in the final dataset (post-extraction filter). Avoids cluttering with test-only but fixture-less repos. |

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
