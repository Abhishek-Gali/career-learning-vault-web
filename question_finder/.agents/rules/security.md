# Security & Isolation Rules

- **SSRF Defenses**: Validate all discovered candidate URLs before connection. Prohibit loopback (`127.0.0.0/8`), private IPv4 (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), link-local, and cloud metadata (`169.254.169.254`).
- **Scheme Restriction**: Allow only `http` and `https` protocols.
- **Path Traversal Prevention**: Verify all exporter target paths resolve strictly within `data/exports/` and cache paths within `data/cache/`.
- **Zero Secrets**: Never commit or log API keys, access tokens, or private environment parameters.
