# Research-only landing-page correction — 2026-09-02

The earlier removal left misleading hero copy, an obsolete 16-tool count, old test counts, generic operation/approval wording and an apparent successful DSH acceptance claim. These were found in the actual page source and corrected before publication. The page now says find/read/compare/cite, states that email/posting/purchasing/account operations are absent, labels the workflow illustration as an example, distinguishes fixture/source evidence from full DSH acceptance, and names the current DSH and login/provider/install gaps. No new product feature or website dependency was added; existing design, social image and owner-only access are retained.

Read before editing: website/app/page.tsx, layout.tsx, package.json, hosting manifest, ignore file and build configuration. Copy-only changes are exempt from logic TDD. Existing build dependencies were reused.

`npm run build` from website:

```text
> halo-research-gateway-site@0.2.0 build
> vinext build

  vinext build  (Vite 8.2.2)
[1/5] analyze client references...
transforming...
✓ 269 modules transformed.
rendering chunks...
✓ built in 1.20s
[2/5] analyze server references...
transforming...
✓ 115 modules transformed.
rendering chunks...
✓ built in 153ms
[3/5] build rsc environment...
transforming...
✓ 261 modules transformed.
rendering chunks...
computing gzip size...
✓ built in 565ms
[4/5] build client environment...
transforming...
✓ 134 modules transformed.
rendering chunks...
computing gzip size...
✓ built in 455ms
[5/5] build ssr environment...
transforming...
✓ 96 modules transformed.
rendering chunks...
computing gzip size...
✓ built in 336ms

  Route (app)
  ─ ? /

  ? Unknown

  ? Some routes could not be classified. vinext currently uses static analysis
    and cannot detect dynamic API usage (headers(), cookies(), etc.) at build time.
    Automatic classification will be improved in a future release.

  Build complete. Run `vinext start` to start the production server.
```

`npm run lint`:

```text
> halo-research-gateway-site@0.2.0 lint
> oxlint app components/ui/button.tsx lib
```

Both commands exited 0. The existing Vinext route-classification warning remains visible above, not treated as proof of rendering correctness. A non-browser `Invoke-WebRequest -Uri http://localhost:3000/ -TimeoutSec 20 | Select-Object StatusCode` returned 200 after `npm run dev`. No browser visual/interaction QA is claimed; the preview open was queued because this task was not foreground.

Sites access was verified as owner-only: current_user_role owner, custom policy, one allowed account, zero external visitors and no workspace/tenant groups. Source credentials and runtime tokens are not recorded here. Build success is not publication success; deployment must be separately verified through Sites before claiming the hosted copy changed.

## Publication verified

Sites returned status `succeeded` at 2026-09-02T23:50:51.513034+00:00 for the existing [owner-only site](https://halo-research-gateway.sconverse.chatgpt.site). Access was rechecked immediately before private deployment and left unchanged.

- Site project: `appgprj_6a9691bac0fc819181ccdad8daae4ed4`.
- Saved Sites version: 3, ID `appgprj_6a9691bac0fc819181ccdad8daae4ed4~appgver_256994e13cfc8191996629c1597dd8c4`.
- Deployment: `appgdep_6a98b63dfea8819182b19d1e0517689d`.
- Dedicated Site source main: `519def36ff18bcd883d12db8bc2d26285eb155e3`, verified against the remote branch after successful push. This is a Site-source SHA, not the Gateway repository SHA.
- Gateway source containing the corrected website: `eb5ca02a8936bae1c1c71749104eda92027f7b6a`.
- All 77 selected website source files were copied byte-for-byte into the dedicated Site checkout and hash-checked. Only that Site source was pushed to its publishing repository.
- Local compressed archive SHA-256: `9049948534380e8fcdb6da009c535cf97c4c7375a99610cdf659ae7377cbc443`.
- Sites-reported archive content hash: `sha256:b4eae2816cc0041e28f0e7a5da611e209d8eacce9b046f857bf079b61311f056`; 71 packaged files, 2,775,040 bytes. This content hash is distinct from the compressed local archive hash.

The provided packaging helper initially failed because GNU tar interpreted a Windows drive-colon archive path as remote syntax:

```text
tar (child): Cannot connect to C: resolve failed
tar: C\:/Users/scott/Documents/Codex/2026-09-01/is-this-tool-plugin-real-https/outputs/halo-research-site-corrected.tar.gz: Cannot write: Broken pipe
tar: Child returned status 128
tar: Error is not recoverable: exiting now
Exception: Site packaging failed.
```

Rerunning the same helper with Git Bash `/c/Users/...` paths completed successfully; no WSL was used and no deployment was attempted with the failed archive. The archive was saved only after both source push and packaging succeeded. No source credential was stored in a file, Git remote URL or Git config.

The existing development server also emitted these warnings during the HTTP preview checks:

```text
5:43:55 PM [vite] (rsc) warning: client component dependency is inconsistently optimized. It's recommended to add the dependency to 'optimizeDeps.exclude'.
  Plugin: rsc:use-client
  File: C:/Users/scott/Desktop/Code/halo-research-gateway/website/node_modules/lucide-react/dist/esm/Icon.mjs?v=b4f745bc
5:43:56 PM [vite] (rsc) warning: client component dependency is inconsistently optimized. It's recommended to add the dependency to 'optimizeDeps.exclude'.
  Plugin: rsc:use-client
  File: C:/Users/scott/Desktop/Code/halo-research-gateway/website/node_modules/@base-ui/react/button/Button.mjs?v=b4f745bc
```

These are not suppressed or represented as clean browser-console evidence. The preview session was stopped after publication. This task was not foreground, so its queued preview opening is not proof that the user saw it; the deployed URL is the handoff. No screenshots, DOM or interaction QA are claimed. Sites publication does not prove the separate localhost Gateway/DSH integration.
