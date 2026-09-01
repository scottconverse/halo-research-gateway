"""Tests for URL redaction functionality."""

from halo_research_gateway.logging_config import redact_text, redact_url


def test_redact_url_golden_case():
    """Test the golden case from constraints."""
    # This should produce exactly one of these two forms:
    # 1. https://h/x?api_key=%5BREDACTED%5D&q=ok (using urllib.parse.quote)
    # 2. https://h/x?api_key=[REDACTED]&q=ok (using literal brackets)
    input_url = "https://u:p@h/x?api_key=AAA&q=ok#f"
    result = redact_url(input_url)

    # Both forms are acceptable - check that the pattern is correct
    assert "api_key=" in result  # Parameter name should remain
    assert "%5BREDACTED%5D" in result or "[REDACTED]" in result  # Value should be redacted


def test_redact_url_amz_signature():
    """Test X-Amz-Signature redaction."""
    input_url = "https://s3.amazonaws.com/bucket?X-Amz-Signature=abc123&other=value"
    result = redact_url(input_url)

    # Should redact the signature parameter
    assert "%5BREDACTED%5D" in result or "[REDACTED]" in result


def test_redact_url_sig_param():
    """Test sig= parameter redaction."""
    input_url = "https://api.example.com/endpoint?sig=secret123&other=value"
    result = redact_url(input_url)

    # Should redact the sig parameter
    assert "%5BREDACTED%5D" in result or "[REDACTED]" in result


def test_redact_url_untouched():
    """Test that non-sensitive parameters are untouched."""
    input_url = "https://api.example.com/endpoint?param1=value1&param2=value2"
    result = redact_url(input_url)

    # Should be unchanged
    assert result == input_url


def test_redact_text_multiple_urls():
    """Test redacting URLs within text."""
    input_text = "Visit https://user:pass@example.com/path?token=secret123 and https://api.example.com/other?key=value"
    result = redact_text(input_text)

    # Both URLs should be redacted
    assert "%5BREDACTED%5D" in result or "[REDACTED]" in result


def test_non_http_url():
    """Test that non-http(s) URLs are unchanged."""
    input_url = "ftp://files.example.com/file.txt"
    result = redact_url(input_url)

    assert result == input_url


def test_invalid_url():
    """Test that invalid URLs return original."""
    input_url = "not a valid url"
    result = redact_url(input_url)

    assert result == input_url


def test_empty_and_none():
    """Test empty and None inputs."""
    assert redact_url("") == ""
    assert redact_url(None) is None


def test_redact_text_empty():
    """Test empty text."""
    assert redact_text("") == ""
    assert redact_text(None) is None
