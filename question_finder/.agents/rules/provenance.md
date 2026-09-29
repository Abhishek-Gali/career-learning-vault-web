# Provenance & Data Lineage Invariants

- **Mandatory Linkage**: Every source question must record `source_url`, `page_id`, `published_at`, `updated_at`, `retrieved_at`, and `content_hash`.
- **No Fabricated Provenance**: Never manufacture a source URL, citation, or date. If publication date cannot be resolved, assign `date_confidence=UNKNOWN`.
- **Date Source Hierarchy**: Follow the strict 10-level hierarchy (schema.org -> JSON-LD -> `<time>` -> OpenGraph -> meta -> visible text -> sitemap).
- **Audit Trails**: Every merge, quarantine, rejection, or canonical selection must insert a record into `audit_logs`.
