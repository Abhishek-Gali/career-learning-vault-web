# Web Research & Crawler Rules

- **Robots Policy**: Check and respect `robots.txt` before issuing HTTP requests to discovered candidate URLs.
- **Rate Limiting**: Enforce per-domain async rate limiting (default minimum 1.0–2.0s delay between requests).
- **Timeouts & Size Limits**: Maximum timeout 20s; abort and reject pages larger than 10MB (`ContentTooLargeError`).
- **No Anti-Bot Evasion**: Never attempt to bypass CAPTCHAs, paywalls, or cloudflare challenge screens. If blocked, log and skip.
- **Content-Addressed Cache**: Always check `data/cache/pages/` before performing network requests. Respect `ETag` and `Last-Modified` headers.
