# Testing Rules

- **Offline by Default**: Automated test suites (`pytest tests/`) must execute 100% offline using the 17 fixture types in `tests/fixtures/`.
- **Async Fixtures**: Use `pytest-asyncio` with explicit `asyncio_mode = "auto"`.
- **Database Isolation**: Unit and integration tests must run against isolated temporary SQLite databases within `data/db/test_*.db` and clean up upon completion.
- **Coverage**: Maintain tests for all parser strategies, URL normalizers, dedup levels, and curriculum mappings.
