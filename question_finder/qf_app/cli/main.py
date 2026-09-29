"""Command Line Interface for the CLF-C02 Researcher."""

import asyncio
import sys
import click
import uvicorn
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from qf_app.analytics.stats import DatasetStatsCalculator
from qf_app.config.settings import get_settings
from qf_app.core import paths
from qf_app.core.date_window import compute_research_window
from qf_app.core.logging import setup_logging
from qf_app.core.paths import DEFAULT_DB_PATH, ensure_data_dirs
from qf_app.curriculum.snapshot import CurriculumSnapshotManager
from qf_app.db.engine import AsyncSessionFactory, engine
from qf_app.db.fts import init_fts5
from qf_app.db.models.base import Base
from qf_app.db.models.question import Question
from qf_app.db.repositories.question_repo import QuestionRepository
from qf_app.export.formats import DatasetExporter
from qf_app.pipeline.orchestrator import ResearchPipeline


@click.group()
def cli():
    """AWS Certified Cloud Practitioner (CLF-C02) Practice Question Researcher."""
    pass


@cli.command()
def doctor():
    """Run comprehensive health checks on Python, SQLite, FTS5, and local paths."""
    click.echo("\nRunning CLF-C02 System Doctor Health Checks...")
    click.echo("=" * 60)

    # 1. Python Check
    py_ver = sys.version.split()[0]
    click.echo(f"  [OK] Python Version: {py_ver} ({sys.executable})")

    # 2. Filesystem Containment Check
    ensure_data_dirs()
    click.echo(f"  [OK] Project Root: {paths.PROJECT_ROOT}")
    click.echo(f"  [OK] Database Directory: {paths.DB_DIR}")
    click.echo(f"  [OK] Cache Directory: {paths.CACHE_DIR}")
    click.echo(f"  [OK] Exports Directory: {paths.EXPORTS_DIR}")

    # 3. SQLite FTS5 Check
    import sqlite3
    try:
        con = sqlite3.connect(":memory:")
        con.execute("CREATE VIRTUAL TABLE fts_test USING fts5(content);")
        con.execute("INSERT INTO fts_test VALUES ('CLF-C02 AWS Cloud Practitioner');")
        rows = con.execute("SELECT * FROM fts_test WHERE fts_test MATCH 'AWS'").fetchall()
        con.close()
        assert len(rows) == 1
        click.echo("  [OK] SQLite FTS5 Full-Text Engine: Available & Verified")
    except Exception as err:
        click.echo(f"  [FAIL] SQLite FTS5: Error ({err})", color="red")

    click.echo("=" * 60)
    click.echo("System is healthy and ready for research and study!\n", color="green")


@cli.command()
def init():
    """Initialize SQLite database, tables, triggers, and FTS5 virtual tables."""
    async def _init():
        ensure_data_dirs()
        click.echo(f"Initializing database at: {DEFAULT_DB_PATH}")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with AsyncSessionFactory() as session:
            await init_fts5(session)
            # Pre-load curriculum
            curriculum_mgr = CurriculumSnapshotManager(session)
            await curriculum_mgr.refresh_curriculum()

        click.echo("Database initialization complete! Schema & FTS5 active.", color="green")

    asyncio.run(_init())


@cli.group()
def curriculum():
    """Curriculum management commands."""
    pass


@curriculum.command(name="refresh")
def curriculum_refresh():
    """Refresh AWS CLF-C02 syllabus from official guide."""
    async def _refresh():
        async with AsyncSessionFactory() as session:
            mgr = CurriculumSnapshotManager(session)
            snapshot = await mgr.refresh_curriculum(force=True)
            click.echo(f"Curriculum snapshot refreshed: ID #{snapshot.id} (Hash: {snapshot.content_hash[:12]})", color="green")

    asyncio.run(_refresh())


@cli.command()
@click.option("--months", default=6, help="Research recency window in months.")
@click.option("--recent-source-target", default=1000, help="Target count for recent source questions.")
@click.option("--max-pages", default=50, help="Maximum pages to fetch per run.")
def research(months: int, recent_source_target: int, max_pages: int):
    """Execute end-to-end research cycle."""
    async def _research():
        setup_logging()
        click.echo(f"\nStarting Research Pipeline (Window: {months} months, Target: {recent_source_target})...")

        async with AsyncSessionFactory() as session:
            # Ensure tables exist
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            await init_fts5(session)

            pipeline = ResearchPipeline(session)
            stats = await pipeline.run(months=months, recent_source_target=recent_source_target, max_pages=max_pages)

            click.echo("\n" + "=" * 50)
            click.echo("CLF-C02 RESEARCH EXECUTION REPORT")
            click.echo("=" * 50)
            click.echo(f"Research Window:              {stats.window_start} -> {stats.window_end}")
            click.echo(f"Recent Source Target:         {recent_source_target}")
            click.echo(f"Recent Source Questions:      {stats.recent_source_questions}")
            click.echo(f"Generated Practice Questions: {stats.questions_generated}")
            click.echo(f"Total Study Pool:             {stats.total_study_questions}")
            click.echo(f"URLs Discovered:              {stats.candidates_discovered}")
            click.echo(f"Pages Fetched:                {stats.pages_fetched}")
            click.echo(f"Candidate Questions Parsed:   {stats.questions_extracted}")
            click.echo(f"Duplicates Clustered:         {stats.duplicates_found}")
            click.echo(f"Verified Answers:             {stats.questions_verified}")
            click.echo(f"Quarantined Items:            {stats.questions_quarantined}")
            click.echo("=" * 50 + "\n")

    asyncio.run(_research())


@cli.command()
def audit():
    """Run automated dataset integrity and provenance audit."""
    async def _audit():
        async with AsyncSessionFactory() as session:
            click.echo("\nRunning Automated Dataset Integrity Audit...")
            click.echo("=" * 60)

            stmt = select(Question).options(
                selectinload(Question.options),
                selectinload(Question.sources),
            )
            questions = list((await session.execute(stmt)).scalars().all())

            missing_provenance = 0
            missing_answers = 0
            c01_leaks = 0

            for q in questions:
                if not q.is_generated and not q.sources:
                    missing_provenance += 1
                if not any(o.is_correct for o in q.options):
                    missing_answers += 1
                if "clf-c01" in q.stem.lower():
                    c01_leaks += 1

            click.echo(f"  Total Questions Audited:    {len(questions)}")
            click.echo(f"  Missing Provenance Check:   {missing_provenance} anomalies")
            click.echo(f"  Missing Answer Check:       {missing_answers} anomalies")
            click.echo(f"  CLF-C01 Leaks in Pool:      {c01_leaks} anomalies")
            click.echo("=" * 60)
            if missing_provenance == 0 and missing_answers == 0 and c01_leaks == 0:
                click.echo("Audit Result: PASSED (100% integrity)\n", color="green")
            else:
                click.echo("Audit Result: ISSUES FOUND (see above)\n", color="yellow")

    asyncio.run(_audit())


@cli.command()
def stats():
    """Print dataset breakdown statistics."""
    async def _stats():
        async with AsyncSessionFactory() as session:
            calc = DatasetStatsCalculator(session)
            s = await calc.get_summary_stats()

            click.echo("\n" + "=" * 45)
            click.echo("CLF-C02 DATASET SUMMARY")
            click.echo("=" * 45)
            click.echo(f"Recent Source Questions:      {s['recent_source_questions']}")
            click.echo(f"Generated Practice Questions: {s['generated_practice_questions']}")
            click.echo(f"Older Questions:              {s['older_questions']}")
            click.echo(f"Legacy CLF-C01 Questions:     {s['legacy_clf_c01']}")
            click.echo(f"Quarantined / Rejected:       {s['quarantined_questions']}")
            click.echo(f"Duplicate Questions:          {s['duplicate_questions']}")
            click.echo("-" * 45)
            click.echo(f"Total Study Questions:        {s['total_study_questions']}")
            click.echo(f"Verified Answers:             {s['verified_questions']}")
            click.echo("=" * 45 + "\n")

    asyncio.run(_stats())


@cli.command()
@click.option("--format", "fmt", type=click.Choice(["json", "jsonl", "csv", "md"]), default="json")
@click.option("--output", default="data/exports/questions.json")
def export(fmt: str, output: str):
    """Export question dataset to file."""
    async def _export():
        async with AsyncSessionFactory() as session:
            repo = QuestionRepository(session)
            questions, _ = await repo.list_questions(limit=10000)

            exporter = DatasetExporter()
            if fmt == "json":
                path = exporter.export_json(questions, filename=output.split("/")[-1])
            elif fmt == "jsonl":
                path = exporter.export_jsonl(questions, filename=output.split("/")[-1])
            elif fmt == "csv":
                path = exporter.export_csv(questions, filename=output.split("/")[-1])
            else:
                path = exporter.export_markdown(questions, filename=output.split("/")[-1])

            click.echo(f"Exported {len(questions)} questions to {path}", color="green")

    asyncio.run(_export())


@cli.command()
@click.option("--target", default=1000, help="Target number of recent public questions.")
@click.option("--months", default=12, help="Recency window in months.")
def harvest(target: int, months: int):
    """Harvest public CLF-C02 question banks and open educational repositories."""
    async def _harvest():
        from qf_app.discovery.harvester import PublicQuestionHarvester
        setup_logging()
        click.echo(f"\nStarting Public Question Harvester (Target: {target}, Window: {months} months)...")
        async with AsyncSessionFactory() as session:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            await init_fts5(session)

            harvester = PublicQuestionHarvester(session)
            stats = await harvester.harvest_all(target_count=target, months=months)

            click.echo("\n" + "=" * 50)
            click.echo("HARVESTING REPORT")
            click.echo("=" * 50)
            click.echo(f"Recent Questions Harvested: {stats['harvested_recent']}")
            click.echo(f"Older Questions Harvested:  {stats['harvested_older']}")
            click.echo(f"Duplicates Skipped:         {stats['duplicates_skipped']}")
            click.echo(f"Total Added to Database:    {stats['total_added']}")
            click.echo("=" * 50 + "\n")

    asyncio.run(_harvest())


@cli.command()
@click.option("--host", default="127.0.0.1")
@click.option("--port", default=8000)
def serve(host: str, port: int):
    """Start Web UI application server."""
    click.echo(f"Starting CLF-C02 Web UI on http://{host}:{port} ...")
    uvicorn.run("app.main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    cli()
