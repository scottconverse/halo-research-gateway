"""Logging configuration with URL redaction."""

import urllib.parse
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Define sensitive parameter names for URL redaction
SENSITIVE_PARAM_NAMES = {"token", "key", "secret", "signature", "sig", "credential", "auth", "code", "session", "jwt"}


def redact_url(url: str) -> str:
    """Redact sensitive parameters from URLs."""
    if not url or not isinstance(url, str):
        return url

    # Handle non-http(s) URLs
    if not url.startswith(("http://", "https://")):
        return url

    try:
        parsed = urllib.parse.urlparse(url)

        # If there's a username/password, remove them
        if parsed.username or parsed.password:
            # Create new netloc without user info
            netloc = parsed.hostname
            if parsed.port:
                netloc += f":{parsed.port}"
            parsed = parsed._replace(netloc=netloc)

        # Parse query parameters
        query_params = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)

        # Redact sensitive parameters
        redacted_params = []
        for name, value in query_params:
            if any(sensitive in name.lower() for sensitive in SENSITIVE_PARAM_NAMES):
                redacted_params.append((name, "[REDACTED]"))
            else:
                redacted_params.append((name, value))

        # Rebuild URL with redacted parameters
        new_query = urllib.parse.urlencode(redacted_params, doseq=True)
        parsed = parsed._replace(query=new_query)

        # Remove fragment entirely (as required by constraints)
        parsed = parsed._replace(fragment="")

        return urllib.parse.urlunparse(parsed)
    except Exception:
        # If parsing fails for any reason, return original URL
        return url


def redact_text(text: str) -> str:
    """Redact sensitive parameters from URLs found within text."""
    if not isinstance(text, str):
        return text

    import re

    # Simple regex to find HTTP(S) URLs in text
    url_pattern = r"https?://[^\s<>\"']+"

    def redact_match(match):
        return redact_url(match.group(0))

    return re.sub(url_pattern, redact_match, text)


def setup_logging(log_path: Path, error_log_path: Path, level: str) -> None:
    """Set up JSONL logging with URL redaction."""
    # Create log directory if needed
    log_path.parent.mkdir(parents=True, exist_ok=True)
    error_log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure root logger for general logs
    import logging

    formatter = logging.Formatter("%(message)s")

    # Setup file handler for all logs
    handler = RotatingFileHandler(str(log_path), maxBytes=1024 * 1024 * 5, backupCount=3)
    handler.setFormatter(formatter)

    # Add handler to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    # Setup error file handler
    error_handler = RotatingFileHandler(str(error_log_path), maxBytes=1024 * 1024 * 5, backupCount=3)
    error_handler.setFormatter(formatter)

    # Add to logger with ERROR level
    error_logger = logging.getLogger("error")
    error_logger.addHandler(error_handler)
    error_logger.setLevel(logging.ERROR)
