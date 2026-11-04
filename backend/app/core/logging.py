"""Structured logging configuration for CivicShield NG."""

import logging
import sys
import json
from datetime import datetime, timezone
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured application and security logging."""

    SENSITIVE_KEYS = {"password", "token", "secret", "authorization", "mfa_secret", "key"}

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }

        # Include custom extra attributes if present
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            sanitized = self._mask_sensitive(record.extra_data)
            log_entry["data"] = sanitized

        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)

    def _mask_sensitive(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively mask sensitive values in logs."""
        masked: Dict[str, Any] = {}
        for k, v in data.items():
            if any(sens in k.lower() for sens in self.SENSITIVE_KEYS):
                masked[k] = "***REDACTED***"
            elif isinstance(v, dict):
                masked[k] = self._mask_sensitive(v)
            else:
                masked[k] = v
        return masked


def setup_logging(level: str = "INFO", json_format: bool = False) -> logging.Logger:
    """Configure root and application logger."""
    logger = logging.getLogger("civicshield")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers to prevent duplicate output
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    if json_format:
        handler.setFormatter(JSONFormatter())
    else:
        standard_format = (
            "[%(asctime)s] [%(levelname)s] [%(name)s:%(module)s:%(lineno)d] - %(message)s"
        )
        handler.setFormatter(logging.Formatter(standard_format, datefmt="%Y-%m-%d %H:%M:%S"))

    logger.addHandler(handler)
    logger.propagate = False
    return logger


logger = setup_logging()
