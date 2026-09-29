"""Structured exceptions for the CLF-C02 Researcher application."""


class CLFResearcherError(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class FetchError(CLFResearcherError):
    """Raised when an HTTP or network fetch operation fails."""


class RobotsDeniedError(FetchError):
    """Raised when a candidate URL is blocked by robots.txt policy."""


class RateLimitError(FetchError):
    """Raised when request rate limit is exceeded."""


class ContentTooLargeError(FetchError):
    """Raised when a fetched response exceeds the maximum size limit."""


class SSRFError(CLFResearcherError):
    """Raised when a candidate URL targets a private/forbidden network address."""


class ParseError(CLFResearcherError):
    """Raised when parsing HTML, PDF, or XML content fails."""


class MetadataError(CLFResearcherError):
    """Raised when extracting page metadata fails."""


class DateResolutionError(CLFResearcherError):
    """Raised when date parsing and validation fails."""


class QuestionExtractionError(CLFResearcherError):
    """Raised when extracting question structure from page content fails."""


class ClassificationError(CLFResearcherError):
    """Raised when mapping a question to curriculum domains/tasks fails."""


class VerificationError(CLFResearcherError):
    """Raised when answer verification encounters an error."""


class DeduplicationError(CLFResearcherError):
    """Raised when duplicate clustering fails."""


class PersistenceError(CLFResearcherError):
    """Raised when persisting records to the database fails."""


class ConfigurationError(CLFResearcherError):
    """Raised when configuration loading or validation fails."""
