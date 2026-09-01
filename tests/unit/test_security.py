# Gate-authored acceptance tests (frozen). The worker implements src/ to make
# these pass and may not modify this file. Authored by the conductor 2026-08-25.
import pytest

from halo_research_gateway.security import (
    UrlPolicyError,
    classify_ip,
    is_sensitive_url,
    validate_redirect,
    validate_resolved,
    validate_url,
)


def _code(url):
    with pytest.raises(UrlPolicyError) as e:
        validate_url(url)
    return e.value.code


def test_accepts_public_urls():
    t = validate_url("https://example.com/a?b=c")
    assert (t.scheme, t.host, t.port) == ("https", "example.com", 443)
    assert validate_url("http://example.com:80/").port == 80
    assert validate_url("https://example.com:443/x").port == 443
    assert validate_url("https://[2606:4700::1]/").host  # public IPv6 literal is allowed


def test_rejects_bad_scheme():
    assert _code("ftp://x.example.com/") == "UNSAFE_URL/scheme"
    assert _code("file:///c/x") == "UNSAFE_URL/scheme"


def test_rejects_userinfo():
    assert _code("https://u:p@h.example.com/") == "UNSAFE_URL/userinfo"


def test_accepts_all_valid_public_http_ports():
    assert validate_url("https://example.com:8080/").port == 8080
    assert validate_url("http://example.com:65535/").port == 65535


def test_rejects_overlong_url():
    assert _code("https://example.com/" + "a" * 2000) == "UNSAFE_URL/length"


def test_rejects_bad_hosts():
    assert _code("http://localhost/") == "UNSAFE_URL/host"
    assert _code("http://foo.local/") == "UNSAFE_URL/host"
    assert _code("http://intranet/") == "UNSAFE_URL/host"  # single-label name


def test_rejects_nonpublic_ip_literals():
    for url in [
        "http://127.0.0.1/",
        "http://10.1.2.3/",
        "http://169.254.1.1/",
        "http://[::1]/",
        "http://[fe80::1]/",
        "http://[fc00::1]/",
        "http://192.168.0.1/",
        "http://2130706433/",
        "http://0x7f000001/",
        "http://[::ffff:10.0.0.1]/",
    ]:
        assert _code(url) == "UNSAFE_URL/ip", url


def test_classify_ip():
    assert classify_ip("2606:4700::1") is True
    assert classify_ip("93.184.216.34") is True
    for ip in [
        "127.0.0.1",
        "10.0.0.1",
        "169.254.1.1",
        "::1",
        "fe80::1",
        "fc00::1",
        "224.0.0.1",
        "0.0.0.0",
        "::ffff:10.0.0.1",
    ]:
        assert classify_ip(ip) is False, ip


def test_validate_resolved():
    t = validate_url("https://example.com/")
    assert validate_resolved(t, ["93.184.216.34", "2606:4700::1"]) == "93.184.216.34"
    with pytest.raises(UrlPolicyError):
        validate_resolved(t, ["93.184.216.34", "10.0.0.1"])  # ANY non-public answer rejects
    with pytest.raises(UrlPolicyError):
        validate_resolved(t, [])


def test_validate_redirect():
    t = validate_url("https://example.com/start")
    n = validate_redirect(t, "/next")
    assert (n.scheme, n.host) == ("https", "example.com")
    with pytest.raises(UrlPolicyError):
        validate_redirect(t, "http://127.0.0.1/")


def test_is_sensitive_url():
    assert is_sensitive_url("https://example.com/?api_key=x") is True
    assert is_sensitive_url("https://example.com/?q=x") is False
    assert is_sensitive_url("https://u:p@example.com/") is True
    assert is_sensitive_url("https://example.com/?X-Amz-Signature=x") is True
