# Installed capability and limitations

The current surface contains fourteen research tools. [Research-only scope](RESEARCH-ONLY-SCOPE.md) supersedes action requirements in the historical v1.5 design.

- Anonymous search and Reddit have upstream rate limits; partial/unavailable results must be disclosed.
- Read-only GitHub App support exists, but live credentials, cursor behavior, discussions, and non-default-ref coverage require validation.
- Public caption adapters do not transcribe captionless media.
- Browser request/WebSocket validation and Chromium DNS behavior still need the remaining fixes and live acceptance; do not infer safety from a registered tool.
- Cookie-only research-session import is supported. It is not site-filtered and is not yet proof that a real imported login works with current Chrome encryption. No passwords, payment data, extensions, history, bookmarks, settings, or full-profile import.
- OAuth and encrypted research connections remain. Live setup requires the operator's chosen account and scopes.
- Optional CapSolver/Bright Data adapters remain disabled; complete crawl routing and live challenge/proxy acceptance are not proven.
- No email, posting, GitHub-write, general form, purchase, account-change, or deletion tools remain. Those are removed scope, not future work.
- A cloud-only client cannot reach workstation loopback merely by installing this skill.
