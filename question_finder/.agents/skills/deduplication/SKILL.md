# Skill: Deduplication Workflow

## Purpose
Identifies identical, rephrased, or reordered questions across multiple public sources and organizes them into duplicate clusters with a single canonical question.

## Procedure
1. **Text Normalization**:
   - Strip leading question numbers, bullets, whitespace, and punctuation variations.
   - Convert text to lowercase NFC unicode representation.
   - Normalize option keys to canonical alphabetical identifiers.
2. **Level 1 (Exact Hash)**: Compute SHA-256 hash of normalized stem + sorted options + answer keys. Match exact collisions.
3. **Level 2 (Stem Hash)**: Match questions with identical normalized stem hashes.
4. **Level 3 (Option Set Comparison)**: Compare normalized option text sets using Jaccard similarity independent of option key order (threshold >= 0.90).
5. **Level 4 (Answer Mapping Verification)**: Confirm that matching stems and options have compatible correct answer mappings.
6. **Level 5 (Fuzzy RapidFuzz Scoring)**: Apply token sort and token set ratio matching on stems (threshold >= 85).
7. **Cluster Assembly**: Group duplicate questions into `duplicate_clusters` and insert references into `duplicate_members`.
8. **Canonical Selection Algorithm**: Rank cluster members based on verification status (30 pts), explanation clarity (20 pts), source tier (15 pts), provenance quality (15 pts), and stem clarity (10 pts). Set the highest-scoring question as the canonical cluster representative.
