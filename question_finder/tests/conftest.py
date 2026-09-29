"""Pytest configuration and async test fixtures."""

import uuid
from typing import AsyncGenerator
import pytest
import pytest_asyncio
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from qf_app.core.paths import DB_DIR, FIXTURES_DIR, ensure_data_dirs
from qf_app.db.fts import init_fts5
from qf_app.db.models.base import Base

ensure_data_dirs()


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide isolated async SQLite database session inside data/db/test_*.db."""
    test_db_path = DB_DIR / f"test_{uuid.uuid4().hex[:8]}.db"
    test_db_url = f"sqlite+aiosqlite:///{test_db_path}"

    test_engine = create_async_engine(test_db_url, echo=False)

    @event.listens_for(test_engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        await init_fts5(session)
        yield session

    await test_engine.dispose()
    if test_db_path.exists():
        try:
            test_db_path.unlink(missing_ok=True)
        except Exception:
            pass


@pytest.fixture
def load_fixture():
    """Helper to load fixture text from tests/fixtures/."""
    def _loader(filename: str) -> str:
        path = FIXTURES_DIR / filename
        return path.read_text(encoding="utf-8")
    return _loader
