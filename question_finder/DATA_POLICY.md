# DATA_POLICY.md — Data Governance, Provenance & Content Policy

## 1. Source Categories & Tiers
The system maintains a structured taxonomy of source registries:
- **OFFICIAL**: Official AWS documentation, exam guides, whitepapers, AWS Skill Builder sample questions, AWS re:Post.
- **ESTABLISHED_EDUCATIONAL**: Established cloud training platforms, reputable educational portals, well-known technical blogs.
- **COMMUNITY_EDUCATIONAL**: Community discussion forums, personal study blogs, open-source repositories.
- **UNVERIFIED**: Newly discovered web pages pending reputation evaluation.
- **REJECTED**: Sources with explicit copyright restrictions against crawling, malicious markup, or unauthorized exam dump claims.

## 2. Dynamic Recency Policy
- **Research Window**: Dynamically computed at runtime as `[today - 6 months, today]`.
- **Date Categories**:
  - `RECENT_PUBLISHED`: Published within the active 6-month research window.
  - `RECENT_UPDATED`: Originally published prior to the window, but substantially modified/updated within the window.
  - `OLDER`: Valid CLF-C02 questions outside the 6-month window (preserved for study, but counted separately).
  - `LEGACY`: Material specifically referencing CLF-C01 or retired concepts.
  - `UNKNOWN_DATE`: Undated public material (retained under separate category).

## 3. Mandatory Provenance Tracking
Every sourced question must store and retain complete lineage:
- `source_id`: Reference to registered domain entity.
- `source_url`: Full canonical URL where the question was discovered.
- `retrieved_at`: ISO 8601 UTC timestamp of content fetch.
- `content_hash`: SHA-256 hash of the source page snapshot.
- `date_source`: Exact tier and element providing publication/update timestamp (e.g., `JSON_LD`, `OPENGRAPH`, `SITEMAP`).
- `date_confidence`: Assessment rating (`HIGH`, `MEDIUM`, `LOW`, `UNKNOWN`).

## 4. Question Categories & Dataset Separation
The database strictly segregates questions by their origin and validation state:
1. **Recent Public Source Questions**: Public practice questions with verified dates <= 6 months.
2. **Generated Practice Questions**: Supplementary questions synthesized deterministically from AWS docs. Must never be labeled or displayed as sourced questions.
3. **Older Practice Questions**: High quality questions published > 6 months ago.
4. **Legacy CLF-C01 Questions**: Historical material containing retired terms/services.
5. **Quarantined / Rejected**: Material failing security, provenance, or ethical standards.

## 5. Licensing & Copyright Compliance
- Public accessibility is **not** treated as permission for bulk commercial redistribution.
- The system operates strictly as a local-first personal research and study application.
- Full source URLs, titles, and author attributions are preserved for every item.
- Large verbatim third-party page bodies are never redistributed; only extracted question structures and evidence summaries are stored locally.

## 6. Retention and Auditability
- Source snapshot records and hash history are preserved across refresh cycles.
- When questions age out of the 6-month window during a refresh, they transition from `RECENT` to `OLDER` status without data deletion.
