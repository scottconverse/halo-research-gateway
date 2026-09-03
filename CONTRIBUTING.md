# Contributing

Halo Research Gateway is a Windows-only, research-only product. DSH is the first
client, but core changes must remain agent/model-neutral standard MCP.

## Development

1. Use Windows 11, PowerShell, Node.js 22 and the locked Python 3.12 `uv` environment.
2. Work on a scoped branch. Preserve unrelated local changes.
3. Add a failing test before changing behavior, then make the smallest repair.
4. Run `./scripts/Invoke-QualityGate.ps1 -Scope Full`.
5. Run `npm ci`, `npm run lint`, and `npm run build` in `website` when its source
   or release-facing documentation changes.

Do not add email, GitHub writes, shopping, general form submission, account
operation, or broad personal-data migration. Research connections exist only to
read evidence.

## Delivery

- Commit locally and push each completed green slice.
- Before merge, align README, user manual, landing-page source, changelog,
  release notes, package metadata and manifest.
- Merge only after the exact pushed revision has green CI.
- Create a release tag only after explicit owner approval.
- Keep source, installed-runtime and live-client evidence distinct.
