# Skill: Dataset Audit Workflow

## Purpose
Performs an automated integrity inspection across all stored questions, sources, dates, and clusters before reporting or exporting.

## Procedure
1. **Provenance Verification**: Confirm that 100% of non-generated questions link to valid `question_sources` with non-empty URLs.
2. **Structural Integrity Check**: Ensure all questions have non-empty stems, >= 2 options, and that every correct answer points to an existing option key.
3. **Date Consistency Audit**: Ensure publication/update dates are not set in the future and match assigned recency statuses.
4. **CLF-C01 Leak Detection**: Scan recent question pool for explicit "CLF-C01" references or retired service names. Flag any leaks.
5. **Cluster Integrity**: Verify that duplicate clusters contain valid canonical question pointers and that canonical questions are active (not quarantined/rejected).
6. **Generation Segregation**: Verify that no generated questions have `source_kind=PUBLIC_PRACTICE` and that generated counters remain strictly isolated.
7. **Audit Report Generation**: Print structured summary to console and log any anomalies.
