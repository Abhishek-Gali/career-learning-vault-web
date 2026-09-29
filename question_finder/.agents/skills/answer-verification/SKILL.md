# Skill: Answer Verification Workflow

## Purpose
Validates extracted answer correctness against official AWS specifications and technical documentation.

## Procedure
1. **Initial Answer Ingestion**: Read extracted source answer and associated explanation.
2. **Concept & Service Identification**: Extract core AWS services and concepts mentioned in the question stem and options.
3. **Official Documentation Lookup**: Query cached AWS official documentation and exam guides for the identified services/concepts.
4. **Consistency Evaluation**:
   - Compare service definitions and feature characteristics (e.g., S3 object vs. EBS block, IAM role vs. IAM user).
   - Evaluate whether the extracted answer is directly supported, contradicted, or ambiguous.
5. **Status Assignment**:
   - `VERIFIED`: Authoritative AWS documentation explicitly confirms the extracted answer.
   - `PARTIALLY_VERIFIED`: Concept aligns with AWS principles, but exact question scenario relies on secondary reasoning.
   - `CONFLICTING`: Official AWS documentation directly contradicts the extracted answer. Flag for human review.
   - `UNVERIFIED`: Extracted answer lacks supporting documentation reference.
6. **Provenance Recording**: Create `verification_records` linking the question ID, AWS reference URL, citation snippet, timestamp, and confidence score.
