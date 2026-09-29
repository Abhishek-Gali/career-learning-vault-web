"""SQLite FTS5 Full-Text Search integration and virtual table management."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

FTS_TABLE_NAME = "questions_fts"

CREATE_FTS_TABLE_SQL = f"""
CREATE VIRTUAL TABLE IF NOT EXISTS {FTS_TABLE_NAME} USING fts5(
    question_id UNINDEXED,
    stem,
    options_text,
    explanation,
    services,
    topics,
    domain_name,
    task_statement,
    source_title,
    tokenize='porter unicode61'
);
"""


async def init_fts5(session: AsyncSession) -> None:
    """Create the FTS5 virtual table if it does not exist."""
    await session.execute(text(CREATE_FTS_TABLE_SQL))
    await session.commit()


async def sync_question_fts(
    session: AsyncSession,
    question_id: int,
    stem: str,
    options_text: str,
    explanation: str,
    services: str,
    topics: str,
    domain_name: str,
    task_statement: str,
    source_title: str,
) -> None:
    """Insert or update FTS5 entry for a question."""
    # Delete existing index record if present
    await session.execute(
        text(f"DELETE FROM {FTS_TABLE_NAME} WHERE question_id = :qid"),
        {"qid": question_id},
    )
    # Insert new record
    await session.execute(
        text(
            f"""
            INSERT INTO {FTS_TABLE_NAME} (
                question_id, stem, options_text, explanation, services, topics, domain_name, task_statement, source_title
            ) VALUES (
                :qid, :stem, :opts, :exp, :svc, :top, :dom, :task, :src
            )
            """
        ),
        {
            "qid": question_id,
            "stem": stem,
            "opts": options_text,
            "exp": explanation,
            "svc": services,
            "top": topics,
            "dom": domain_name,
            "task": task_statement,
            "src": source_title,
        },
    )
    await session.commit()


async def search_questions_fts(session: AsyncSession, query: str, limit: int = 50) -> list[int]:
    """Execute FTS5 search query and return matching question IDs."""
    sanitized_query = query.replace("'", " ").replace('"', " ").strip()
    if not sanitized_query:
        return []

    sql = f"""
    SELECT question_id, rank
    FROM {FTS_TABLE_NAME}
    WHERE {FTS_TABLE_NAME} MATCH :match_query
    ORDER BY rank
    LIMIT :limit
    """
    result = await session.execute(text(sql), {"match_query": sanitized_query, "limit": limit})
    rows = result.fetchall()
    return [int(row[0]) for row in rows]
