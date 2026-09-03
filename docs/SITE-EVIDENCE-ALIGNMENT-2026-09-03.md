# Landing-page evidence alignment - 2026-09-03

The existing owner-only landing page is published with the verified Gateway
checkpoint and its remaining limits. This is documentation work, not a change
to research tools, accounts, permissions, providers or DSH.

## What changed

Replaced the stale 176-test claim with the same 423-test suite passed locally
and in Windows CI for Gateway runtime checkpoint
`7cdfe72b5ac7f6d7e1d1c6fc08187830f123982a`. Added a direct exact-run CI link and
a commit-pinned research-only finish list. The first viewport now explicitly
states that the DSH workflow is blocked before dispatch and is not a completed
end-to-end release.

The proof list distinguishes installed Gateway checks, real public-source MCP,
disposable authenticated GitHub MCP, native browser/document/job/cache fixtures,
and fake-vendor challenge routing. It no longer says all crawl routing is
unverified, and it does not claim a live paid call or universal challenge bypass.
It discloses unverified vendor final redirects, estimated rather than invoiced
budgets, and compressed-payload rather than whole-disk/RAM cache limits.
Real login, human handoff, CapSolver token application and broad reliability/
installation work remain open. No removed account-operation feature returned.

Existing theme, architecture diagram, fourteen-tool inventory, social image,
metadata, package manager, lockfile, dependencies and owner-only access remain.
Only page copy/content links changed in website/app/page.tsx.

## Publication identity

- URL: https://halo-research-gateway.sconverse.chatgpt.site
- Site project: `appgprj_6a9691bac0fc819181ccdad8daae4ed4`.
- Saved Sites version: 4, ID `appgprj_6a9691bac0fc819181ccdad8daae4ed4~appgver_244ab10fea808191b7b8b2cdb300bc59`.
- Dedicated Site source SHA: `b7bd4ff7c2c0a29d5f3ebcc0358c590abcf49894`, verified against
  its remote main after a successful push. This is not the Gateway repository SHA.
- Deployment: `appgdep_6a990ff5dec881919f3b22751d4881cd`, status `succeeded` at
  `2026-09-03T06:13:20.213800+00:00`.
- Local archive SHA-256: `DC19C615D4CBC2830AEE1E1E1950AA7D8A6582CA2CA06B0DBE3E60437FBAA07D`.
- Sites archive content hash: `sha256:a04d3f5cee9086dea1e38952ed0a0a64409316de44407068d3255c2b5a4d5134`;
  71 packaged files, 2775040 bytes. This is not the compressed-file hash.
- All 77 selected website source files matched the dedicated Site checkout byte
  for byte before its commit. Archive came from the successful build of that
  same source. Existing social-image SHA-256:
  `BD36F821F836CC2CA6F22C0B2E1864A386AAEC748D77ACB08D5FF05D58CF4EDC`.

Access was rechecked immediately before deployment: owner role, custom policy,
one allowed account, zero external visitors and no workspace/tenant groups.
Access revision stays 1. Credentials were short-lived, used only in a per-command
Git HTTP header, and were not put in Git configuration, source or this record.

## Verification scope and limitations

Read before editing: Sites building/hosting skills and required environment/
library/packaging references, repo AGENTS, website page/layout/theme/button,
package/lock/hosting/ignore/build configuration, prior publication record and
current Gateway evidence. This is copy-only work: logic TDD/baseline is exempt.
No dependency installation or new library was needed.

The existing development preview compiled and returned HTTP 200. The final
production build and lint exited zero. Native Sites verified the deployment;
build success alone was not treated as publication success. No screenshots,
DOM inspection, browser interaction or responsive visual QA was requested or
performed. Existing route-classification and optimized-dependency warnings are
retained below, not described as clean console evidence.

The same existing site tab was used for preview and publication handoff.
Both open requests were queued because this task was not foreground; this is
not proof that Scott saw the page. The retained preview process was deliberately
stopped with Ctrl+C after successful publication (exit 1 is interruption, not
a failed production build). No unrelated server was stopped.
A listener still present on port 3000 belonged to a pre-existing Node server
created at 2026-09-02T21:11:26.795186-06:00, before this preview. Its command
was `.output/server/index.mjs`, not the newly launched Vinext command. It and
its descendants were left untouched; no claim that port 3000 is free is made.

Whole selected Site source credential-pattern scan: 77 files, zero matches.
Ignore rules cover local env, build, dependencies and Wrangler state. Existing
private repository licensing/contributing/package-release work remains separate.
No new endpoint, data input, unsafe rendering/eval, runtime secret, dependency
or authentication behavior was introduced. This does not grant public access.

Initial read-only lookup attempted nonexistent cwd .openai and website README
paths before using the actual website manifest; no changes arose from those
lookup errors. Source/build evidence and final service status remain distinct.

## Exact validation output

### Development server startup

Command:

```powershell
npm run dev -- --host 127.0.0.1
```

Output:

```text

> halo-research-gateway-site@0.2.0 dev
> vinext dev --host 127.0.0.1


  vinext dev  (Vite 8.2.2)

Sites local sign-in: seedy@sites.test
  ➜  Local:   http://localhost:3000/
  ➜  Debug:   http://localhost:3000/__debug
12:07:09 AM [vite] (rsc) warning: client component dependency is inconsistently optimized. It's recommended to add the dependency to 'optimizeDeps.exclude'.
  Plugin: rsc:use-client
  File: C:/Users/scott/Desktop/Code/halo-research-gateway/website/node_modules/lucide-react/dist/esm/Icon.mjs?v=b4f745bc
12:07:09 AM [vite] (rsc) warning: client component dependency is inconsistently optimized. It's recommended to add the dependency to 'optimizeDeps.exclude'.
  Plugin: rsc:use-client
  File: C:/Users/scott/Desktop/Code/halo-research-gateway/website/node_modules/@base-ui/react/button/Button.mjs?v=b4f745bc
 GET / 200 in 1.7s (compile: 1788415611.8s, render: 1.3s)
```

Retained development process at this stage.

### Non-browser HTTP preview

Command:

```powershell
Invoke-WebRequest -Uri http://localhost:3000/ -TimeoutSec 20 | Select-Object StatusCode
```

Output:

```text

StatusCode
----------
       200
```

Exit code: 0.

### Production build and lint

Command:

```powershell
npm run build
if ($LASTEXITCODE) { throw 'Site build failed' }
npm run lint
if ($LASTEXITCODE) { throw 'Site lint failed' }
```

Output:

```text

> halo-research-gateway-site@0.2.0 build
> vinext build


  vinext build  (Vite 8.2.2)

[1/5] analyze client references...
transforming...
✓ 269 modules transformed.
rendering chunks...
✓ built in 722ms
[2/5] analyze server references...
transforming...
✓ 115 modules transformed.
rendering chunks...
✓ built in 125ms
[3/5] build rsc environment...
transforming...
✓ 261 modules transformed.
rendering chunks...
computing gzip size...
✓ built in 645ms
[4/5] build client environment...
transforming...
✓ 134 modules transformed.
rendering chunks...
computing gzip size...
✓ built in 456ms
[5/5] build ssr environment...
transforming...
✓ 96 modules transformed.
rendering chunks...
computing gzip size...
✓ built in 387ms
[0m
  Route (app)
  ─ ? /

  ? Unknown

  ? Some routes could not be classified. vinext currently uses static analysis
    and cannot detect dynamic API usage (headers(), cookies(), etc.) at build time.
    Automatic classification will be improved in a future release.

  Build complete. Run `vinext start` to start the production server.


> halo-research-gateway-site@0.2.0 lint
> oxlint app components/ui/button.tsx lib
```

Exit code: 0.

### Source copy and credential-pattern audit

Command:

```powershell
$ErrorActionPreference='Stop'
$taskRepo='C:\Users\scott\Desktop\Code\halo-research-gateway'
$taskSite='C:\Users\scott\Documents\Codex\2026-09-01\is-this-tool-plugin-real-https\work\site-publication'
if(@(git -c safe.directory=C:/Users/scott/Documents/Codex/2026-09-01/is-this-tool-plugin-real-https/work/site-publication -C $taskSite status --porcelain).Count){throw 'Publishing checkout has other changes; no overwrite.'}
$taskSourcePaths=@(git -c safe.directory=C:/Users/scott/Desktop/Code/halo-research-gateway -C $taskRepo ls-files website)
$taskPublishedPaths=@(git -c safe.directory=C:/Users/scott/Documents/Codex/2026-09-01/is-this-tool-plugin-real-https/work/site-publication -C $taskSite ls-files)
if(@(Compare-Object @($taskSourcePaths | ForEach-Object {$_.Substring(8)}) $taskPublishedPaths).Count){throw 'Publishing source inventories differ; no overwrite.'}
foreach($taskPath in $taskSourcePaths){$taskRelative=$taskPath.Substring(8);$taskSource=Join-Path $taskRepo $taskPath;$taskDestination=Join-Path $taskSite $taskRelative; Copy-Item -LiteralPath $taskSource -Destination $taskDestination; if((Get-FileHash -LiteralPath $taskSource).Hash -ne (Get-FileHash -LiteralPath $taskDestination).Hash){throw "Site source mismatch: $taskRelative"}}
[pscustomobject]@{source_files=$taskSourcePaths.Count;source_copy_hash_mismatches=0} | ConvertTo-Json -Compress
git -c safe.directory=C:/Users/scott/Documents/Codex/2026-09-01/is-this-tool-plugin-real-https/work/site-publication -C $taskSite status --short --branch
$taskPattern='(gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|sk-[A-Za-z0-9_-]{30,}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|https?://[^\s/@]+:[^\s/@]+@)'
$taskFindings=@(foreach($taskPath in $taskPublishedPaths){Select-String -LiteralPath (Join-Path $taskSite $taskPath) -Pattern $taskPattern | ForEach-Object { [pscustomobject]@{path=$taskPath;line=$_.LineNumber} }})
$taskFindings | ConvertTo-Json -Compress
[pscustomobject]@{scanned_site_files=$taskPublishedPaths.Count;matches=$taskFindings.Count} | ConvertTo-Json -Compress
```

Output:

```text
{"source_files":77,"source_copy_hash_mismatches":0}
## main...origin/main
 M app/page.tsx
{"scanned_site_files":77,"matches":0}
```

Exit code: 0.

### Site source commit, push and remote-head verification

Command:

```powershell
$ErrorActionPreference='Stop'
$taskSite='C:\Users\scott\Documents\Codex\2026-09-01\is-this-tool-plugin-real-https\work\site-publication'
$taskRemote='https://git.chatgpt-team.site/02f150c7-9f91-4896-b7f2-1eece80a472d/appgprj_6a9691bac0fc819181ccdad8daae4ed4.git'
$taskHeader='Authorization: Bearer [REDACTED-SHORT-LIVED-CREDENTIAL]'
if((git -c safe.directory=C:/Users/scott/Documents/Codex/2026-09-01/is-this-tool-plugin-real-https/work/site-publication -C $taskSite remote get-url origin) -ne $taskRemote){throw 'Unexpected site remote'}
git -c safe.directory=C:/Users/scott/Documents/Codex/2026-09-01/is-this-tool-plugin-real-https/work/site-publication -C $taskSite add -- app/page.tsx
if($LASTEXITCODE){throw 'Site stage failed'}
git -c safe.directory=C:/Users/scott/Documents/Codex/2026-09-01/is-this-tool-plugin-real-https/work/site-publication -C $taskSite commit -m 'Align research evidence and unfinished work with the verified Gateway checkpoint'
if($LASTEXITCODE){throw 'Site commit failed'}
git -c safe.directory=C:/Users/scott/Documents/Codex/2026-09-01/is-this-tool-plugin-real-https/work/site-publication -c "http.extraHeader=$taskHeader" -C $taskSite push origin main
if($LASTEXITCODE){throw 'Site push failed'}
$taskSha=git -c safe.directory=C:/Users/scott/Documents/Codex/2026-09-01/is-this-tool-plugin-real-https/work/site-publication -C $taskSite rev-parse HEAD
$taskRemoteHead=git -c safe.directory=C:/Users/scott/Documents/Codex/2026-09-01/is-this-tool-plugin-real-https/work/site-publication -c "http.extraHeader=$taskHeader" -C $taskSite ls-remote origin refs/heads/main
if($LASTEXITCODE -or -not $taskRemoteHead.StartsWith($taskSha)){throw 'Site source head verification failed'}
[pscustomobject]@{commit_sha=$taskSha;remote_head_matches=$true} | ConvertTo-Json -Compress
git -c safe.directory=C:/Users/scott/Documents/Codex/2026-09-01/is-this-tool-plugin-real-https/work/site-publication -C $taskSite status --short --branch
```

Output:

```text
warning: in the working copy of 'app/page.tsx', LF will be replaced by CRLF the next time Git touches it
[main b7bd4ff] Align research evidence and unfinished work with the verified Gateway checkpoint
 1 file changed, 49 insertions(+), 23 deletions(-)
To https://git.chatgpt-team.site/02f150c7-9f91-4896-b7f2-1eece80a472d/appgprj_6a9691bac0fc819181ccdad8daae4ed4.git
   519def3..b7bd4ff  main -> main
{"commit_sha":"b7bd4ff7c2c0a29d5f3ebcc0358c590abcf49894","remote_head_matches":true}
## main...origin/main
```

Exit code: 0.

### Site packaging

Command:

```powershell
& 'C:\Program Files\Git\bin\bash.exe' 'C:/Users/scott/.codex/plugins/cache/openai-bundled/sites/0.1.52/scripts/package-site.sh' '/c/Users/scott/Desktop/Code/halo-research-gateway/website' '/c/Users/scott/Documents/Codex/2026-09-01/is-this-tool-plugin-real-https/outputs/halo-research-site-evidence-2026-09-03.tar.gz'
if ($LASTEXITCODE) { throw 'Site archive packaging failed' }
Get-FileHash -LiteralPath 'C:\Users\scott\Documents\Codex\2026-09-01\is-this-tool-plugin-real-https\outputs\halo-research-site-evidence-2026-09-03.tar.gz' | Select-Object Path,Hash | ConvertTo-Json -Compress
```

Output:

```text
/c/Users/scott/Documents/Codex/2026-09-01/is-this-tool-plugin-real-https/outputs/halo-research-site-evidence-2026-09-03.tar.gz
{"Path":"C:\\Users\\scott\\Documents\\Codex\\2026-09-01\\is-this-tool-plugin-real-https\\outputs\\halo-research-site-evidence-2026-09-03.tar.gz","Hash":"DC19C615D4CBC2830AEE1E1E1950AA7D8A6582CA2CA06B0DBE3E60437FBAA07D"}
```

Exit code: 0.

### Preview teardown

Command:

```powershell
write_stdin(session_id=42586, chars=CTRL-C)
```

Output:

```text
 GET / 200 in 150ms (compile: 1788415611.4s, render: 96ms)
 GET / 200 in 168ms (compile: 1788415611.4s, render: 127ms)
12:09:02 AM [vite] (rsc) hmr update /@id/__x00__virtual:vinext-rsc-entry, /app/globals.css
12:09:02 AM [vite] (client) hmr update /app/globals.css?direct
[vite] hot updated:  virtual:vinext-rsc-entry
 GET /?_rsc 200 in 336ms (compile: 1788415611.6s, render: 0ms)
```

Exit code: 1.

### Verified deployment response

```json
{
  "id": "appgdep_6a990ff5dec881919f3b22751d4881cd",
  "project_id": "appgprj_6a9691bac0fc819181ccdad8daae4ed4",
  "title": "Halo Research Gateway",
  "version_id": "appgprj_6a9691bac0fc819181ccdad8daae4ed4~appgver_244ab10fea808191b7b8b2cdb300bc59",
  "type": "publish",
  "status": "succeeded",
  "url": "https://halo-research-gateway.sconverse.chatgpt.site",
  "screenshot_asset_pointer": null,
  "provider_deployment_id": "site---6a9691bac0fc819181ccdad8daae4ed4",
  "failure_message": null,
  "env_set_revision": 0,
  "updated_at": "2026-09-03T06:13:20.213800+00:00"
}
```
