"""Configuration loader and Pydantic validation models."""

from pathlib import Path
from typing import Any
import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from qf_app.core.paths import (
    DEFAULT_DB_URL,
    QUERIES_FILE,
    REJECTION_RULES_FILE,
    SETTINGS_FILE,
    SOURCES_FILE,
    TAXONOMY_FILE,
)


class ResearchConfig(BaseModel):
    months: int = 6
    recent_source_target: int = 1000
    total_study_target: int = 1000
    language: str = "en"
    date_policy: str = "RECENT_PUBLICATION_OR_SUBSTANTIAL_UPDATE"


class CrawlerConfig(BaseModel):
    max_pages_per_run: int = 5000
    request_timeout_seconds: int = 20
    max_content_size_mb: int = 10
    max_concurrency: int = 8
    respect_robots: bool = True
    max_redirects: int = 5
    user_agent: str = "CLF-C02-Researcher/0.1 (educational-study-research-tool; local-first)"


class QualityConfig(BaseModel):
    minimum_score: int = 60
    fuzzy_duplicate_threshold: int = 85


class VerificationConfig(BaseModel):
    require_answer: bool = True
    max_evidence_sources: int = 5


class GenerationConfig(BaseModel):
    enabled: bool = True
    count_only_as_supplementary: bool = True
    max_per_topic: int = 25


class SearchConfig(BaseModel):
    searxng_enabled: bool = False
    searxng_url: str = "http://localhost:8080"
    direct_sources_enabled: bool = True
    rss_enabled: bool = True
    sitemap_enabled: bool = True


class UIConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8000
    questions_per_page: int = 20
    quiz_size: int = 25


class AppSettings(BaseSettings):
    """Global application settings."""

    database_url: str = DEFAULT_DB_URL
    research: ResearchConfig = Field(default_factory=ResearchConfig)
    crawler: CrawlerConfig = Field(default_factory=CrawlerConfig)
    quality: QualityConfig = Field(default_factory=QualityConfig)
    verification: VerificationConfig = Field(default_factory=VerificationConfig)
    generation: GenerationConfig = Field(default_factory=GenerationConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    ui: UIConfig = Field(default_factory=UIConfig)


def load_yaml(path: Path) -> dict[str, Any]:
    """Safely load YAML file if exists."""
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_settings() -> AppSettings:
    """Load settings from config/settings.yaml merged with environment overrides."""
    yaml_data = load_yaml(SETTINGS_FILE)
    return AppSettings(**yaml_data)


def get_sources_data() -> list[dict[str, Any]]:
    """Load sources list from config/sources.yaml."""
    data = load_yaml(SOURCES_FILE)
    return data.get("sources", [])


def get_queries_data() -> dict[str, Any]:
    """Load query templates from config/queries.yaml."""
    return load_yaml(QUERIES_FILE)


def get_taxonomy_data() -> dict[str, Any]:
    """Load taxonomy and curriculum mapping from config/taxonomy.yaml."""
    return load_yaml(TAXONOMY_FILE)


def get_rejection_rules_data() -> dict[str, Any]:
    """Load rejection and quarantine rules from config/rejection_rules.yaml."""
    return load_yaml(REJECTION_RULES_FILE)
