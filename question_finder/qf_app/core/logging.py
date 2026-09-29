"""Structured application logging setup."""

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from qf_app.core.paths import LOGS_DIR


class JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "run_id"):
            log_obj["run_id"] = record.run_id
        if hasattr(record, "stage"):
            log_obj["stage"] = record.stage
        if hasattr(record, "url"):
            log_obj["url"] = record.url
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def setup_logging(level: str = "INFO") -> None:
    """Configure root logger with console stream and JSON file output."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / "app.log"

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers
    for handler in list(root.handlers):
        root.removeHandler(handler)

    # Console Handler (Human-readable)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(
        logging.Formatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s", datefmt="%H:%M:%S")
    )
    root.addHandler(console_handler)

    # File Handler (Structured JSON)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(JSONFormatter())
    root.addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """Retrieve logger instance with given name."""
    return logging.getLogger(name)
