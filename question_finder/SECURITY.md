# SECURITY.md — Security, SSRF Protection & Resource Limits

## 1. Secrets & Credentials Management
- Zero hardcoded API keys, tokens, or credentials are permitted in the codebase.
- Optional external endpoints (e.g., local SearXNG URL) are loaded via environment variables or `config/settings.yaml`.
- Default behavior operates completely offline/locally without requiring API tokens.

## 2. SSRF (Server-Side Request Forgery) Protections
To protect local and private networks when crawling arbitrary discovered URLs:
- **Allowed Schemes**: Only `http` and `https` protocols are permitted. `file://`, `ftp://`, `gopher://`, `dict://`, and cloud metadata URLs (`http://169.254.169.254/`) are strictly blocked.
- **Private IP Blocking**: Resolving hostnames to loopback addresses (`127.0.0.0/8`, `::1`), link-local (`169.254.0.0/16`, `fe80::/10`), RFC 1918 private networks (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), and carrier-grade NAT blocks (`100.64.0.0/10`) will raise `SSRFError` and abort the fetch.
- **Redirect Limits**: Maximum 5 sequential HTTP redirects allowed to prevent redirect loops and rebinding exploits.

## 3. Crawler Resource & Denial-of-Service Defenses
- **Maximum Request Timeout**: Default 20 seconds per request.
- **Maximum Response Size**: Default 10 megabytes per page (`10 * 1024 * 1024` bytes). Downloads exceeding this threshold immediately abort with `ContentTooLargeError`.
- **Concurrency Bounds**: Async HTTP client semaphore restricts concurrent outbound connections to 8 simultaneous requests.
- **Per-Domain Rate Limiting**: Minimum 1.0–2.0 second delay between consecutive requests to the same origin domain.

## 4. Fetched Content Isolation & Sandboxing
- HTML parsing uses lxml / BeautifulSoup with script/iframe execution completely disabled.
- Optional browser automation (Playwright) runs in headless, isolated browser contexts with JavaScript execution sandboxed and access to local storage / system files forbidden.

## 5. Local Data Storage & Filesystem Containment
- All runtime databases, caches, logs, and downloaded browser binaries reside strictly within `e:\Anti Gravity (Projects)\question finder\`.
- Path traversal vulnerabilities in file exporters and caching modules are prevented using strict `pathlib.Path.resolve()` checks verifying that paths stay within the `data/` directory.
