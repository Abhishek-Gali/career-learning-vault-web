# Database & SQLite Invariants

- **Engine & Driver**: Use SQLAlchemy 2.0 Async with `aiosqlite`. Connection string derived from `app.core.paths.DEFAULT_DB_URL`.
- **Pragmas**: Every database connection must immediately execute:
  - `PRAGMA journal_mode=WAL;`
  - `PRAGMA synchronous=NORMAL;`
  - `PRAGMA foreign_keys=ON;`
- **FTS5 Integration**: Maintain `questions_fts` virtual table synchronized via database triggers or repository events.
- **Async Relationships**: Always eager load relationships intended for serialization (`selectinload` or `joinedload`) to prevent `MissingGreenlet` errors.
- **Self-Contained Storage**: Database files must reside at `data/db/clf_c02.db`. Test databases must reside at `data/db/test_*.db`.
