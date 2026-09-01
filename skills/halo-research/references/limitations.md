# Installed capability and limitations

The service exposes the complete sixteen-tool semantic surface, but adapter depth varies.

Currently operational and tested locally: anonymous search with fallback, DNS-pinned direct fetch, Crawl4AI rendering, Reddit RSS search/thread, PDF extraction, signed pagination, shared cache/singleflight, bounded durable jobs, exact configured local targets, encrypted generic connections, prepared actions, and approved generic form submission.

Important limitations:

- Anonymous upstream search and Reddit remain externally rate limited.
- GitHub research currently uses public web discovery rather than an authenticated GitHub API adapter.
- Transcript retrieval may report `TRANSCRIPT_UNAVAILABLE`; site-specific caption adapters are not universal.
- Browser modes do not guarantee bypass of every challenge. Operator-assisted managed-profile use is preferred when a challenge requires a human.
- Browser subresource interception and complete service-worker/WebSocket hardening remain defense-in-depth work; top-level public URL policy is enforced.
- Generic OAuth PKCE, refresh, Chrome selected/full-profile import, paid CAPTCHA, proxy adapters, and site-specific posting/messaging/purchase/account/delete adapters require operator-selected providers and additional implementation before use.
- Only generic form submission has an execution adapter. Other prepared action types fail closed with `ACTION_ADAPTER_NOT_CONFIGURED`.
- The operator must explicitly configure local targets and connections. The gateway does not discover or grant itself private-network or credential authority.
- Installing this skill in a cloud runtime does not make the workstation localhost endpoint reachable.

For implementation requirements, evidence gates, and the intended completed architecture, read the complete v1.5 specification bundled beside this file.
