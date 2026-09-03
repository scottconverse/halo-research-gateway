"""Public URL validation and sensitive URL handling.

Public tools accept HTTP(S) on every valid TCP port, but only after the whole
resolved address set is proven public. Local/private access is deliberately a
different tool contract and never calls these helpers.
"""

from __future__ import annotations

import re
import urllib.parse
from dataclasses import dataclass
from ipaddress import IPv4Address, IPv6Address, ip_address

UNSAFE_URL = "UNSAFE_URL"
SCHEME = f"{UNSAFE_URL}/scheme"
USERINFO = f"{UNSAFE_URL}/userinfo"
PORT = f"{UNSAFE_URL}/port"
LENGTH = f"{UNSAFE_URL}/length"
HOST = f"{UNSAFE_URL}/host"
IP = f"{UNSAFE_URL}/ip"
DNS = f"{UNSAFE_URL}/dns"

_SENSITIVE_NAME = re.compile(
    r"(?:^|[_-])(token|key|secret|signature|sig|credential|auth|code|session|jwt)(?:$|[_-])",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class ParsedTarget:
    scheme: str
    host: str
    port: int
    path_query: str

    @property
    def origin(self) -> str:
        default = 443 if self.scheme == "https" else 80
        suffix = "" if self.port == default else f":{self.port}"
        return f"{self.scheme}://{self.host}{suffix}"


class UrlPolicyError(ValueError):
    def __init__(self, code: str, message: str = "") -> None:
        self.code = code
        super().__init__(message)


def _parse_ip_literal(host: str):
    """Return an IP for strict literals, rejecting browser-style encodings."""
    try:
        return ip_address(host)
    except ValueError:
        pass
    lowered = host.lower()
    if lowered.startswith("0x") or (host.isdigit() and "." not in host):
        try:
            value = int(host, 16 if lowered.startswith("0x") else 10)
            return ip_address(value)
        except (ValueError, OverflowError):
            raise UrlPolicyError(IP, "Ambiguous numeric IP literal") from None
    if re.fullmatch(r"0[0-7]+", host):
        try:
            return ip_address(int(host, 8))
        except (ValueError, OverflowError):
            raise UrlPolicyError(IP, "Ambiguous numeric IP literal") from None
    return None


def validate_url(url: str) -> ParsedTarget:
    if not isinstance(url, str) or not url or len(url) > 2000:
        raise UrlPolicyError(LENGTH, "URL is empty or exceeds 2,000 characters")
    try:
        parsed = urllib.parse.urlsplit(url)
        port = parsed.port
    except ValueError as exc:
        raise UrlPolicyError(PORT, "Invalid TCP port") from exc
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"}:
        raise UrlPolicyError(SCHEME, "Only HTTP and HTTPS are supported")
    if parsed.username is not None or parsed.password is not None:
        raise UrlPolicyError(USERINFO, "Embedded credentials are forbidden")
    host = (parsed.hostname or "").rstrip(".").lower()
    if not host:
        raise UrlPolicyError(HOST, "URL has no hostname")
    if host == "localhost" or host.endswith(".localhost") or host.endswith(".local"):
        raise UrlPolicyError(HOST, "Local hostname is not public")
    literal = _parse_ip_literal(host)
    if literal is not None:
        if not classify_ip(literal):
            raise UrlPolicyError(IP, "IP address is not public")
    elif "." not in host:
        raise UrlPolicyError(HOST, "Single-label hostname is not public")
    effective_port = port if port is not None else (443 if scheme == "https" else 80)
    if not 1 <= effective_port <= 65535:
        raise UrlPolicyError(PORT, "TCP port must be 1..65535")
    path = parsed.path or "/"
    path_query = urllib.parse.urlunsplit(("", "", path, parsed.query, ""))
    return ParsedTarget(scheme, host, effective_port, path_query)


def classify_ip(value: object) -> bool:
    """Return True only for globally routable unicast addresses."""
    try:
        addr = value if isinstance(value, (IPv4Address, IPv6Address)) else ip_address(value)
    except ValueError:
        return False
    if isinstance(addr, IPv6Address) and addr.ipv4_mapped is not None:
        return classify_ip(addr.ipv4_mapped)
    return bool(addr.is_global and not addr.is_multicast)


def validate_resolved(target: ParsedTarget, addresses: list[str] | tuple[str, ...]) -> str:
    """Reject the complete DNS answer when *any* address is not public."""
    del target
    if not addresses:
        raise UrlPolicyError(DNS, "DNS returned no addresses")
    normalized: list[str] = []
    for value in addresses:
        try:
            addr = ip_address(value)
        except ValueError as exc:
            raise UrlPolicyError(DNS, "DNS returned an invalid address") from exc
        if not classify_ip(addr):
            raise UrlPolicyError(DNS, "DNS answer contains a non-public address")
        normalized.append(str(addr))
    return normalized[0]


def validate_redirect(current: ParsedTarget, location: str) -> ParsedTarget:
    return validate_url(urllib.parse.urljoin(current.origin + current.path_query, location))


def is_sensitive_url(url: str) -> bool:
    try:
        parsed = urllib.parse.urlsplit(url)
    except ValueError:
        return True
    if parsed.username is not None or parsed.password is not None:
        return True
    return any(_SENSITIVE_NAME.search(name) for name, _ in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True))


def redact_url(url: str) -> str:
    """Remove userinfo, fragment, and every query value before logging."""
    try:
        parsed = urllib.parse.urlsplit(url)
        host = parsed.hostname or ""
        if ":" in host:
            host = f"[{host}]"
        port = f":{parsed.port}" if parsed.port else ""
        query = urllib.parse.urlencode(
            [(name, "[REDACTED]") for name, _ in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)]
        )
        return urllib.parse.urlunsplit((parsed.scheme, host + port, parsed.path, query, ""))
    except (ValueError, TypeError):
        return "[REDACTED_URL]"
