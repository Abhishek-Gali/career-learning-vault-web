# CONTRIBUTING.md — Developer Guidelines

## 1. Development Environment Setup
Always use the self-contained virtual environment within the repository root:
```powershell
.\scripts\setup.ps1
.venv\Scripts\Activate.ps1
```

## 2. Code Quality & Standards
- Type annotations required on all function arguments and returns.
- Pydantic models for all external input/output validation.
- All database operations must use SQLAlchemy async repositories.
- No `print()` statements in application code — use `app.core.logging.get_logger(__name__)`.
- Absolute filesystem paths must resolve through `app.core.paths`.

## 3. Running Automated Tests
```powershell
pytest tests/ -v
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/e2e/ -v
```

## 4. Test Coverage & Fixtures
When adding or updating extraction strategies or classifiers, create corresponding offline HTML/JSON fixture files in `tests/fixtures/`. Never run automated test suites against live third-party websites.
