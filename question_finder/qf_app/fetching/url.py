"""URL canonicalization and SSRF security validation."""

import ipaddress
import socket
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from qf_app.core.exceptions import SSRFError

TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "fbclid",
    "gclid",
    "_ga",
    "_gl",
    "ref",
}


def normalize_url(raw_url: str) -> str:
    """Normalize URL by lowercasing host, removing tracking params, and stripping fragments."""
    try:
        parsed = urlparse(raw_url.strip())
        scheme = parsed.scheme.lower() or "https"
        netloc = parsed.netloc.lower()
        path = parsed.path or "/"

        # Normalize trailing slashes on root path
        if path != "/" and path.endswith("/"):
            path = path.rstrip("/")

        # Filter tracking query parameters
        filtered_query = []
        if parsed.query:
            for k, v in parse_qsl(parsed.query, keep_blank_values=True):
                if k.lower() not in TRACKING_PARAMS:
                    filtered_query.append((k, v))
        query_str = urlencode(filtered_query)

        # Drop fragment
        return urlunparse((scheme, netloc, path, parsed.params, query_str, ""))
    except Exception:
        return raw_url.strip()


def validate_url_security(url: str) -> None:
    """Validate URL against SSRF, internal IPs, private networks, and invalid schemes."""
    parsed = urlparse(url)
    scheme = parsed.scheme.lower()
    if scheme not in ("http", "https"):
        raise SSRFError(f"Prohibited URL scheme: {scheme}")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFError("Missing hostname in candidate URL")

    # Reject localhost names
    if hostname.lower() in ("localhost", "127.0.0.1", "::1", "0.0.0.0", "metadata.google.internal"):
        raise SSRFError(f"Prohibited destination host: {hostname}")

    # Check for direct IP addresses
    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
            raise SSRFError(f"Target IP is private or restricted: {ip}")
    except ValueError:
        # Hostname is a domain name, not an IP literal
        pass
