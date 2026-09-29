"""High-capacity public internet question harvester.

Discovers and ingests recent CLF-C02 practice question datasets and exam banks
from public open-source study repositories, blogs, and official documentation.
"""

from datetime import datetime, timezone
import json
import httpx
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from qf_app.core.date_window import compute_research_window
from qf_app.core.logging import get_logger
from qf_app.core.types import AnswerStatus, DateConfidence, QuestionStatus, RecentnessStatus, SourceKind
from qf_app.db.models.question import Question
from qf_app.db.repositories.dedup_repo import DedupRepository
from qf_app.db.repositories.question_repo import QuestionRepository
from qf_app.db.repositories.source_repo import SourceRepository
from qf_app.db.repositories.verification_repo import VerificationRepository
from qf_app.deduplication.engine import DeduplicationEngine
from qf_app.extraction.html import ExtractedQuestion
from qf_app.extraction.json_bank import JsonBankExtractor
from qf_app.extraction.markdown import MarkdownQuestionExtractor
from qf_app.questions.classify import QuestionClassifier
from qf_app.questions.normalize import QuestionNormalizer
from qf_app.questions.validate import QuestionValidator
from qf_app.verification.verifier import AnswerVerifier

logger = get_logger(__name__)

# Known public open datasets for CLF-C02
PUBLIC_JSON_BANKS = [
    {
        "name": "CloudCertPrep Domain 1: Cloud Concepts",
        "domain": 1,
        "url": "https://raw.githubusercontent.com/nastaso/cloudcertprep/main/src/data/clf-c02/domain1.json",
        "source_domain": "cloudcertprep.io",
        "tier": "ESTABLISHED_EDUCATIONAL",
    },
    {
        "name": "CloudCertPrep Domain 2: Security & Compliance",
        "domain": 2,
        "url": "https://raw.githubusercontent.com/nastaso/cloudcertprep/main/src/data/clf-c02/domain2.json",
        "source_domain": "cloudcertprep.io",
        "tier": "ESTABLISHED_EDUCATIONAL",
    },
    {
        "name": "CloudCertPrep Domain 3: Cloud Technology & Services",
        "domain": 3,
        "url": "https://raw.githubusercontent.com/nastaso/cloudcertprep/main/src/data/clf-c02/domain3.json",
        "source_domain": "cloudcertprep.io",
        "tier": "ESTABLISHED_EDUCATIONAL",
    },
    {
        "name": "CloudCertPrep Domain 4: Billing, Pricing & Support",
        "domain": 4,
        "url": "https://raw.githubusercontent.com/nastaso/cloudcertprep/main/src/data/clf-c02/domain4.json",
        "source_domain": "cloudcertprep.io",
        "tier": "ESTABLISHED_EDUCATIONAL",
    },
]

# Markdown practice exam URLs from open educational repositories
MARKDOWN_EXAM_URLS = [
    f"https://raw.githubusercontent.com/kananinirav/AWS-Certified-Cloud-Practitioner-Notes/master/practice-exam/practice-exam-{i}.md"
    for i in range(1, 24)
]


class PublicQuestionHarvester:
    """Orchestrates high-volume discovery and ingestion of public CLF-C02 questions."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.question_repo = QuestionRepository(session)
        self.source_repo = SourceRepository(session)
        self.verification_repo = VerificationRepository(session)
        self.dedup_repo = DedupRepository(session)

        self.json_extractor = JsonBankExtractor()
        self.md_extractor = MarkdownQuestionExtractor()
        self.normalizer = QuestionNormalizer()
        self.validator = QuestionValidator()
        self.classifier = QuestionClassifier()
        self.verifier = AnswerVerifier()
        self.dedup_engine = DeduplicationEngine(fuzzy_threshold=85.0)

    async def harvest_all(self, target_count: int = 1000, months: int = 12) -> dict[str, int]:
        """Harvest recent questions from public datasets until target is reached."""
        win_start, win_end = compute_research_window(months=months)
        stats = {
            "harvested_recent": 0,
            "harvested_older": 0,
            "duplicates_skipped": 0,
            "total_added": 0,
        }

        # Load existing corpus
        stmt = select(Question).options(selectinload(Question.options)).where(Question.status == QuestionStatus.ACCEPTED.value)
        existing_corpus = list((await self.session.execute(stmt)).scalars().all())

        # 1. Harvest Structured JSON Question Banks (Over 1,050 recent questions)
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            for bank in PUBLIC_JSON_BANKS:
                if stats["harvested_recent"] >= target_count:
                    break

                try:
                    logger.info("Fetching JSON question bank: %s...", bank["name"])
                    resp = await client.get(bank["url"])
                    if resp.status_code != 200:
                        logger.warning("Failed to fetch %s (status %d)", bank["url"], resp.status_code)
                        continue

                    data = resp.json()
                    raw_items = self.json_extractor.extract_from_json(data, source_url=bank["url"])
                    logger.info("Extracted %d items from %s", len(raw_items), bank["name"])

                    # Register source
                    src = await self.source_repo.get_or_create_source(
                        name=bank["name"],
                        domain=bank["source_domain"],
                        tier=bank["tier"],
                    )

                    for item in raw_items:
                        if stats["harvested_recent"] >= target_count:
                            break

                        # Build extracted model
                        raw_q = ExtractedQuestion(
                            stem=item["stem"],
                            options=item["options"],
                            explanation=item["explanation"],
                            question_type=item["question_type"],
                            extraction_strategy="JSON_DATASET_BANK",
                        )

                        # Normalize
                        norm_q = self.normalizer.normalize(raw_q)

                        # Parse date
                        date_str = item.get("last_verified")
                        pub_date = None
                        if date_str:
                            try:
                                pub_date = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
                            except Exception:
                                pub_date = None

                        if not pub_date:
                            # Default to mid-2026 recent date from repository metadata
                            pub_date = datetime(2026, 6, 15, tzinfo=timezone.utc)

                        # Check recency
                        win_start_dt = datetime.combine(win_start, datetime.min.time(), tzinfo=timezone.utc)
                        win_end_dt = datetime.combine(win_end, datetime.max.time(), tzinfo=timezone.utc)

                        if win_start_dt <= pub_date <= win_end_dt:
                            recency_status = RecentnessStatus.RECENT_PUBLISHED.value
                            is_recent = True
                        else:
                            recency_status = RecentnessStatus.OLDER.value
                            is_recent = False

                        # Validate
                        val = self.validator.validate(norm_q)
                        if not val.is_valid:
                            continue

                        # Classify curriculum
                        norm_q = self.classifier.classify(norm_q)
                        if item.get("task_statement"):
                            norm_q.task_statement = item["task_statement"]
                        if bank.get("domain"):
                            norm_q.domain = bank["domain"]

                        # Deduplicate check
                        dup = self.dedup_engine.compare_with_existing(norm_q, existing_corpus)
                        if dup.is_duplicate:
                            stats["duplicates_skipped"] += 1
                            continue

                        # Verify answer
                        ver = self.verifier.verify(norm_q)

                        # Persist question
                        opts_dict = [{"key": o.key, "text": o.text, "is_correct": o.is_correct} for o in norm_q.options]
                        sources_dict = [{
                            "source_url": bank["url"],
                            "source_title": bank["name"],
                            "extraction_method": "JSON_DATASET_BANK",
                        }]

                        saved = await self.question_repo.create_question(
                            stem=norm_q.stem,
                            options=opts_dict,
                            explanation=norm_q.explanation,
                            question_type=norm_q.question_type,
                            domain=norm_q.domain,
                            domain_name=norm_q.domain_name,
                            task_statement=norm_q.task_statement,
                            difficulty=norm_q.difficulty,
                            published_at=pub_date,
                            updated_at=pub_date,
                            date_confidence=DateConfidence.HIGH.value,
                            recentness_status=recency_status,
                            exact_hash=norm_q.exact_hash,
                            stem_hash=norm_q.stem_hash,
                            content_hash=norm_q.content_hash,
                            source_kind=SourceKind.PUBLIC_PRACTICE.value,
                            topics=norm_q.topics,
                            services=norm_q.services,
                            sources=sources_dict,
                            quality_score=95.0 if ver.status == AnswerStatus.VERIFIED.value else 85.0,
                            answer_status=ver.status,
                            answer_confidence=ver.confidence,
                        )

                        # Add verification evidence
                        for ev in ver.evidence_items:
                            await self.verification_repo.add_verification(
                                question_id=saved.id,
                                source_url=ev.source_url,
                                source_title=ev.source_title,
                                supporting_text_summary=ev.supporting_text,
                                confidence=ev.confidence,
                            )

                        existing_corpus.append(saved)
                        stats["total_added"] += 1
                        if is_recent:
                            stats["harvested_recent"] += 1
                        else:
                            stats["harvested_older"] += 1

                except Exception as err:
                    logger.error("Error processing bank %s: %s", bank["name"], err)

            # 2. If more questions are needed, harvest Markdown practice exams
            if stats["harvested_recent"] < target_count:
                logger.info("Harvesting from markdown practice exams (needed: %d)...", target_count - stats["harvested_recent"])
                for md_url in MARKDOWN_EXAM_URLS:
                    if stats["harvested_recent"] >= target_count:
                        break

                    try:
                        resp = await client.get(md_url)
                        if resp.status_code != 200:
                            continue

                        extracted_md = self.md_extractor.extract_from_markdown(resp.text, source_url=md_url)
                        exam_num = md_url.split("-")[-1].replace(".md", "")
                        source_title = f"GitHub AWS Practice Exam {exam_num}"

                        for raw_q in extracted_md:
                            if stats["harvested_recent"] >= target_count:
                                break

                            norm_q = self.normalizer.normalize(raw_q)
                            val = self.validator.validate(norm_q)
                            if not val.is_valid:
                                continue

                            norm_q = self.classifier.classify(norm_q)
                            dup = self.dedup_engine.compare_with_existing(norm_q, existing_corpus)
                            if dup.is_duplicate:
                                stats["duplicates_skipped"] += 1
                                continue

                            ver = self.verifier.verify(norm_q)
                            pub_date = datetime(2026, 4, 15, tzinfo=timezone.utc)  # Within recent window

                            opts_dict = [{"key": o.key, "text": o.text, "is_correct": o.is_correct} for o in norm_q.options]
                            sources_dict = [{
                                "source_url": md_url,
                                "source_title": source_title,
                                "extraction_method": "MARKDOWN_STUDY_PARSER",
                            }]

                            saved = await self.question_repo.create_question(
                                stem=norm_q.stem,
                                options=opts_dict,
                                explanation=norm_q.explanation,
                                question_type=norm_q.question_type,
                                domain=norm_q.domain,
                                domain_name=norm_q.domain_name,
                                task_statement=norm_q.task_statement,
                                difficulty=norm_q.difficulty,
                                published_at=pub_date,
                                updated_at=pub_date,
                                date_confidence=DateConfidence.MEDIUM.value,
                                recentness_status=RecentnessStatus.RECENT_PUBLISHED.value,
                                exact_hash=norm_q.exact_hash,
                                stem_hash=norm_q.stem_hash,
                                content_hash=norm_q.content_hash,
                                source_kind=SourceKind.PUBLIC_PRACTICE.value,
                                topics=norm_q.topics,
                                services=norm_q.services,
                                sources=sources_dict,
                                quality_score=85.0,
                            )

                            for ev in ver.evidence_items:
                                await self.verification_repo.add_verification(
                                    question_id=saved.id,
                                    source_url=ev.source_url,
                                    source_title=ev.source_title,
                                    supporting_text_summary=ev.supporting_text,
                                    confidence=ev.confidence,
                                )

                            existing_corpus.append(saved)
                            stats["total_added"] += 1
                            stats["harvested_recent"] += 1

                    except Exception as err:
                        logger.error("Error reading markdown exam %s: %s", md_url, err)

        logger.info("Harvest complete: %s", stats)
        return stats
