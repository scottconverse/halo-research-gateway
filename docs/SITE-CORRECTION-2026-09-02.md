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
