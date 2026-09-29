"""Shared enums and core types for CLF-C02 Researcher."""

from enum import Enum


class QuestionType(str, Enum):
    """Supported structural question types."""

    SINGLE_CHOICE = "SINGLE_CHOICE"
    MULTIPLE_RESPONSE = "MULTIPLE_RESPONSE"
    TRUE_FALSE = "TRUE_FALSE"
    MATCHING = "MATCHING"
    SCENARIO = "SCENARIO"


class QuestionStatus(str, Enum):
    """Lifecycle states of a question."""

    DISCOVERED = "DISCOVERED"
    FETCHED = "FETCHED"
    EXTRACTED = "EXTRACTED"
    NORMALIZED = "NORMALIZED"
    CLASSIFIED = "CLASSIFIED"
    VERIFIED = "VERIFIED"
    DEDUPLICATED = "DEDUPLICATED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    QUARANTINED = "QUARANTINED"


class SourceKind(str, Enum):
    """Origin category of questions."""

    PUBLIC_PRACTICE = "PUBLIC_PRACTICE"
    GENERATED_PRACTICE = "GENERATED_PRACTICE"
    OFFICIAL_SAMPLE = "OFFICIAL_SAMPLE"
    COMMUNITY = "COMMUNITY"


class DateConfidence(str, Enum):
    """Confidence score in extracted publication or update date."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class DatePolicy(str, Enum):
    """Evaluation policy for dynamic recency."""

    RECENT_PUBLICATION_ONLY = "RECENT_PUBLICATION_ONLY"
    RECENT_UPDATE_ONLY = "RECENT_UPDATE_ONLY"
    RECENT_PUBLICATION_OR_UPDATE = "RECENT_PUBLICATION_OR_UPDATE"
    RECENT_PUBLICATION_OR_SUBSTANTIAL_UPDATE = "RECENT_PUBLICATION_OR_SUBSTANTIAL_UPDATE"
    STRICT_RECENT = "STRICT_RECENT"


class RecentnessStatus(str, Enum):
    """Recency state of a question relative to active 6-month research window."""

    RECENT_PUBLISHED = "RECENT_PUBLISHED"
    RECENT_UPDATED = "RECENT_UPDATED"
    OLDER = "OLDER"
    LEGACY = "LEGACY"
    UNKNOWN_DATE = "UNKNOWN_DATE"


class AnswerStatus(str, Enum):
    """Authoritative answer verification outcome."""

    VERIFIED = "VERIFIED"
    PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    CONFLICTING = "CONFLICTING"
    REJECTED = "REJECTED"


class KnowledgeStatus(str, Enum):
    """State of AWS concept currency."""

    CURRENT = "CURRENT"
    POTENTIALLY_STALE = "POTENTIALLY_STALE"
    OUTDATED = "OUTDATED"
    UNKNOWN = "UNKNOWN"


class SourceTier(str, Enum):
    """Reputation and trust tier for source domains."""

    OFFICIAL = "OFFICIAL"
    ESTABLISHED_EDUCATIONAL = "ESTABLISHED_EDUCATIONAL"
    COMMUNITY_EDUCATIONAL = "COMMUNITY_EDUCATIONAL"
    UNVERIFIED = "UNVERIFIED"
    REJECTED = "REJECTED"


class CandidateStatus(str, Enum):
    """Processing state for search and candidate URLs."""

    NEW = "NEW"
    QUEUED = "QUEUED"
    FETCHED = "FETCHED"
    SKIPPED = "SKIPPED"
    REJECTED = "REJECTED"
    PROCESSED = "PROCESSED"


class LegacyStatus(str, Enum):
    """CLF-C01 vs. CLF-C02 syllabus classification."""

    CLF_C02 = "CLF_C02"
    POSSIBLE_LEGACY = "POSSIBLE_LEGACY"
    LEGACY_CLF_C01 = "LEGACY_CLF_C01"
    CURRENT_BUT_UNCERTAIN = "CURRENT_BUT_UNCERTAIN"


class LicenseStatus(str, Enum):
    """Licensing and copyright attribution status."""

    LICENSE_KNOWN = "LICENSE_KNOWN"
    LICENSE_UNKNOWN = "LICENSE_UNKNOWN"
    REDISTRIBUTION_ALLOWED = "REDISTRIBUTION_ALLOWED"
    PERSONAL_REFERENCE = "PERSONAL_REFERENCE"
    GENERATED = "GENERATED"
    REJECTED = "REJECTED"


class ContentSafetyStatus(str, Enum):
    """Content safety and quarantine assessment."""

    NORMAL = "NORMAL"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    QUARANTINED = "QUARANTINED"
    REJECTED = "REJECTED"


class QuizMode(str, Enum):
    """Interactive quiz session modes."""

    RANDOM = "RANDOM"
    RECENT_SOURCE_ONLY = "RECENT_SOURCE_ONLY"
    GENERATED_ONLY = "GENERATED_ONLY"
    VERIFIED_ONLY = "VERIFIED_ONLY"
    DOMAIN_PRACTICE = "DOMAIN_PRACTICE"
    TASK_PRACTICE = "TASK_PRACTICE"
    SERVICE_PRACTICE = "SERVICE_PRACTICE"
    WEAK_TOPIC = "WEAK_TOPIC"
    REVIEW_INCORRECT = "REVIEW_INCORRECT"
    TIMED = "TIMED"
