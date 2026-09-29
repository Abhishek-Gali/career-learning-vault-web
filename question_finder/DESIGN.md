# DESIGN.md — Architecture & Technical Specifications

## 1. System Goals & Non-Goals

### Goals
- Discover publicly accessible AWS CLF-C02 practice and study material on the public internet.
- Dynamically determine recentness (default: last 6 calendar months from runtime).
- Extract structured single-choice, multiple-response, true/false, matching, and scenario questions.
- Maintain a strict distinction between **Recent Source Questions**, **Generated Practice Questions**, **Older Questions**, **Legacy CLF-C01**, and **Quarantined** items.
- Map questions to the official AWS CLF-C02 curriculum domains (1 through 4) and task statements.
- Verify extracted answers against official AWS documentation, whitepapers, and guides.
- Implement robust multi-level duplicate detection and clustering.
- Provide a responsive local Web UI (FastAPI + HTMX) and rich CLI (Click).
- Support offline study, quiz modes, weak-topic analytics, and multiple export formats (JSON, JSONL, CSV, MD, HTML).
- Ensure 100% free operation with zero mandatory paid services, APIs, or cloud infrastructure.
- Maintain total filesystem self-containment inside the project directory (`E:\`).

### Non-Goals
- Bypassing paywalls, login screens, or anti-bot protections.
- Downloading or storing confidential/leaked NDA-protected AWS exam dumps.
- Storing entire external websites or violating content licenses.
- Guaranteeing exam passing or predicting exact certification questions.
- Relying on external paid LLMs or paid search engines.

---

## 2. High-Level System Architecture

```mermaid
flowchart TD
    subgraph Discovery["Discovery Layer"]
        QM[Query Matrix Builder]
        SP[Search Providers]
        SR[Source Registry]
        SP --> |SearXNG (Optional)| SX[SearXNG Provider]
        SP --> |Direct Crawl| DS[Direct Source Provider]
        SP --> |RSS/Atom| RSS[RSS Provider]
        SP --> |XML Sitemap| SM[Sitemap Provider]
    end

    subgraph Fetching["Fetching & Caching Layer"]
        CM[Candidate Manager]
        HF[HTTP Fetcher (HTTPX)]
        BF[Browser Fetcher (Playwright - Opt)]
        RB[Robots & Policy Checker]
        RL[Per-Domain Rate Limiter]
        CA[Content-Addressed Cache]
    end

    subgraph Extraction["Extraction & Normalization Layer"]
        ME[Metadata Extractor]
        DE[Date Hierarchy Analyzer]
        QE[Question Extractor Engine]
        HE[HTML/DOM Parser]
        PE[PDF Parser (PyMuPDF)]
        QZ[Structured Quiz Parser]
    end

    subgraph Processing["Classification, Verification & Dedup"]
        NM[Text Normalizer]
        CS[Content Safety & Quarantine]
        CL[Curriculum Classifier]
        VR[Authoritative Answer Verifier]
        DD[Multi-Level Dedup Engine]
        QV[Data Quality Scorer]
    end

    subgraph Generation["Generated Practice Layer"]
        TG[Deterministic Template Generator]
        LG[Optional Local Reasoning Provider]
        GV[Fact & Distractor Validator]
    end

    subgraph Storage["Storage Layer"]
        DB[(SQLite 3 + WAL Mode)]
        FTS[FTS5 Full-Text Index]
        FS[Disk Snapshot Cache]
    end

    subgraph Interface["Interface & Delivery Layer"]
        WEB[Web UI (FastAPI + Jinja2 + HTMX)]
        CLI[Command Line Interface (Click)]
        EXP[Export Engine (JSON/CSV/MD/HTML)]
        SCH[Background Scheduler (APScheduler)]
    end

    QM --> SP
    SR --> SP
    SP --> CM
    CM --> RB --> RL --> HF
    HF --> CA
    CA --> ME --> DE
    CA --> HE --> QE
    CA --> PE --> QE
    CA --> QZ --> QE
    QE --> NM --> CS
    CS --> CL --> VR --> DD --> QV --> DB
    QV --> FTS
    TG --> GV --> DB
    DB --> WEB
    DB --> CLI
    DB --> EXP
    SCH --> QM
```

---

## 3. Ingestion Sequence Flow

```mermaid
sequenceDiagram
    participant P as Pipeline Orchestrator
    participant Q as Query Builder
    participant S as Search Provider
    participant C as Candidate Manager
    participant R as Robots & RateLimiter
    participant F as HTTP Fetcher
    participant CA as Cache
    participant M as Metadata & Date Extractor
    participant E as Question Extractor
    participant CL as Classifier & Safety
    participant V as Answer Verifier
    participant DD as Dedup Engine
    participant DB as SQLite DB

    P->>Q: Build Query Matrix (Domains x Services x Types)
    Q-->>P: Queries[]
    loop For each Query Batch
        P->>S: search(query, limit)
        S-->>P: SearchResult[]
        P->>C: register_candidates(results)
    end
    loop For each Queued Candidate
        P->>R: check_robots_and_rate_limit(url)
        R-->>P: Allowed (delay_ms)
        P->>CA: check_cache(url)
        alt Cache Miss or Stale
            P->>F: fetch_url(url, timeout, limits)
            F-->>P: FetchResult(html, headers, status)
            P->>CA: store_snapshot(url, content)
        else Cache Hit
            CA-->>P: CachedContent(html)
        end
        P->>M: extract_metadata_and_date(html)
        M-->>P: DateInfo(published_at, updated_at, confidence)
        P->>E: extract_questions(html)
        E-->>P: ExtractedQuestion[]
        loop For each Question
            P->>CL: inspect_safety_and_classify(question)
            CL-->>P: Classification(domain, task, status)
            P->>V: verify_answer(question)
            V-->>P: VerificationResult(status, evidence)
            P->>DD: check_duplicates(question)
            DD-->>P: DedupResult(is_dup, cluster_id, canonical)
            P->>DB: persist_question_and_provenance()
        end
    end
```

---

## 4. Question Lifecycle State Machine

```mermaid
stateDiagram-v2
    [*] --> DISCOVERED: URL found by Search/Crawl
    DISCOVERED --> QUEUED: Validated against scope & policy
    QUEUED --> FETCHED: HTTP/Browser download complete
    FETCHED --> EXTRACTED: Question stems & options parsed
    EXTRACTED --> REJECTED: Malformed/Empty/No options
    EXTRACTED --> NORMALIZED: Text cleaned & hashed

    NORMALIZED --> QUARANTINED: Suspicious exam disclosure text
    NORMALIZED --> CLASSIFIED: Mapped to CLF-C02 Domain/Task

    CLASSIFIED --> LEGACY_C01: Explicit CLF-C01 / Retired Services
    CLASSIFIED --> VERIFIED: Answer verified against AWS Docs
    CLASSIFIED --> CONFLICTING: Conflicting evidence found
    CLASSIFIED --> UNVERIFIED: No authoritative evidence found

    VERIFIED --> DEDUPLICATED: Clustered with exact/fuzzy matches
    CONFLICTING --> DEDUPLICATED
    UNVERIFIED --> DEDUPLICATED

    DEDUPLICATED --> ACCEPTED_RECENT: Recency policy met (<= 6 months)
    DEDUPLICATED --> ACCEPTED_OLDER: Valid C02 but > 6 months old

    ACCEPTED_RECENT --> [*]
    ACCEPTED_OLDER --> [*]
    LEGACY_C01 --> [*]
    QUARANTINED --> [*]
    REJECTED --> [*]
```

---

## 5. Answer Verification Flow

```mermaid
flowchart TD
    Q[Extracted Question Candidate] --> CHK_ANS{Has Extracted Answer?}
    CHK_ANS --> |No| UNV[Status: UNVERIFIED]
    CHK_ANS --> |Yes| EG[Check AWS Exam Guide Specifications]
    EG --> |Direct Concept Match| V1[Verify Domain Alignment]
    V1 --> SD[Query AWS Documentation & Knowledge Base]
    SD --> MTCH{Does AWS Doc Confirm Answer?}
    MTCH --> |Exact Match| VER[Status: VERIFIED<br>Confidence: HIGH]
    MTCH --> |Partial/Derived Match| PVER[Status: PARTIALLY_VERIFIED<br>Confidence: MEDIUM]
    MTCH --> |Contradicts Extracted Answer| CONF[Status: CONFLICTING<br>Flag for Review]
    MTCH --> |No Direct Doc Found| UNV2[Status: UNVERIFIED<br>Confidence: LOW]

    VER --> REC[Create Verification Record with AWS Citation]
    PVER --> REC
    CONF --> REC
    UNV --> REC
    UNV2 --> REC
```

---

## 6. Duplicate-Clustering Flow

```mermaid
flowchart TD
    Q[Normalized Question] --> L1{Level 1: Exact Hash Match?}
    L1 --> |Yes| C1[Assign to Cluster as Duplicate]
    L1 --> |No| L2{Level 2: Stem Hash / Exact Stem?}
    L2 --> |Yes| C2[Assign to Cluster]
    L2 --> |No| L3{Level 3: Option Set Similarity >= 90%?}
    L3 --> |Yes| C3[Assign to Cluster]
    L3 --> |No| L4{Level 4: RapidFuzz Stem Score >= 85%?}
    L4 --> |Yes| L4A{Answer Mappings Compatible?}
    L4A --> |Yes| C4[Assign to Cluster]
    L4A --> |No| NEW[Create New Question Record]
    L4 --> |No| NEW

    C1 --> CANON[Run Canonical Selection Algorithm]
    C2 --> CANON
    C3 --> CANON
    C4 --> CANON

    CANON --> |Scored Rank: Verification + Clarity + Provenance| BEST[Mark as Canonical Representation]
```

---

## 7. Dynamic Refresh Flow

```mermaid
flowchart TD
    TRIG[Refresh Triggered (CLI / Scheduled / Web)] --> WIN[Recompute 6-Month Date Window]
    WIN --> CUR[Check Official AWS Exam Guide for Updates]
    CUR --> ETAG{Curriculum Content Hash Changed?}
    ETAG --> |Yes| NCUR[Create New Curriculum Snapshot & Re-index Taxonomy]
    ETAG --> |No| DISCO[Run Incremental Source Discovery]
    NCUR --> DISCO

    DISCO --> HTTP_COND[Conditional HTTP Fetch using ETag & Last-Modified]
    HTTP_COND --> MOD{Page Modified?}
    MOD --> |304 Not Modified| SKP[Skip Extraction - Update Last Checked]
    MOD --> |200 OK (Content Changed)| REEXT[Re-extract Questions]

    REEXT --> DEDUP[Re-run Duplicate Clustering on Changed Set]
    DEDUP --> RECALC[Recalculate Dataset Recency Statuses]
    SKP --> RECALC
    RECALC --> AUDIT[Run Automated Dataset Audit]
    AUDIT --> RPT[Generate research_report.json & .html]
```

---

## 8. Generated-Question Validation Flow

```mermaid
flowchart TD
    TPL[Deterministic Template Engine] --> GEN[Generate Stem + Options + Explanation]
    GEN --> V1{Rule 1: Valid AWS Service/Feature Name?}
    V1 --> |No| REJ[Reject Generation]
    V1 --> |Yes| V2{Rule 2: Accurate Responsibility/Pricing/Scope?}
    V2 --> |No| REJ
    V2 --> |Yes| V3{Rule 3: Exactly One Correct Answer?}
    V3 --> |No| REJ
    V3 --> |Yes| V4{Rule 4: Plausible Distractors from Same Domain?}
    V4 --> |No| REJ
    V4 --> |Yes| V5{Rule 5: Not Duplicate of Existing Question?}
    V5 --> |No| REJ
    V5 --> |Yes| V6{Rule 6: Contains Official AWS Citation URL?}
    V6 --> |No| REJ
    V6 --> |Yes| ACC[Accept as GENERATED_PRACTICE]

    ACC --> PERSIST[Persist to DB with is_generated=True]
```

---

## 9. Storage & Data Management
- **SQLite Database**: File at `data/db/clf_c02.db`. Configured with `PRAGMA journal_mode=WAL`, `PRAGMA synchronous=NORMAL`, and `PRAGMA foreign_keys=ON`.
- **FTS5 Full-Text Search**: Virtual table `questions_fts` indexing stem, options, explanation, services, topics, and domains for millisecond query performance.
- **Content-Addressed Cache**: `data/cache/pages/{url_hash}/{content_hash}` storing raw HTTP response bodies and metadata headers for zero-waste incremental runs.
- **Curriculum Cache**: `data/cache/curriculum/` for official PDF/HTML guides.
- **Log Files**: `data/logs/` for structured JSON and console logs.
- **Exports**: `data/exports/` for JSON, JSONL, CSV, Markdown, and HTML reports.
