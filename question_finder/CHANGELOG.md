# CHANGELOG

## [0.1.0] - 2026-09-29
### Added
- Initial project architecture and constitution (`AGENTS.md`, `DESIGN.md`, `PROJECT_SPEC.md`).
- Modular agent rules (`.agents/rules/`) and skill specifications (`.agents/skills/`).
- Self-contained project layout with all venv, cache, logs, and databases isolated to `E:\`.
- Curriculum parser and snapshot engine for official AWS CLF-C02 specifications.
- Multi-provider discovery layer (Direct Crawl, Sitemap, RSS, optional SearXNG).
- Async HTTP fetcher with robots.txt, domain rate limiter, SSRF protection, and content cache.
- Multi-strategy question extraction (HTML, DOM heuristics, structured quizzes, PDF).
- 10-level publication and update date extraction hierarchy.
- CLF-C02 domain/task classifier and suspicious content quarantine engine.
- Authoritative answer verification engine using AWS documentation citations.
- 6-level duplicate detection and canonical question clustering.
- Deterministic template-based generated question pipeline with strict labeling.
- SQLite + WAL database with FTS5 virtual table for full-text search.
- Interactive Web UI (FastAPI + Jinja2 + HTMX) with 10 study/quiz modes and dashboard.
- Full Click CLI with 15 commands.
- Multi-format exporters (JSON, JSONL, CSV, Markdown, HTML) and automated dataset audit tool.
- 17 test fixture types and full unit, integration, and E2E test suite.
