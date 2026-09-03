# Installed capability and limitations

The current surface contains fourteen research tools. [Research-only scope](RESEARCH-ONLY-SCOPE.md) supersedes action requirements in the historical v1.5 design.

- Anonymous search and Reddit have upstream rate limits; partial/unavailable results must be disclosed.
- Read-only GitHub token/App support, GitHub-bound fallback cursors, discussion search/threads and exact-ref retrieval have regression coverage. Authenticated public-source adapter canaries passed; connected DSH acceptance remains separate.
- Public caption adapters do not transcribe captionless media.
- Exact local browser HTTP/WebSocket request validation passed real Chrome fixtures. Chromium-level DNS pinning and wider lifecycle/concurrency acceptance remain; do not infer those from a registered tool.
- Cookie-only import passed an actual Chrome encrypted-cookie loopback-login fixture. The owned copy is read by installed Chrome and cookies are transferred in memory to the research context. It is not site-filtered; app-bound cookies and a chosen real-world login remain unproven. No passwords, payment data, extensions, history, bookmarks, settings, or full-profile import.
- OAuth and encrypted research connections remain. Live setup requires the operator's chosen account and scopes.
- Optional CapSolver/Bright Data adapters remain disabled; complete crawl routing and live challenge/proxy acceptance are not proven.
- Research jobs checkpoint completed/remaining sources and cumulative budgets, renew leases, and return bounded pageable status. A disposable native process-crash/restart fixture and a live Gateway MCP pause/resume/budget/evidence-cursor canary passed. DSH job acceptance and broad cancellation stress remain; cancelling an async call cannot forcibly stop DDGS's in-flight synchronous thread. A completed worker may have partial evidence; inspect state, progress, error_code and warnings.
- The latest DSH acceptance run failed before tool dispatch because its host/agent-loop resolved different tools-package scheduler symbols. Gateway source-tool tests are not a substitute for a successful DSH workflow.
- No email, posting, GitHub-write, general form, purchase, account-change, or deletion tools remain. Those are removed scope, not future work.
- A cloud-only client cannot reach workstation loopback merely by installing this skill.
