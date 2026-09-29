"""Central path resolver.

All paths are strictly computed relative to the project root directory.
No files or data are ever placed on the C:\\ drive or external locations.
"""

from pathlib import Path

# Project root directory: determined dynamically from this file location
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Data storage directories (all stay inside project on E:\)
DATA_DIR = PROJECT_ROOT / "data"
DB_DIR = DATA_DIR / "db"
CACHE_DIR = DATA_DIR / "cache"
PAGE_CACHE_DIR = CACHE_DIR / "pages"
CURRICULUM_CACHE_DIR = CACHE_DIR / "curriculum"
EXPORTS_DIR = DATA_DIR / "exports"
LOGS_DIR = DATA_DIR / "logs"

# Configuration directory & files
CONFIG_DIR = PROJECT_ROOT / "config"
SETTINGS_FILE = CONFIG_DIR / "settings.yaml"
SOURCES_FILE = CONFIG_DIR / "sources.yaml"
QUERIES_FILE = CONFIG_DIR / "queries.yaml"
TAXONOMY_FILE = CONFIG_DIR / "taxonomy.yaml"
REJECTION_RULES_FILE = CONFIG_DIR / "rejection_rules.yaml"

# Schemas directory
SCHEMAS_DIR = PROJECT_ROOT / "schemas"
QUESTION_SCHEMA_FILE = SCHEMAS_DIR / "question.schema.json"

# SQLite Database path & async connection URL
DEFAULT_DB_PATH = DB_DIR / "clf_c02.db"
DEFAULT_DB_URL = f"sqlite+aiosqlite:///{DEFAULT_DB_PATH}"

# Static assets and Jinja2 templates
STATIC_DIR = PROJECT_ROOT / "qf_app" / "web" / "static"
TEMPLATES_DIR = PROJECT_ROOT / "qf_app" / "web" / "templates"
VENDOR_DIR = STATIC_DIR / "vendor"
HTMX_LOCAL_PATH = VENDOR_DIR / "htmx.min.js"

# Tests & fixtures
TESTS_DIR = PROJECT_ROOT / "tests"
FIXTURES_DIR = TESTS_DIR / "fixtures"


def ensure_data_dirs() -> None:
    """Ensure that all runtime data directories exist locally."""
    for directory in [
        DB_DIR,
        PAGE_CACHE_DIR,
        CURRICULUM_CACHE_DIR,
        EXPORTS_DIR,
        LOGS_DIR,
        VENDOR_DIR,
    ]:
        directory.mkdir(parents=True, exist_ok=True)
