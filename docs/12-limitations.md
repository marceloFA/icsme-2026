# Limitations and Threats to Validity

## Sampling bias

The corpus is drawn from repositories with ≥ 100 GitHub stars. Popular,
actively maintained projects may exhibit higher test discipline than typical
open-source software. A prior study from our institution (Coelho et al.,
MSR 2020) shows that star-based sampling over-represents JavaScript projects
and web frameworks; this is why `star_tier` is recorded and why we recommend
stratifying analyses by tier.

## Go language exclusion

Go repositories are excluded from the FixtureDB dataset due to unvalidated heuristic-based detection. The Go helper detector relies on pattern matching (non-test functions called from ≥2 test functions) without formal validation. Rather than publish unvalidated data, Go is not included (this exclusion avoids ~2.5% of data). All included languages (Python, Java, JavaScript, TypeScript) use syntax-based detection with high confidence (~95%+).

## Snapshot corpus

Each repository is captured at a single commit. The dataset does not support
longitudinal analyses of fixture evolution.

## Language coverage

This dataset covers four languages (Python, Java, JavaScript, TypeScript) with syntax-based detection across all. Ruby (RSpec), Kotlin, Scala, Rust, and Go are not included.

## Mock detection completeness

Mock detection uses regular expressions over source text. Framework versions
or unusual coding styles may produce false negatives. The `raw_source`
column is included in the SQLite file specifically so that researchers can
re-run or improve detection against the original fixture text.
