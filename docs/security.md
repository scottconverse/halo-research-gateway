# Security and authority

Security here is intended to preserve capability, not make research unusable.

## Code invariants

- The server binds only to `127.0.0.1`.
- Public tools accept valid public HTTP(S) destinations on any valid port.
- Public tools reject loopback, private, link-local, multicast, unspecified, and cloud metadata destinations after parsing and DNS resolution; redirects are revalidated.
- Direct HTTP connects to the validated IP while preserving Host/TLS SNI, disables inherited proxies.
- Local/private services use exact named target policies and separate tools; they do not weaken public URL policy.
- Sensitive URLs are not persisted in cache.
- Secrets are DPAPI-encrypted for the current Windows user and represented to models only by connection ID and non-secret scope/status metadata.
- Session-import review accepts only cookie imports, validates stored plan integrity, and retains durable at-most-once receipts. Historical non-research plans are not executable.
- Research jobs are bounded and operator-visible; there are no invisible unbounded background loops.

These invariants do not claim protection from arbitrary code already running as the same Windows user modifying the source or runtime. They remove accidental and quiet unsafe configuration paths.

## Browser boundary

Top-level, frame, ordinary subresource, redirect, and WebSocket destinations are routed through public/local policy before connection. Service workers and downloads are disabled, imported profiles are gateway-owned copies, and the Chromium tree is process-contained. Browser-level address pinning across Chromium's own DNS resolution and every browser-internal request class is not yet proven. That remains a real hardening gap, not a reason to remove Crawl4AI from the useful release.

## Research-only boundary

There are no email, GitHub-write, purchase, general form-submission, posting, account-change, or deletion adapters or model-facing tools. Historical action database tables are retained only to preserve data and support import receipts. This is product scope, not a change to DSH native permissions.

Credential import and paid challenge/proxy capabilities are not prohibited, but are not silently enabled. They require an operator-selected provider/import scope/domain/budget and a tested adapter.
