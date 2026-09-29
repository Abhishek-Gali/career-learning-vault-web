# Skill: Research Pipeline Workflow

## Purpose
Executes the end-to-end multi-stage research cycle to discover, fetch, extract, verify, deduplicate, and persist CLF-C02 practice questions.

## Procedure
1. **Initialize & Checkpoint**: Load active configuration, resolve dynamic 6-month date window, and create or resume `research_runs` record.
2. **Curriculum Synchronization**: Fetch and parse the latest AWS CLF-C02 exam guide; generate domain and service taxonomy.
3. **Query Matrix Construction**: Combine curriculum topics with practice question intent patterns to build query matrix.
4. **Discovery & Candidate Queuing**: Query configured search providers and source registries; populate `search_candidates`.
5. **Safe Batch Fetching**: Check `robots.txt`, acquire rate-limiter slots, check content cache, and execute async HTTP requests.
6. **Metadata & Date Resolution**: Extract structured headers, schema.org JSON-LD, OpenGraph tags, and determine publication/update dates.
7. **Question Extraction & Normalization**: Parse questions using multi-strategy parsers; clean text and compute hashes.
8. **Classification & Safety Review**: Map questions to CLF-C02 domains/tasks; screen for suspicious disclosure content.
9. **Authoritative Answer Verification**: Compare extracted answers with official AWS documentation; record citations.
10. **Multi-Level Deduplication**: Check exact, stem, option, and fuzzy similarity; assign to duplicate clusters and select canonical representations.
11. **Quality Scoring & Persistence**: Compute quality score, persist to SQLite, and update FTS5 virtual table.
12. **Audit & Reporting**: Execute dataset audit and write `research_report.json` and `research_report.html` to `data/exports/`.
