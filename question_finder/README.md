# CLF-C02 Recent Practice Question Researcher

> A serious, local-first research, study, and verification system for AWS Certified Cloud Practitioner (CLF-C02) public practice material.

---

## Key Capabilities
- **Dynamic 6-Month Recency Window**: Dynamically computes publication and update dates from current runtime.
- **Strict Content Categorization**: Transparently separates **Recent Public Source Questions**, **Generated Practice Questions**, **Older Questions**, **Legacy CLF-C01**, and **Quarantined** items.
- **Curriculum Mapping**: Automatically maps questions across the official 4 CLF-C02 Domains and Task Statements.
- **Authoritative Answer Verification**: Verifies question answers against AWS official documentation, whitepapers, and guides.
- **Multi-Level Deduplication**: 6-level dedup engine (Exact Hash, Stem Hash, Option Sets, Answer Mappings, RapidFuzz, Semantic).
- **10 Interactive Quiz Modes**: Random, Recent Only, Generated Only, Verified Only, Domain Practice, Weak Topics, Timed, etc.
- **Local Full-Text Search (SQLite FTS5)**: Fast keyword and service search across thousands of questions.
- **Self-Contained & Free**: 100% free, zero paid APIs, zero cloud subscriptions. All venv, pip cache, and data files reside in this project folder (`E:\`).

---

## Quick Start (Windows)

```powershell
# 1. Run the self-contained setup script (configures .venv and .pip-cache locally)
.\scripts\setup.ps1

# 2. Activate virtual environment
.venv\Scripts\Activate.ps1

# 3. Verify health & environment
clf doctor

# 4. Initialize database and schemas
clf init

# 5. Refresh AWS CLF-C02 Curriculum
clf curriculum refresh

# 6. Run research pipeline (default 6 months, target 1000 questions)
clf research --months 6 --recent-source-target 1000

# 7. Start interactive web interface
clf serve
```
Open your browser at `http://127.0.0.1:8000`.

---

## Quick Start (Linux / macOS)

```bash
# 1. Run setup script
chmod +x scripts/setup.sh
./scripts/setup.sh

# 2. Activate virtual environment
source .venv/bin/activate

# 3. Verify health
clf doctor

# 4. Initialize & Refresh Curriculum
clf init
clf curriculum refresh

# 5. Run research pipeline
clf research --months 6 --recent-source-target 1000

# 6. Start Web UI
clf serve
```

---

## CLI Command Reference

| Command | Description |
|---|---|
| `clf doctor` | Runs comprehensive health checks on Python, SQLite, FTS5, and local dirs |
| `clf init` | Creates database tables, triggers, and FTS5 virtual tables |
| `clf curriculum refresh` | Downloads and parses official AWS CLF-C02 exam guide |
| `clf research` | Executes full research pipeline (discover, fetch, extract, verify, dedupe) |
| `clf discover` | Discovers candidate URLs from query matrix and registered sources |
| `clf crawl` | Fetches and caches queued candidate web pages |
| `clf extract` | Extracts structured questions and dates from cached pages |
| `clf classify` | Maps extracted questions to CLF-C02 domains and task statements |
| `clf verify` | Verifies question answers against authoritative AWS documentation |
| `clf dedupe` | Runs 6-level duplicate detection and clusters matching questions |
| `clf audit` | Audits dataset integrity, provenance, dates, and C01 leaks |
| `clf stats` | Prints rich summary statistics of all dataset categories |
| `clf export` | Exports questions to JSON, JSONL, CSV, Markdown, or HTML |
| `clf quiz` | Starts a terminal-based interactive quiz session |
| `clf refresh` | Re-checks date windows, revisits sources, and updates recency |
| `clf serve` | Launches the FastAPI + HTMX Web UI on `http://127.0.0.1:8000` |

---

## Project Structure

```text
├── AGENTS.md               # Project constitution & engineering invariants
├── DESIGN.md               # Full architecture & 7 Mermaid sequence diagrams
├── PROJECT_SPEC.md         # Requirements FR-001 through FR-017
├── DATA_POLICY.md          # Provenance & content licensing policies
├── SECURITY.md             # SSRF protections & resource limits
│
├── .agents/                # Modular rules and procedural skills
│   ├── rules/              # Architecture, Python, Database, Provenance, Security...
│   └── skills/             # Research pipeline, Extraction, Verification, Dedup, Audit
│
├── config/                 # YAML settings, sources, query templates, taxonomy
├── schemas/                # JSON Schema for exports
├── scripts/                # Self-contained setup scripts (Windows & Linux)
│
├── data/                   # ALL runtime storage (gitignored, stays on E:\)
│   ├── db/                 # SQLite database (clf_c02.db)
│   ├── cache/              # Content-addressed page cache & curriculum cache
│   ├── exports/            # JSON, CSV, HTML research reports
│   └── logs/               # Structured application logs
│
├── app/                    # Core Python application
│   ├── core/               # Path resolver, exceptions, date window, enums
│   ├── db/                 # SQLAlchemy models, repositories, FTS5 setup
│   ├── curriculum/         # AWS guide fetcher, parser, taxonomy
│   ├── discovery/          # Query builder, candidate pipeline, search providers
│   ├── fetching/           # Async HTTPX fetcher, robots parser, rate limiter
│   ├── extraction/         # Metadata, dates, HTML, PDF, quiz parsers
│   ├── questions/          # Normalizer, validator, curriculum classifier
│   ├── verification/       # AWS answer verifier, evidence engine, C01 detector
│   ├── deduplication/      # Exact, stem, option, fuzzy RapidFuzz deduplication
│   ├── generation/         # Deterministic template question generator
│   ├── pipeline/           # Checkpointed orchestrator & scheduler
│   ├── analytics/          # Stats, domain coverage, user performance
│   ├── export/             # Multi-format export engine
│   ├── content_safety/     # Suspicious content classifier
│   ├── web/                # FastAPI routes, Jinja2 templates, static assets
│   └── cli/                # Click CLI interface
│
└── tests/                  # 17 fixture types, unit, integration & E2E tests
```

---

## Docker Support (Optional)

```bash
# Run local web application in Docker (bind-mounted to ./data and ./config)
docker compose up

# Run with optional SearXNG container
docker compose --profile search up
```

---

## License & Attribution
Operates as a local personal study and research application. All third-party material retains original copyright and attribution.
