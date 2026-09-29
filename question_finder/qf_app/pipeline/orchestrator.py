"""Main Research Pipeline Orchestrator."""

from datetime import datetime, timezone
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from qf_app.config.settings import AppSettings, get_settings
from qf_app.content_safety.classifier import ContentSafetyClassifier
from qf_app.core.date_window import compute_research_window
from qf_app.core.logging import get_logger
from qf_app.core.types import AnswerStatus, CandidateStatus, ContentSafetyStatus, QuestionStatus, RecentnessStatus, SourceKind
from qf_app.curriculum.snapshot import CurriculumSnapshotManager
from qf_app.deduplication.clustering import ClusterManager
from qf_app.deduplication.engine import DeduplicationEngine
from qf_app.discovery.candidate_manager import CandidateManager
from qf_app.discovery.providers.direct import DirectSourceProvider
from qf_app.discovery.providers.searxng import SearXNGProvider
from qf_app.discovery.query_builder import QueryMatrixBuilder
from qf_app.extraction.dates import DateAnalyzer
from qf_app.extraction.html import HtmlQuestionExtractor
from qf_app.extraction.metadata import MetadataExtractor
from qf_app.fetching.http import HttpFetcher
from qf_app.fetching.url import normalize_url
from qf_app.generation.templates import TemplateGenerator
from qf_app.generation.validator import GenerationValidator
from qf_app.db.models.question import Question
from qf_app.db.models.research import ResearchRun
from qf_app.db.repositories.candidate_repo import CandidateRepository
from qf_app.db.repositories.question_repo import QuestionRepository
from qf_app.db.repositories.source_repo import SourceRepository
from qf_app.db.repositories.verification_repo import VerificationRepository
from qf_app.pipeline.checkpoint import CheckpointManager
from qf_app.pipeline.stages import PipelineStage
from qf_app.questions.classify import QuestionClassifier
from qf_app.questions.normalize import QuestionNormalizer
from qf_app.questions.validate import QuestionValidator
from qf_app.verification.verifier import AnswerVerifier

logger = get_logger(__name__)


class PipelineStats(BaseModel):
    """Statistics for a research pipeline execution."""

    run_id: int | None = None
    window_start: str = ""
    window_end: str = ""
    queries_generated: int = 0
    candidates_discovered: int = 0
    pages_fetched: int = 0
    fetch_failures: int = 0
    questions_extracted: int = 0
    questions_accepted: int = 0
    questions_quarantined: int = 0
    questions_rejected: int = 0
    duplicates_found: int = 0
    questions_verified: int = 0
    questions_generated: int = 0
    recent_source_questions: int = 0
    total_study_questions: int = 0


class ResearchPipeline:
    """End-to-end research orchestrator."""

    def __init__(self, session: AsyncSession, settings: AppSettings | None = None) -> None:
        self.session = session
        self.settings = settings or get_settings()

        # Repositories & Checkpoints
        self.checkpoint = CheckpointManager(session)
        self.candidate_repo = CandidateRepository(session)
        self.question_repo = QuestionRepository(session)
        self.source_repo = SourceRepository(session)
        self.verification_repo = VerificationRepository(session)

        # Components
        self.curriculum_mgr = CurriculumSnapshotManager(session)
        self.query_builder = QueryMatrixBuilder()
        self.candidate_mgr = CandidateManager(session)
        self.fetcher = HttpFetcher(
            timeout=float(self.settings.crawler.request_timeout_seconds),
            user_agent=self.settings.crawler.user_agent,
            respect_robots=self.settings.crawler.respect_robots,
        )
        self.meta_extractor = MetadataExtractor()
        self.date_analyzer = DateAnalyzer()
        self.html_extractor = HtmlQuestionExtractor()
        self.normalizer = QuestionNormalizer()
        self.validator = QuestionValidator()
        self.classifier = QuestionClassifier()
        self.safety = ContentSafetyClassifier()
        self.verifier = AnswerVerifier()
        self.dedup = DeduplicationEngine(fuzzy_threshold=float(self.settings.quality.fuzzy_duplicate_threshold))
        self.cluster_mgr = ClusterManager(session)
        self.template_gen = TemplateGenerator()
        self.gen_validator = GenerationValidator()

    async def run(
        self,
        months: int = 6,
        recent_source_target: int = 1000,
        max_pages: int = 50,
    ) -> PipelineStats:
        """Execute the full research pipeline."""
        start_date, end_date = compute_research_window(months=months)
        stats = PipelineStats(
            window_start=start_date.isoformat(),
            window_end=end_date.isoformat(),
        )

        # 1. Create Research Run Record
        run = ResearchRun(
            window_start=start_date,
            window_end=end_date,
            config_snapshot=self.settings.model_dump(),
            status="RUNNING",
        )
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        stats.run_id = run.id
        logger.info("Started Research Run ID: %d for window %s to %s", run.id, stats.window_start, stats.window_end)

        # 2. Stage: Refresh Curriculum
        await self.checkpoint.update_stage(run.id, PipelineStage.REFRESH_CURRICULUM.value)
        await self.curriculum_mgr.refresh_curriculum()

        # 3. Stage: Generate Query Matrix & Search Discovery
        await self.checkpoint.update_stage(run.id, PipelineStage.GENERATE_QUERIES.value)
        queries = self.query_builder.build_query_matrix()
        stats.queries_generated = len(queries)

        await self.checkpoint.update_stage(run.id, PipelineStage.SEARCH_DISCOVERY.value)
        direct_prov = DirectSourceProvider()
        for q in queries[:10]:  # batch of discovery queries
            results = await direct_prov.search(q, limit=5)
            added = await self.candidate_mgr.ingest_search_results(run.id, results)
            stats.candidates_discovered += added

        # 4. Stage: Fetch Candidates & Extract Content
        await self.checkpoint.update_stage(run.id, PipelineStage.FETCH_PAGES.value)
        pending_candidates = await self.candidate_mgr.get_next_candidates(limit=max_pages)

        # Fetch existing questions for duplicate checking
        stmt = select(Question).where(Question.status == QuestionStatus.ACCEPTED.value)
        existing_corpus = list((await self.session.execute(stmt)).scalars().all())

        for cand in pending_candidates:
            try:
                fetch_res = await self.fetcher.fetch(cand.url)
                stats.pages_fetched += 1
                await self.candidate_repo.update_candidate_status(cand.id, CandidateStatus.FETCHED.value)

                # Find or create source
                src = await self.source_repo.get_or_create_source(
                    name=cand.domain,
                    domain=cand.domain,
                )

                # Metadata & Date extraction
                meta = self.meta_extractor.extract(fetch_res.body)
                date_res = self.date_analyzer.analyze(
                    meta,
                    fetch_res.body,
                    window_start=datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc),
                    window_end=datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc),
                )

                # Persist Page
                page = await self.source_repo.create_or_update_page(
                    source_id=src.id,
                    url=fetch_res.url,
                    canonical_url=normalize_url(fetch_res.url),
                    title=meta.title,
                    content_hash=fetch_res.content_hash,
                    etag=fetch_res.etag,
                    last_modified=fetch_res.last_modified,
                    published_at=date_res.published_at,
                    updated_at=date_res.updated_at,
                    date_source=date_res.date_source,
                    date_confidence=date_res.confidence,
                )
                await self.source_repo.add_snapshot(page.id, fetch_res.content_hash, fetch_res.status_code, fetch_res.content_length)

                # Extract Questions
                extracted_qs = self.html_extractor.extract_questions(fetch_res.body)
                stats.questions_extracted += len(extracted_qs)

                for raw_q in extracted_qs:
                    # Normalize
                    norm_q = self.normalizer.normalize(raw_q)
                    norm_q.published_at = date_res.published_at
                    norm_q.updated_at = date_res.updated_at
                    norm_q.date_confidence = date_res.confidence
                    norm_q.recentness_status = date_res.recentness_status
                    norm_q.source_url = fetch_res.url
                    norm_q.source_title = meta.title or cand.domain
                    norm_q.page_id = page.id

                    # Validate Structure
                    val_res = self.validator.validate(norm_q)
                    if not val_res.is_valid:
                        stats.questions_rejected += 1
                        continue

                    # Content Safety Review
                    safety_status, safety_reason = self.safety.evaluate(norm_q.stem)
                    if safety_status == ContentSafetyStatus.QUARANTINED:
                        stats.questions_quarantined += 1
                        continue

                    # Classify Curriculum
                    norm_q = self.classifier.classify(norm_q)

                    # Verify Answer
                    ver_res = self.verifier.verify(norm_q)
                    if ver_res.status == AnswerStatus.VERIFIED.value:
                        stats.questions_verified += 1

                    # Deduplication Check
                    dup_match = self.dedup.compare_with_existing(norm_q, existing_corpus)

                    # Persist Question
                    opts_dict = [{"key": o.key, "text": o.text, "is_correct": o.is_correct} for o in norm_q.options]
                    sources_dict = [{"page_id": page.id, "source_url": fetch_res.url, "source_title": meta.title, "extraction_method": norm_q.extraction_method}]

                    created_q = await self.question_repo.create_question(
                        stem=norm_q.stem,
                        options=opts_dict,
                        explanation=norm_q.explanation,
                        question_type=norm_q.question_type,
                        domain=norm_q.domain,
                        domain_name=norm_q.domain_name,
                        task_statement=norm_q.task_statement,
                        difficulty=norm_q.difficulty,
                        published_at=norm_q.published_at,
                        updated_at=norm_q.updated_at,
                        retrieved_at=norm_q.retrieved_at,
                        date_confidence=norm_q.date_confidence,
                        recentness_status=norm_q.recentness_status,
                        exact_hash=norm_q.exact_hash,
                        stem_hash=norm_q.stem_hash,
                        content_hash=norm_q.content_hash,
                        source_kind=SourceKind.PUBLIC_PRACTICE.value,
                        topics=norm_q.topics,
                        services=norm_q.services,
                        sources=sources_dict,
                        quality_score=norm_q.quality_score,
                    )

                    # Store Verification
                    for ev in ver_res.evidence_items:
                        await self.verification_repo.add_verification(
                            question_id=created_q.id,
                            source_url=ev.source_url,
                            source_title=ev.source_title,
                            supporting_text_summary=ev.supporting_text,
                            confidence=ev.confidence,
                        )

                    # Handle Duplicate Cluster
                    if dup_match.is_duplicate and dup_match.matched_question_id:
                        stats.duplicates_found += 1
                        matched_q = await self.question_repo.get_by_id(dup_match.matched_question_id)
                        if matched_q:
                            await self.cluster_mgr.assign_duplicate(
                                new_question=created_q,
                                matched_question=matched_q,
                                similarity_score=dup_match.similarity_score,
                                comparison_method=dup_match.level,
                            )
                    else:
                        existing_corpus.append(created_q)
                        stats.questions_accepted += 1
                        if norm_q.recentness_status in (RecentnessStatus.RECENT_PUBLISHED.value, RecentnessStatus.RECENT_UPDATED.value):
                            stats.recent_source_questions += 1

            except Exception as err:
                stats.fetch_failures += 1
                logger.debug("Fetch/processing failed for candidate %s: %s", cand.url, err)
        # 4.5 Public Dataset Harvester
        if stats.recent_source_questions < recent_source_target:
            logger.info("Engaging Public Question Harvester to reach target %d...", recent_source_target)
            from qf_app.discovery.harvester import PublicQuestionHarvester
            harvester = PublicQuestionHarvester(self.session)
            needed = recent_source_target - stats.recent_source_questions
            h_stats = await harvester.harvest_all(target_count=needed, months=months)
            stats.recent_source_questions += h_stats["harvested_recent"]
            stats.questions_verified += h_stats["harvested_recent"]
            stats.duplicates_found += h_stats["duplicates_skipped"]

        # 5. Supplementary Practice Generation
        if self.settings.generation.enabled and stats.recent_source_questions < recent_source_target:
            needed = min(15, recent_source_target - stats.recent_source_questions)
            generated_list = self.template_gen.generate_batch(count_per_domain=needed // 4 + 1)
            for gen_q in generated_list:
                gen_val = self.gen_validator.validate(gen_q)
                if not gen_val.is_valid:
                    continue

                norm_opts = [{"key": o.key, "text": o.text, "is_correct": o.is_correct} for o in gen_q.options]
                created_gen_q = await self.question_repo.create_question(
                    stem=gen_q.stem,
                    options=norm_opts,
                    explanation=gen_q.explanation,
                    domain=gen_q.domain,
                    domain_name=gen_q.domain_name,
                    task_statement=gen_q.task_statement,
                    source_kind=SourceKind.GENERATED_PRACTICE.value,
                    is_generated=True,
                    generation_method=gen_q.generation_method,
                    topics=gen_q.topics,
                    services=gen_q.services,
                    quality_score=90.0,
                )
                stats.questions_generated += 1

        # 6. Finalize Run Record
        counts = await self.question_repo.get_counts_by_category()
        stats.total_study_questions = counts["total_questions"]
        stats.recent_source_questions = counts["recent_source_questions"]

        run.completed_at = datetime.now(timezone.utc)
        run.status = "COMPLETED"
        run.stats_json = stats.model_dump()
        await self.session.commit()

        logger.info("Research run %d completed. Recent source: %d, Generated: %d, Total: %d",
                    run.id, stats.recent_source_questions, stats.questions_generated, stats.total_study_questions)

        return stats
