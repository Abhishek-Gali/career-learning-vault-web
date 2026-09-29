# AGENTS.md — CLF-C02 Recent Practice Question Researcher

## Mission
Build a completely free, local-first research and study system that discovers publicly accessible AWS Certified Cloud Practitioner (CLF-C02) practice questions, determines recentness, validates structure, maps to the current curriculum, verifies answers against authoritative AWS documentation, detects duplicates, stores full provenance, and provides a searchable study/quiz interface.

All project dependencies, databases, caches, logs, and artifacts MUST remain strictly self-contained within the project root directory on `E:\` (nothing touches `C:\`).

## Engineering Principles
- **Correctness over speed**: Every question, answer, and date must be verified.
- **Provenance over convenience**: Every sourced question must track source URL, page ID, snapshot, date evidence, and extraction method.
- **Deterministic before probabilistic**: Regex and DOM parsing before heuristics; explicit taxonomy matching before fuzzy scoring; deterministic templates before probabilistic models.
- **No hidden transformations**: Transformations, normalizations, and clustering steps must be auditable.
- **No fabricated facts or data**: Never invent dates, URLs, answers, explanations, or exam questions.
- **No silent data corruption**: If extraction fails or data is malformed, reject or quarantine with explicit logging.
- **Incremental and restartable**: Research runs must checkpoint every stage; failed targets must not destroy previous run results.
- **Test before declaring completion**: Verify through fixtures, unit tests, integration tests, and full E2E runs.

## Mandatory Content Rules
- **Distinguish source kinds**: Never represent generated questions or older questions as recent public source questions.
- **Separate counters**: Maintain clear, separate counters for Recent Source Questions, Generated Practice Questions, Older Questions, Legacy CLF-C01, Quarantined, and Duplicates.
- **Preserve evidence**: Verification records must link to official AWS documentation or authoritative references.
- **Respect access rules**: Do not bypass authentication, CAPTCHAs, or anti-bot mechanisms. Obey robots.txt and rate limits.
- **No misleading marketing**: Do not use claims like "real exam questions" or "100% pass guarantee". Use accurate terms: "recent publicly available CLF-C02 practice questions" and "generated practice questions".

## Development Rules
- Use full Python type annotations throughout the codebase.
- Use Pydantic v2 for data validation and schema definitions.
- Use structured logging (standard library `logging` or JSON structured output); no raw `print()` statements in production code.
- Write modular, single-responsibility components with minimal coupling.
- Keep configuration strictly separated in YAML/environment files. No hardcoded credentials or operational constants.
- Ensure all paths resolve relative to `app.core.paths.PROJECT_ROOT`.

## Modular Rules & Skills
- Stable architectural and coding invariants: `.agents/rules/*.md`
- Multi-step operational workflows: `.agents/skills/*/SKILL.md`
