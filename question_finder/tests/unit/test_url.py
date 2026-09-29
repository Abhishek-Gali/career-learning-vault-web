"""Unit tests for URL normalization and SSRF validation."""

import pytest
from qf_app.core.exceptions import SSRFError
from qf_app.fetching.url import normalize_url, validate_url_security


def test_normalize_url_strips_tracking():
    raw = "https://EXAMPLE.com/practice/clf-c02/?utm_source=twitter&utm_medium=cpc&id=123#q1"
    normalized = normalize_url(raw)
    assert normalized == "https://example.com/practice/clf-c02?id=123"


def test_validate_url_security_allowed():
    validate_url_security("https://aws.amazon.com/certification/")
    validate_url_security("http://tutorialsdojo.com/free-clf-c02/")


def test_validate_url_security_blocks_private_and_local():
    with pytest.raises(SSRFError):
        validate_url_security("http://localhost:8000/internal")

    with pytest.raises(SSRFError):
        validate_url_security("http://127.0.0.1:8080/metrics")

    with pytest.raises(SSRFError):
        validate_url_security("http://169.254.169.254/latest/meta-data/")

    with pytest.raises(SSRFError):
        validate_url_security("http://192.168.1.1/admin")

    with pytest.raises(SSRFError):
        validate_url_security("file:///etc/passwd")
