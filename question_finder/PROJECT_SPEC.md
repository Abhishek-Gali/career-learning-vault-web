# PROJECT_SPEC.md — Functional Requirements Specification

## FR-001: Source Discovery
- **Requirement**: The system must discover candidate web pages through configured query matrices, known source registries, XML sitemaps, RSS/Atom feeds, and optional SearXNG search providers.
- **Reason**: To systematically discover public CLF-C02 practice questions without relying on manually entered URLs or single static scraping scripts.
- **Acceptance Condition**: Running discovery outputs structured candidate records into the `search_candidates` table with query, provider, URL, timestamp, and status.

## FR-002: Dynamic Query Matrix Generation
- **Requirement**: Queries must be dynamically constructed from the cross-product of CLF-C02 domains, task statements, in-scope services, key concepts, and intent qualifiers (e.g., "practice question", "quiz", "sample question").
- **Reason**: To ensure balanced topic coverage across the entire 4-domain AWS exam syllabus.
- **Acceptance Condition**: Query generation produces over 150 targeted search queries, loaded from `config/queries.yaml` and formatted without manual code edits.

## FR-003: Access Policy & Safe Fetching
- **Requirement**: The system must inspect and respect `robots.txt`, obey per-domain rate limits, enforce HTTP timeouts (default 20s), restrict content size (<= 10MB), and validate URLs against SSRF/private networks.
- **Reason**: To operate ethically, protect network integrity, and prevent crawler blocking.
- **Acceptance Condition**: Requests to prohibited robots paths or private IP blocks are blocked with logged `RobotsDeniedError` or `SSRFError`.

## FR-004: Dynamic Date & Recency Verification
- **Requirement**: The research window must dynamically calculate the last 6 calendar months from runtime. The date analyzer must inspect a 10-level hierarchy (schema.org, JSON-LD, `<time>`, OpenGraph, article meta, visible text, sitemap).
- **Reason**: To distinguish between genuinely recent questions, recently updated pages, and old material.
- **Acceptance Condition**: The system correctly records `published_at`, `updated_at`, `date_confidence`, and assigns status `RECENT_PUBLISHED`, `RECENT_UPDATED`, or `OLD`.

## FR-005: Multi-Strategy Content & Question Extraction
- **Requirement**: Support HTML structured data, semantic lists, table layouts, accordion FAQs, regex patterns, and public PDFs (via PyMuPDF).
- **Reason**: Practice questions appear in diverse markup formats across educational websites.
- **Acceptance Condition**: Extract stem, options list, correct answer keys, explanation text, and source offsets into normalized Pydantic question models.

## FR-006: Structural Question Validation
- **Requirement**: Reject or quarantine questions that have empty stems, < 2 options, mismatched answer references, missing required answers, or non-CLF-C02 content.
- **Reason**: To keep the dataset high-quality, preventing malformed objects from polluting study pools.
- **Acceptance Condition**: Validation filters out invalid fixtures with explicit rejection records logged to `rejection_records`.

## FR-007: Multiple-Response & Question Type Support
- **Requirement**: Support `SINGLE_CHOICE`, `MULTIPLE_RESPONSE`, `TRUE_FALSE`, `MATCHING`, and `SCENARIO` types. Preserve full answer sets during option shuffling.
- **Reason**: CLF-C02 exams explicitly feature multi-select questions (e.g., "Select TWO").
- **Acceptance Condition**: Multi-select options maintain 100% correct answer verification mapping even after random UI option reordering.

## FR-008: CLF-C02 Curriculum Classification
- **Requirement**: Map every accepted question to Domain (1-4), Task Statement (e.g., "1.2", "2.3"), Service Name, and Topic using exact taxonomy rules and keyword scoring.
- **Reason**: To allow domain-weighted quizzes, weak-topic analytics, and curriculum coverage reports.
- **Acceptance Condition**: Question classification accuracy on benchmark fixtures exceeds 95% with confidence scores stored.

## FR-009: Authoritative Answer Verification
- **Requirement**: Verify extracted answers against the official AWS Exam Guide, AWS Service documentation, and Knowledge Center articles.
- **Reason**: Public practice questions often feature incorrect community-voted answers.
- **Acceptance Condition**: Output records with status `VERIFIED`, `PARTIALLY_VERIFIED`, `CONFLICTING`, or `UNVERIFIED` with AWS citation URL.

## FR-010: Multi-Level Deduplication & Clustering
- **Requirement**: Detect duplicate questions across 6 levels: Exact Hash, Stem Hash, Option Set Similarity, Answer Mapping, Fuzzy RapidFuzz (>=85%), and optional Semantic Similarity.
- **Reason**: The same question frequently appears across dozens of different websites with cosmetic formatting changes.
- **Acceptance Condition**: Duplicates are grouped into `duplicate_clusters`, selecting a single scored canonical question.

## FR-011: Data Provenance & Lineage Storage
- **Requirement**: Store full lineage for every source question: source domain, source URL, page ID, published date, updated date, retrieved timestamp, content hash, extraction method, and licensing status.
- **Reason**: To maintain 100% auditable research findings and respect copyright.
- **Acceptance Condition**: Every question in the database links to a valid `question_sources` entry.

## FR-012: Generated Practice Question Pipeline
- **Requirement**: Deterministically generate supplementary practice questions from verified AWS documentation facts and CLF-C02 objectives.
- **Reason**: To fill coverage gaps in under-represented syllabus areas.
- **Acceptance Condition**: Generated questions are tagged `is_generated=True`, `source_kind=GENERATED_PRACTICE`, and never counted as recent source questions.

## FR-013: Local Full-Text Search (SQLite FTS5)
- **Requirement**: Provide millisecond full-text search indexing stem, options, explanation, services, topics, and domains.
- **Reason**: To enable instant query filtering across thousands of questions in UI and CLI.
- **Acceptance Condition**: FTS5 search queries return matching questions accurately with rank scoring.

## FR-014: Interactive Study & Quiz Engine
- **Requirement**: Deliver 10 quiz modes (Random, Recent Only, Generated Only, Verified Only, Domain Practice, Task Practice, Service Practice, Weak Topics, Review Incorrect, Timed).
- **Reason**: To provide a rich, responsive learning interface.
- **Acceptance Condition**: Interactive sessions track user answers, compute domain-level accuracy, and preserve randomized question/option mappings.

## FR-015: User Analytics & Weak Topic Detection
- **Requirement**: Locally calculate user attempt statistics, time per question, domain mastery, and pinpoint topics with < 70% accuracy.
- **Reason**: To guide study efforts efficiently toward areas needing improvement.
- **Acceptance Condition**: Analytics dashboard renders domain accuracy breakdown and recommended study topics.

## FR-016: Multi-Format Dataset Export
- **Requirement**: Support exporting filtered or complete datasets to JSON, JSONL, CSV, Markdown, and HTML with full metadata preserved.
- **Reason**: To enable offline study, flashcard generation, and research auditing.
- **Acceptance Condition**: Exported JSON conforms to `schemas/question.schema.json`.

## FR-017: Comprehensive Automated Dataset Audit
- **Requirement**: Provide `clf audit` command to detect broken links, date anomalies, missing answers, C01 leaks, or cluster inconsistencies.
- **Reason**: To ensure dataset integrity before study or distribution.
- **Acceptance Condition**: The audit script runs a suite of integrity queries and outputs an actionable health report.
