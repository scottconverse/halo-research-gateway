# Cursor-only MCP contract and live-source evidence — 2026-09-02

## Scope and result

Base: 39941a92130de8560fa7730c64dff6797c871a79, product 0.2.0, result schema 1.5.
This fixes an existing research contract, without adding actions or changing DSH
capabilities. Delivery/CI/live-installed identity is recorded separately.

An actual authenticated native MCP GitHub thread read exposed that community_thread
returned page one but its cursor-only continuation failed schema validation.
The same mismatch existed in transcript_fetch, community_search and deep_research.
Their MCP and service seed arguments now default to None. New requests still fail
with explicit policy errors when the URL/query/question is absent. Valid cursors
resume before seed validation; malformed cursors reach the existing signed validator.
Durable job result cursors belong to deep_research, so no placeholder question is
needed for that nested result. No job-control behavior or authorization changed.

Twenty-nine new tests cover all thirteen pageable reader dispatch paths, all four
published schemas, missing-input behavior, invalid cursors and direct-service calls.
They seed retained normalized fixture evidence and verify complete collected text
through the real tool manager; they do not claim thirteen live upstream providers.
The separate native canaries below use actual subprocesses, MCP HTTP and upstreams.

## Evidence gained

- Real anonymous Exa search succeeded. A disposable Gateway's configured one-request
  quota then forced a different web query through the actual DDGS provider. It returned
  official Python sources and the Gateway fetched 2,664 characters from a returned URL.
  No provider response was mocked. Installed quotas/configuration were unchanged.
- Authenticated native MCP used the existing gh login through a temporary DPAPI vault.
  It read a 19-comment public GitHub discussion (20 citable items) over eight response
  pages, another discussion's depth-two replies over seven pages, and 11,261 characters
  of a commit-pinned Playwright README over 46 small pages. Reply/result/scan-limit
  warnings remain visible. This does not prove unlimited GitHub traversal.
- Authenticated results had no persistent cache key and disk cache remained empty.
  Token absence in unencrypted temporary files, MCP responses and native logs was
  checked. The owned child exited and temporary vault/state was removed.
  No production connection, account scope change, GitHub mutation or paid call occurred.
- Current DSH was tested again in session-21cc0995-f351-4d3e-ab03-7cac579cfd96 with
  existing lmstudio / halo/qwen3.6-35b-a3b selection. It selected web_search but failed
  before dispatch: Cannot read properties of undefined (reading 'prepare').
  Zero tool results, no fetched pages/cursors, no supported answer; all 120 prior
  sessions retained. Scoped package-resolution repair/restart approval was requested.
  These successful Gateway tests are not a substitute for a DSH workflow.

## Test-development failures and limitations

The first DSH preflight incorrectly assumed zero events in a new session. The actual
three permission/preset, sandbox/mode and approval/policy initialization events were
inspected; the guard now allows only those events before prompting. No duplicate
prompt was sent and no new model/settings were selected.

The initial GitHub canary expected github-api for the community wrapper. Source showed
the documented wrapper identity is github-discussions with authenticated_source=true;
the test was corrected to verify both. The next live failure was the real cursor-only
schema defect, reproduced before implementation.

The initial unit run reported 20 failures: sixteen were assertion failures, while four
schema-inspection tests used the wrong SDK attribute inputSchema instead of input_schema.
Those four are not counted as assertion RED. After fixing that test attribute, only the
four app signatures were temporarily restored to their original state to capture four
proper schema assertion failures, then the minimal fix was restored. The first targeted
post-fix output was tool-truncated; the complete unchanged rerun of its four test errors
is retained immediately after it. No original truncation is represented as complete.

Script lint initially found synchronous pathlib calls inside async test code; those
checks were moved to an awaited thread, with no product behavior change.

Read before edits: complete app.py, affected service methods/guards, cursor/envelope and
adjacent tests; search/Exa/rate ledger, GitHub/community adapters, migrations/DPAPI store
and native fixture patterns; README/manual/status/progress/changelog/scope.
Baseline passed 314 tests. Full gate after the product fix passed 343 tests. The final
tracked live scripts also pass format/lint and real upstream acceptance below.

## Security, scope and remaining work

- Inputs: cursor signatures, tool/profile binding and initial-input validation retained;
  only four now-optional seed parameters changed. No unsafe URL policy change.
- Routes/auth: no new endpoints, credential flows or authorization policy in product code.
  Thirteen readers plus the existing job-control tool remain; no outbound action tools.
- Secrets/logs: canary token never appears in command arguments, output or plaintext
  fixtures; temporary encrypted connection only. Whole-repo scan is a separate pre-push step.
- Rendering/deserialization: existing JSON/signed cursor path only; no eval/pickle added.
- Dependencies: none added or changed; no new dependency review is applicable.
- Performance: continuation still returns retained evidence without upstream reads.
  Native tests bound pages, requested replies and owned subprocess lifetime. They are
  not a general hard memory/CPU limit or exhaustive resource stress.
- Native SDK logs emitted INFO lines despite ERROR configuration. Exa session cleanup
  returned HTTP 405 for DELETE; source retrieval/fallback passed. These observations are
  retained and not presented as clean logging/protocol acceptance.

Still open: DSH workflow/jobs and installed authenticated connection/operator acceptance;
real login/app-bound cookies/challenge/provider routing; advanced crawl options;
broader shared/response/job-field/disk-cache and native resource limits; lifecycle/stress/
clean installation; metadata/licensing/contributing and final site alignment.
The added source samples are useful bounded evidence, not universal provider correctness.

## Exact commands and outputs

### Unchanged baseline

Command:

```powershell
pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Commit
```

```text
[GATE] lock check
Resolved 130 packages in 1ms
[GATE] format
90 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
.................................................
```

```text
....................... [ 22%]
........................................................................ [ 45%]
.......................
```

```text
................................................. [ 68%]
.........
```

```text
............................................................... [ 91%]
..........................                                               [100%]
314 passed in 67.40s (0:01:07)
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Commit)

```

### Fresh DSH preflight failure before prompting

Command:

```powershell
uv run --locked python C:/Users/scott/Documents/Codex/2026-09-01/is-this-tool-plugin-real-https/outputs/dsh-current-acceptance.py
```

```text
Traceback (most recent call last):
  File "C:\Users\scott\Documents\Codex\2026-09-01\is-this-tool-plugin-real-https\outputs\dsh-current-acceptance.py", line 61, in <module>
    raise SystemExit(asyncio.run(main()))
                     ^^^^^^^^^^^^^^^^^^^
  File "C:\Users\scott\AppData\Local\Programs\Python\Python312\Lib\asyncio\runners.py", line 195, in run
    return runner.run(main)
           ^^^^^^^^^^^^^^^^
  File "C:\Users\scott\AppData\Local\Programs\Python\Python312\Lib\asyncio\runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\scott\AppData\Local\Programs\Python\Python312\Lib\asyncio\base_events.py", line 691, in run_until_complete
    return future.result()
           ^^^^^^^^^^^^^^^
  File "C:\Users\scott\Documents\Codex\2026-09-01\is-this-tool-plugin-real-https\outputs\dsh-current-acceptance.py", line 31, in main
    assert not history["events"], "Owned session already has events; refusing duplicate prompt"
           ^^^^^^^^^^^^^^^^^^^^^
AssertionError: Owned session already has events; refusing duplicate prompt

```

### Initialization event inspection

Command:

```powershell
$taskBody=@{type='client-request';rpcId=[guid]::NewGuid().ToString();method='session.history';payload=@{sessionId='session-21cc0995-f351-4d3e-ab03-7cac579cfd96';maxMessages=100}} | ConvertTo-Json -Compress
$taskHistory=(Invoke-RestMethod http://127.0.0.1:3080/api/session.history -Method Post -ContentType application/json -Body $taskBody -TimeoutSec 15).result.value
$taskHistory.events | ForEach-Object { [pscustomobject]@{type=$_.event.type;data_keys=@($_.event.data.PSObject.Properties.Name)} } | ConvertTo-Json -Depth 4 -Compress
```

```text
[{"type":"permission/preset","data_keys":["preset"]},{"type":"sandbox/mode","data_keys":["mode"]},{"type":"approval/policy","data_keys":["policy"]}]

```

### Fresh DSH research attempt and failed verdict

Command:

```powershell
uv run --locked python C:/Users/scott/Documents/Codex/2026-09-01/is-this-tool-plugin-real-https/outputs/dsh-current-acceptance.py
```

```text
{"session": "session-21cc0995-f351-4d3e-ab03-7cac579cfd96", "model": {"provider": "lmstudio", "model": "halo/qwen3.6-35b-a3b"}, "prompt_sent": true}

```

```text
{"running": false, "events": 52, "last_types": ["tool/call", "step/end", "turn/end", "session/title"]}
{"workflow_verdict": {"passed": false, "turn_end": {"kind": "error", "error": {"message": "Cannot read properties of undefined (reading 'prepare')", "code": "UNKNOWN"}}, "calls": ["mcp__halo_research__web_search"], "result_events": 0, "cursor_used": false, "fetched_urls": [], "final": "I'll use the Halo Research Gateway tools to answer this question about Python asyncio TaskGroup behavior.\n\n", "semantic_evidence_review_required": true}}
{"finished": true, "missing_existing_sessions": 0}

```

### Initial real search failover canary

Command:

```powershell
uv run --locked python C:/Users/scott/Documents/Codex/2026-09-01/is-this-tool-plugin-real-https/outputs/gateway-live-fallback.py
```

```text
{"case": "primary_attempt", "provider": "exa-anonymous", "urls": ["https://docs.python.org/3/library/asyncio-exceptions.html", "https://docs.python.org/3/library/asyncio-task.html", "https://docs.python.org/release/3.12.1/library/asyncio-task.html"], "pages": 25, "warnings": ["RESULT_TRUNCATED"], "exa_ledger": {"window": "2026-09-03", "requests": 1, "consecutive_429": 0, "circuit": "closed", "circuit_until": null}}
{"case": "quota_induced_real_ddgs_fallback", "provider": "ddgs-accountless", "urls": ["https://docs.python.org/3/library/asyncio-exceptions.html", "https://docs.python.org/3/library/asyncio-task.html", "https://docs.python.org/3/library/asyncio.html"], "pages": 2, "warnings": ["PROVIDER_FALLBACK_USED", "RESULT_TRUNCATED"], "exa_admissions_unchanged": true}
{"case": "fallback_source_read", "url": "https://docs.python.org/3/library/asyncio-exceptions.html", "chars": 2664, "sha256": "af554e59402bf4f7f84d514c21333e0e218c2190df8b7ca84a44f8e0d090932b", "pages": 1, "warnings": []}
Live native Gateway Exa admission -> quota fallback -> DDGS -> source fetch PASS
NATIVE GATEWAY OUTPUT: [09/02/26 21:43:14] INFO     StreamableHTTP      streamable_http_manager.py:148
                             session manager                                   
                             started                                           
[09/02/26 21:43:15] INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     HTTP Request: POST                 _client.py:1740
                             https://mcp.exa.ai/mcp?tools=web_s                
                             earch_exa,web_fetch_exa "HTTP/1.1                 
                             200 OK"                                           
                    INFO     Received session ID:        streamable_http.py:146
                             c64886dd-0f10-4405-9038-d4f                       
                             46e45fc16                                         
                    INFO     GET stream disconnected,    streamable_http.py:240
                             reconnecting in 1000ms...                         
                    INFO     HTTP Request: POST                 _client.py:1740
                             https://mcp.exa.ai/mcp?tools=web_s                
                             earch_exa,web_fetch_exa "HTTP/1.1                 
                             202 Accepted"                                     
[09/02/26 21:43:16] INFO     HTTP Request: POST                 _client.py:1740
                             https://mcp.exa.ai/mcp?tools=web_s                
                             earch_exa,web_fetch_exa "HTTP/1.1                 
                             200 OK"                                           
                    INFO     HTTP Request: POST                 _client.py:1740
                             https://mcp.exa.ai/mcp?tools=web_s                
                             earch_exa,web_fetch_exa "HTTP/1.1                 
                             200 OK"                                           
                    INFO     HTTP Request: DELETE               _client.py:1740
                             https://mcp.exa.ai/mcp?tools=web_s                
                             earch_exa,web_fetch_exa "HTTP/1.1                 
                             405 Method Not Allowed"                           
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
[09/02/26 21:43:17] INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     response:                               lib.rs:429
                             https://en.wikipedia.org/w/api.php?acti           
                             on=opensearch&profile=fuzzy&limit=1&sea           
                             rch=site%3Adocs.python.org%20asyncio%20           
                             cancellation%20CancelledError%20excepti           
                             on 200                                            
                    INFO     response:                               lib.rs:429
                             https://grokipedia.com/api/typeahead?qu           
                             ery=site%3Adocs.python.org+asyncio+canc           
                             ellation+CancelledError+exception&limit           
                             =1 200                                            
[09/02/26 21:43:18] INFO     response:                               lib.rs:429
                             https://html.duckduckgo.com/html/ 200             
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     HTTP Request: GET                  _client.py:1740
                             https://docs.python.org/3/library/                
                             asyncio-exceptions.html "HTTP/1.1                 
                             200 OK"                                           
                    INFO     Terminating session: None   streamable_http.py:814

{"owned_native_process_stopped": true}

```

### Initial GitHub wrapper-identity test error

Command:

```powershell
uv run --locked python C:/Users/scott/Documents/Codex/2026-09-01/is-this-tool-plugin-real-https/outputs/gateway-github-mcp-live.py
```

```text
{"case": "authenticated_mcp_discussion_search", "urls": ["https://github.com/foodcoops/foodsoft/discussions/1258", "https://github.com/unclecode/crawl4ai/discussions/2118", "https://github.com/unclecode/crawl4ai/discussions/508"], "pages": 1, "warnings": ["GITHUB_RESULTS_LIMIT_REACHED"], "selected_reply_count": 19}
NATIVE GATEWAY OUTPUT: [09/02/26 21:45:47] INFO     StreamableHTTP      streamable_http_manager.py:148
                             session manager                                   
                             started                                           
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
[09/02/26 21:45:48] INFO     HTTP Request: POST                 _client.py:1740
                             https://api.github.com/graphql                    
                             "HTTP/1.1 200 OK"                                 
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
[09/02/26 21:45:49] INFO     HTTP Request: POST                 _client.py:1740
                             https://api.github.com/graphql                    
                             "HTTP/1.1 200 OK"                                 
                    INFO     Terminating session: None   streamable_http.py:814

{"owned_native_process_stopped": true}
  + Exception Group Traceback (most recent call last):
  |   File "C:\Users\scott\Documents\Codex\2026-09-01\is-this-tool-plugin-real-https\outputs\gateway-github-mcp-live.py", line 140, in <module>
  |     asyncio.run(main())
  |   File "C:\Users\scott\AppData\Local\Programs\Python\Python312\Lib\asyncio\runners.py", line 195, in run
  |     return runner.run(main)
  |            ^^^^^^^^^^^^^^^^
  |   File "C:\Users\scott\AppData\Local\Programs\Python\Python312\Lib\asyncio\runners.py", line 118, in run
  |     return self._loop.run_until_complete(task)
  |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  |   File "C:\Users\scott\AppData\Local\Programs\Python\Python312\Lib\asyncio\base_events.py", line 691, in run_until_complete
  |     return future.result()
  |            ^^^^^^^^^^^^^^^
  |   File "C:\Users\scott\Documents\Codex\2026-09-01\is-this-tool-plugin-real-https\outputs\gateway-github-mcp-live.py", line 70, in main
  |     async with streamable_http_client(f"http://127.0.0.1:{port}/mcp", http_client=http) as streams:
  |                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  |   File "C:\Users\scott\AppData\Local\Programs\Python\Python312\Lib\contextlib.py", line 231, in __aexit__
  |     await self.gen.athrow(value)
  |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\.venv\Lib\site-packages\mcp\client\streamable_http.py", line 688, in streamable_http_client
  |     anyio.create_task_group() as tg,
  |     ^^^^^^^^^^^^^^^^^^^^^^^^^
  |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\.venv\Lib\site-packages\anyio\_backends\_asyncio.py", line 815, in __aexit__
  |     raise BaseExceptionGroup(
  | ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception)
  +-+---------------- 1 ----------------
    | Exception Group Traceback (most recent call last):
    |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\.venv\Lib\site-packages\mcp\client\streamable_http.py", line 705, in streamable_http_client
    |     yield read_stream, write_stream
    |   File "C:\Users\scott\Documents\Codex\2026-09-01\is-this-tool-plugin-real-https\outputs\gateway-github-mcp-live.py", line 71, in main
    |     async with ClientSession(streams[0], streams[1]) as session:
    |                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\.venv\Lib\site-packages\mcp\client\session.py", line 521, in __aexit__
    |     result = await self._task_group.__aexit__(exc_type, exc_val, exc_tb)
    |              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\.venv\Lib\site-packages\anyio\_backends\_asyncio.py", line 815, in __aexit__
    |     raise BaseExceptionGroup(
    | ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception)
    +-+---------------- 1 ----------------
      | Traceback (most recent call last):
      |   File "C:\Users\scott\Documents\Codex\2026-09-01\is-this-tool-plugin-real-https\outputs\gateway-github-mcp-live.py", line 102, in main
      |     thread, pages, warnings = await collect("community_thread",
      |                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      |   File "C:\Users\scott\Documents\Codex\2026-09-01\is-this-tool-plugin-real-https\outputs\gateway-github-mcp-live.py", line 82, in collect
      |     assert value["provider"] == "github-api", value["provider"]
      |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      | AssertionError: github-discussions
      +------------------------------------

```

### Live cursor-only schema failure

Command:

```powershell
uv run --locked python C:/Users/scott/Documents/Codex/2026-09-01/is-this-tool-plugin-real-https/outputs/gateway-github-mcp-live.py
```

```text
{"case": "authenticated_mcp_discussion_search", "urls": ["https://github.com/foodcoops/foodsoft/discussions/1258", "https://github.com/unclecode/crawl4ai/discussions/2118", "https://github.com/unclecode/crawl4ai/discussions/508"], "pages": 1, "warnings": ["GITHUB_RESULTS_LIMIT_REACHED"], "selected_reply_count": 19}
NATIVE GATEWAY OUTPUT: [09/02/26 21:46:26] INFO     StreamableHTTP      streamable_http_manager.py:148
                             session manager                                   
                             started                                           
[09/02/26 21:46:27] INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
[09/02/26 21:46:28] INFO     HTTP Request: POST                 _client.py:1740
                             https://api.github.com/graphql                    
                             "HTTP/1.1 200 OK"                                 
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     HTTP Request: POST                 _client.py:1740
                             https://api.github.com/graphql                    
                             "HTTP/1.1 200 OK"                                 
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Tool 'community_thread' rejected     server.py:435
                             arguments: ['url']                                
                    INFO     Terminating session: None   streamable_http.py:814

{"owned_native_process_stopped": true}
  + Exception Group Traceback (most recent call last):
  |   File "C:\Users\scott\Documents\Codex\2026-09-01\is-this-tool-plugin-real-https\outputs\gateway-github-mcp-live.py", line 143, in <module>
  |     asyncio.run(main())
  |   File "C:\Users\scott\AppData\Local\Programs\Python\Python312\Lib\asyncio\runners.py", line 195, in run
  |     return runner.run(main)
  |            ^^^^^^^^^^^^^^^^
  |   File "C:\Users\scott\AppData\Local\Programs\Python\Python312\Lib\asyncio\runners.py", line 118, in run
  |     return self._loop.run_until_complete(task)
  |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  |   File "C:\Users\scott\AppData\Local\Programs\Python\Python312\Lib\asyncio\base_events.py", line 691, in run_until_complete
  |     return future.result()
  |            ^^^^^^^^^^^^^^^
  |   File "C:\Users\scott\Documents\Codex\2026-09-01\is-this-tool-plugin-real-https\outputs\gateway-github-mcp-live.py", line 70, in main
  |     async with streamable_http_client(f"http://127.0.0.1:{port}/mcp", http_client=http) as streams:
  |                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  |   File "C:\Users\scott\AppData\Local\Programs\Python\Python312\Lib\contextlib.py", line 231, in __aexit__
  |     await self.gen.athrow(value)
  |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\.venv\Lib\site-packages\mcp\client\streamable_http.py", line 688, in streamable_http_client
  |     anyio.create_task_group() as tg,
  |     ^^^^^^^^^^^^^^^^^^^^^^^^^
  |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\.venv\Lib\site-packages\anyio\_backends\_asyncio.py", line 815, in __aexit__
  |     raise BaseExceptionGroup(
  | ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception)
  +-+---------------- 1 ----------------
    | Exception Group Traceback (most recent call last):
    |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\.venv\Lib\site-packages\mcp\client\streamable_http.py", line 705, in streamable_http_client
    |     yield read_stream, write_stream
    |   File "C:\Users\scott\Documents\Codex\2026-09-01\is-this-tool-plugin-real-https\outputs\gateway-github-mcp-live.py", line 71, in main
    |     async with ClientSession(streams[0], streams[1]) as session:
    |                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\.venv\Lib\site-packages\mcp\client\session.py", line 521, in __aexit__
    |     result = await self._task_group.__aexit__(exc_type, exc_val, exc_tb)
    |              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\.venv\Lib\site-packages\anyio\_backends\_asyncio.py", line 815, in __aexit__
    |     raise BaseExceptionGroup(
    | ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception)
    +-+---------------- 1 ----------------
      | Traceback (most recent call last):
      |   File "C:\Users\scott\Documents\Codex\2026-09-01\is-this-tool-plugin-real-https\outputs\gateway-github-mcp-live.py", line 105, in main
      |     thread, pages, warnings = await collect("community_thread",
      |                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      |   File "C:\Users\scott\Documents\Codex\2026-09-01\is-this-tool-plugin-real-https\outputs\gateway-github-mcp-live.py", line 80, in collect
      |     value = json.loads(wire)
      |             ^^^^^^^^^^^^^^^^
      |   File "C:\Users\scott\AppData\Local\Programs\Python\Python312\Lib\json\__init__.py", line 346, in loads
      |     return _default_decoder.decode(s)
      |            ^^^^^^^^^^^^^^^^^^^^^^^^^^
      |   File "C:\Users\scott\AppData\Local\Programs\Python\Python312\Lib\json\decoder.py", line 338, in decode
      |     obj, end = self.raw_decode(s, idx=_w(s, 0).end())
      |                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      |   File "C:\Users\scott\AppData\Local\Programs\Python\Python312\Lib\json\decoder.py", line 356, in raw_decode
      |     raise JSONDecodeError("Expecting value", s, err.value) from None
      | json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
      +------------------------------------

```

### Initial unit RED (four schema-test errors disclosed above)

Command:

```powershell
uv run --locked pytest -q tests/unit/test_cursor_tool_contract.py
```

```text
FFFF......F.FFF..FFFFFFFFFFFF                                            [100%]
================================== FAILURES ===================================
_ test_schema_does_not_require_original_selector_for_continuation[deep_research] _

app = <starlette.applications.Starlette object at 0x000001C0F43F2150>
tool = 'deep_research'

    @pytest.mark.parametrize("tool", REPAIRED)
    async def test_schema_does_not_require_original_selector_for_continuation(app, tool):
        definitions = {entry.name: entry for entry in await app.state.mcp_server.list_tools()}
        selector, _ = REPAIRED[tool]
>       assert selector not in definitions[tool].inputSchema.get("required", []), (
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            f"{tool} advertises a cursor but requires {selector} before dispatch"
        )

tests\unit\test_cursor_tool_contract.py:54: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = Tool(name='deep_research', title=None, description='Collect a bounded multi-source evidence packet; returns evidence, ...eep_researchArguments', 'type': 'object'}, execution=None, output_schema=None, icons=None, annotations=None, meta=None)
item = 'inputSchema'

    def __getattr__(self, item: str) -> Any:
        private_attributes = object.__getattribute__(self, '__private_attributes__')
        if item in private_attributes:
            attribute = private_attributes[item]
            if hasattr(attribute, '__get__'):
                return attribute.__get__(self, type(self))  # type: ignore
    
            try:
                # Note: self.__pydantic_private__ cannot be None if self.__private_attributes__ has items
                return self.__pydantic_private__[item]  # type: ignore
            except KeyError as exc:
                raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}') from exc
        else:
            # `__pydantic_extra__` can fail to be set if the model is not yet fully initialized.
            # See `BaseModel.__repr_args__` for more details
            try:
                pydantic_extra = object.__getattribute__(self, '__pydantic_extra__')
            except AttributeError:
                pydantic_extra = None
    
            if pydantic_extra and item in pydantic_extra:
                return pydantic_extra[item]
            else:
                if hasattr(self.__class__, item):
                    return super().__getattribute__(item)  # Raises AttributeError if appropriate
                else:
                    # this is the current error
>                   raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}')
E                   AttributeError: 'Tool' object has no attribute 'inputSchema'. Did you mean: 'input_schema'?

.venv\Lib\site-packages\pydantic\main.py:1042: AttributeError
_ test_schema_does_not_require_original_selector_for_continuation[transcript_fetch] _

app = <starlette.applications.Starlette object at 0x000001C0F44AAAE0>
tool = 'transcript_fetch'

    @pytest.mark.parametrize("tool", REPAIRED)
    async def test_schema_does_not_require_original_selector_for_continuation(app, tool):
        definitions = {entry.name: entry for entry in await app.state.mcp_server.list_tools()}
        selector, _ = REPAIRED[tool]
>       assert selector not in definitions[tool].inputSchema.get("required", []), (
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            f"{tool} advertises a cursor but requires {selector} before dispatch"
        )

tests\unit\test_cursor_tool_contract.py:54: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = Tool(name='transcript_fetch', title=None, description='Retrieve public captions or transcript text for a known media U...script_fetchArguments', 'type': 'object'}, execution=None, output_schema=None, icons=None, annotations=None, meta=None)
item = 'inputSchema'

    def __getattr__(self, item: str) -> Any:
        private_attributes = object.__getattribute__(self, '__private_attributes__')
        if item in private_attributes:
            attribute = private_attributes[item]
            if hasattr(attribute, '__get__'):
                return attribute.__get__(self, type(self))  # type: ignore
    
            try:
                # Note: self.__pydantic_private__ cannot be None if self.__private_attributes__ has items
                return self.__pydantic_private__[item]  # type: ignore
            except KeyError as exc:
                raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}') from exc
        else:
            # `__pydantic_extra__` can fail to be set if the model is not yet fully initialized.
            # See `BaseModel.__repr_args__` for more details
            try:
                pydantic_extra = object.__getattribute__(self, '__pydantic_extra__')
            except AttributeError:
                pydantic_extra = None
    
            if pydantic_extra and item in pydantic_extra:
                return pydantic_extra[item]
            else:
                if hasattr(self.__class__, item):
                    return super().__getattribute__(item)  # Raises AttributeError if appropriate
                else:
                    # this is the current error
>                   raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}')
E                   AttributeError: 'Tool' object has no attribute 'inputSchema'. Did you mean: 'input_schema'?

.venv\Lib\site-packages\pydantic\main.py:1042: AttributeError
_ test_schema_does_not_require_original_selector_for_continuation[community_search] _

app = <starlette.applications.Starlette object at 0x000001C0F461DE80>
tool = 'community_search'

    @pytest.mark.parametrize("tool", REPAIRED)
    async def test_schema_does_not_require_original_selector_for_continuation(app, tool):
        definitions = {entry.name: entry for entry in await app.state.mcp_server.list_tools()}
        selector, _ = REPAIRED[tool]
>       assert selector not in definitions[tool].inputSchema.get("required", []), (
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            f"{tool} advertises a cursor but requires {selector} before dispatch"
        )

tests\unit\test_cursor_tool_contract.py:54: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = Tool(name='community_search', title=None, description='Search public technical discussions outside Reddit.', input_sch...unity_searchArguments', 'type': 'object'}, execution=None, output_schema=None, icons=None, annotations=None, meta=None)
item = 'inputSchema'

    def __getattr__(self, item: str) -> Any:
        private_attributes = object.__getattribute__(self, '__private_attributes__')
        if item in private_attributes:
            attribute = private_attributes[item]
            if hasattr(attribute, '__get__'):
                return attribute.__get__(self, type(self))  # type: ignore
    
            try:
                # Note: self.__pydantic_private__ cannot be None if self.__private_attributes__ has items
                return self.__pydantic_private__[item]  # type: ignore
            except KeyError as exc:
                raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}') from exc
        else:
            # `__pydantic_extra__` can fail to be set if the model is not yet fully initialized.
            # See `BaseModel.__repr_args__` for more details
            try:
                pydantic_extra = object.__getattribute__(self, '__pydantic_extra__')
            except AttributeError:
                pydantic_extra = None
    
            if pydantic_extra and item in pydantic_extra:
                return pydantic_extra[item]
            else:
                if hasattr(self.__class__, item):
                    return super().__getattribute__(item)  # Raises AttributeError if appropriate
                else:
                    # this is the current error
>                   raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}')
E                   AttributeError: 'Tool' object has no attribute 'inputSchema'. Did you mean: 'input_schema'?

.venv\Lib\site-packages\pydantic\main.py:1042: AttributeError
_ test_schema_does_not_require_original_selector_for_continuation[community_thread] _

app = <starlette.applications.Starlette object at 0x000001C0F45B9520>
tool = 'community_thread'

    @pytest.mark.parametrize("tool", REPAIRED)
    async def test_schema_does_not_require_original_selector_for_continuation(app, tool):
        definitions = {entry.name: entry for entry in await app.state.mcp_server.list_tools()}
        selector, _ = REPAIRED[tool]
>       assert selector not in definitions[tool].inputSchema.get("required", []), (
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            f"{tool} advertises a cursor but requires {selector} before dispatch"
        )

tests\unit\test_cursor_tool_contract.py:54: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = Tool(name='community_thread', title=None, description='Read one public community discussion thread; Reddit routes to r...unity_threadArguments', 'type': 'object'}, execution=None, output_schema=None, icons=None, annotations=None, meta=None)
item = 'inputSchema'

    def __getattr__(self, item: str) -> Any:
        private_attributes = object.__getattribute__(self, '__private_attributes__')
        if item in private_attributes:
            attribute = private_attributes[item]
            if hasattr(attribute, '__get__'):
                return attribute.__get__(self, type(self))  # type: ignore
    
            try:
                # Note: self.__pydantic_private__ cannot be None if self.__private_attributes__ has items
                return self.__pydantic_private__[item]  # type: ignore
            except KeyError as exc:
                raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}') from exc
        else:
            # `__pydantic_extra__` can fail to be set if the model is not yet fully initialized.
            # See `BaseModel.__repr_args__` for more details
            try:
                pydantic_extra = object.__getattribute__(self, '__pydantic_extra__')
            except AttributeError:
                pydantic_extra = None
    
            if pydantic_extra and item in pydantic_extra:
                return pydantic_extra[item]
            else:
                if hasattr(self.__class__, item):
                    return super().__getattribute__(item)  # Raises AttributeError if appropriate
                else:
                    # this is the current error
>                   raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}')
E                   AttributeError: 'Tool' object has no attribute 'inputSchema'. Did you mean: 'input_schema'?

.venv\Lib\site-packages\pydantic\main.py:1042: AttributeError
_ test_cursor_only_dispatch_returns_all_retained_evidence_for_each_reader[deep_research] _

app = <starlette.applications.Starlette object at 0x000001C0F48C1B20>
tool = 'deep_research'

    @pytest.mark.parametrize("tool", READERS)
    async def test_cursor_only_dispatch_returns_all_retained_evidence_for_each_reader(app, tool):
        body = "Retained source evidence must survive every cursor-only call. " * 100
        result = ProviderResult("contract-fixture", [
            EvidenceItem(url="https://example.org/research", retrieved_at="2026-09-03T03:00:00Z", content=body)
        ])
        page = app.state.halo_service._envelope(tool, result, 2000)
        content, pages = "", 0
        assert page["page"]["next_cursor"]
        while True:
            assert page["ok"] and page["tool"] == tool
            assert page["provider"] == "contract-fixture"
            assert len(json.dumps(page, indent=2, ensure_ascii=False)) == page["page"]["serialized_chars"] <= 2000
            content += "".join(item.get("content") or "" for item in page["items"])
            pages += 1
            cursor = page["page"]["next_cursor"]
            if not cursor:
                break
            assert pages < 100
>           page = await dispatch(app, tool, {"cursor": cursor, "max_chars": 2000})
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_cursor_tool_contract.py:77: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

app = <starlette.applications.Starlette object at 0x000001C0F48C1B20>
tool = 'deep_research'
arguments = {'cursor': 'eyJiIjoyMDAwLCJjIjoxLCJleHAiOjE3ODg0MTEwMDUsImkiOjEsImsiOiIiLCJuIjoyLCJzIjoiNDlmMDVlNDY2Y2U0OWYwMzAxYTQwYz...Y2Q0OTJjZWY3MjRhMSIsInQiOiJkZWVwX3Jlc2VhcmNoIiwidiI6Mn2uU3M63WUFUDXIqN9Obag5hILuomxYKRbAKEx1X9AZjQ', 'max_chars': 2000}

    async def dispatch(app, tool, arguments):
        context = Context(
            request_context=SimpleNamespace(request=SimpleNamespace(headers={})),
            mcp_server=app.state.mcp_server,
        )
        rejected = None
        try:
            result = await app.state.mcp_server._tool_manager.call_tool(tool, arguments, context)
        except Exception as exc:
            rejected = str(exc)
            result = None
>       assert rejected is None, f"MCP rejected a valid continuation or missing-input envelope: {rejected}"
E       AssertionError: MCP rejected a valid continuation or missing-input envelope: Error executing tool deep_research: 1 validation error for deep_researchArguments
E         question
E           Field required [type=missing, input_value={'cursor': 'eyJiIjoyMDAwL...ZjQ', 'max_chars': 2000}, input_type=dict]
E             For further information visit https://errors.pydantic.dev/2.13/v/missing
E       assert "Error executing tool deep_research: 1 validation error for deep_researchArguments\nquestion\n  Field required [type=m...Q', 'max_chars': 2000}, input_type=dict]\n    For further information visit https://errors.pydantic.dev/2.13/v/missing" is None

tests\unit\test_cursor_tool_contract.py:47: AssertionError
_ test_cursor_only_dispatch_returns_all_retained_evidence_for_each_reader[transcript_fetch] _

app = <starlette.applications.Starlette object at 0x000001C0F4678500>
tool = 'transcript_fetch'

    @pytest.mark.parametrize("tool", READERS)
    async def test_cursor_only_dispatch_returns_all_retained_evidence_for_each_reader(app, tool):
        body = "Retained source evidence must survive every cursor-only call. " * 100
        result = ProviderResult("contract-fixture", [
            EvidenceItem(url="https://example.org/research", retrieved_at="2026-09-03T03:00:00Z", content=body)
        ])
        page = app.state.halo_service._envelope(tool, result, 2000)
        content, pages = "", 0
        assert page["page"]["next_cursor"]
        while True:
            assert page["ok"] and page["tool"] == tool
            assert page["provider"] == "contract-fixture"
            assert len(json.dumps(page, indent=2, ensure_ascii=False)) == page["page"]["serialized_chars"] <= 2000
            content += "".join(item.get("content") or "" for item in page["items"])
            pages += 1
            cursor = page["page"]["next_cursor"]
            if not cursor:
                break
            assert pages < 100
>           page = await dispatch(app, tool, {"cursor": cursor, "max_chars": 2000})
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_cursor_tool_contract.py:77: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

app = <starlette.applications.Starlette object at 0x000001C0F4678500>
tool = 'transcript_fetch'
arguments = {'cursor': 'eyJiIjoyMDAwLCJjIjoxLCJleHAiOjE3ODg0MTEwMDUsImkiOjEsImsiOiIiLCJuIjoyLCJzIjoiNDlmMDVlNDY2Y2U0OWYwMzAxYTQwYz...OTJjZWY3MjRhMSIsInQiOiJ0cmFuc2NyaXB0X2ZldGNoIiwidiI6Mn3fg3HydhPIrywYXaAq7o-GKaxR86wJ2cd2vV89Ml0_Wg', 'max_chars': 2000}

    async def dispatch(app, tool, arguments):
        context = Context(
            request_context=SimpleNamespace(request=SimpleNamespace(headers={})),
            mcp_server=app.state.mcp_server,
        )
        rejected = None
        try:
            result = await app.state.mcp_server._tool_manager.call_tool(tool, arguments, context)
        except Exception as exc:
            rejected = str(exc)
            result = None
>       assert rejected is None, f"MCP rejected a valid continuation or missing-input envelope: {rejected}"
E       AssertionError: MCP rejected a valid continuation or missing-input envelope: Error executing tool transcript_fetch: 1 validation error for transcript_fetchArguments
E         url
E           Field required [type=missing, input_value={'cursor': 'eyJiIjoyMDAwL..._Wg', 'max_chars': 2000}, input_type=dict]
E             For further information visit https://errors.pydantic.dev/2.13/v/missing
E       assert "Error executing tool transcript_fetch: 1 validation error for transcript_fetchArguments\nurl\n  Field required [type=...g', 'max_chars': 2000}, input_type=dict]\n    For further information visit https://errors.pydantic.dev/2.13/v/missing" is None

tests\unit\test_cursor_tool_contract.py:47: AssertionError
_ test_cursor_only_dispatch_returns_all_retained_evidence_for_each_reader[community_search] _

app = <starlette.applications.Starlette object at 0x000001C0F4674110>
tool = 'community_search'

    @pytest.mark.parametrize("tool", READERS)
    async def test_cursor_only_dispatch_returns_all_retained_evidence_for_each_reader(app, tool):
        body = "Retained source evidence must survive every cursor-only call. " * 100
        result = ProviderResult("contract-fixture", [
            EvidenceItem(url="https://example.org/research", retrieved_at="2026-09-03T03:00:00Z", content=body)
        ])
        page = app.state.halo_service._envelope(tool, result, 2000)
        content, pages = "", 0
        assert page["page"]["next_cursor"]
        while True:
            assert page["ok"] and page["tool"] == tool
            assert page["provider"] == "contract-fixture"
            assert len(json.dumps(page, indent=2, ensure_ascii=False)) == page["page"]["serialized_chars"] <= 2000
            content += "".join(item.get("content") or "" for item in page["items"])
            pages += 1
            cursor = page["page"]["next_cursor"]
            if not cursor:
                break
            assert pages < 100
>           page = await dispatch(app, tool, {"cursor": cursor, "max_chars": 2000})
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_cursor_tool_contract.py:77: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

app = <starlette.applications.Starlette object at 0x000001C0F4674110>
tool = 'community_search'
arguments = {'cursor': 'eyJiIjoyMDAwLCJjIjoxLCJleHAiOjE3ODg0MTEwMDUsImkiOjEsImsiOiIiLCJuIjoyLCJzIjoiNDlmMDVlNDY2Y2U0OWYwMzAxYTQwYz...OTJjZWY3MjRhMSIsInQiOiJjb21tdW5pdHlfc2VhcmNoIiwidiI6Mn3maiEkUKhApj0ndCHxd-_l2rlgkEWVIKU4Kd-N9tm_dQ', 'max_chars': 2000}

    async def dispatch(app, tool, arguments):
        context = Context(
            request_context=SimpleNamespace(request=SimpleNamespace(headers={})),
            mcp_server=app.state.mcp_server,
        )
        rejected = None
        try:
            result = await app.state.mcp_server._tool_manager.call_tool(tool, arguments, context)
        except Exception as exc:
            rejected = str(exc)
            result = None
>       assert rejected is None, f"MCP rejected a valid continuation or missing-input envelope: {rejected}"
E       AssertionError: MCP rejected a valid continuation or missing-input envelope: Error executing tool community_search: 1 validation error for community_searchArguments
E         query
E           Field required [type=missing, input_value={'cursor': 'eyJiIjoyMDAwL..._dQ', 'max_chars': 2000}, input_type=dict]
E             For further information visit https://errors.pydantic.dev/2.13/v/missing
E       assert "Error executing tool community_search: 1 validation error for community_searchArguments\nquery\n  Field required [typ...Q', 'max_chars': 2000}, input_type=dict]\n    For further information visit https://errors.pydantic.dev/2.13/v/missing" is None

tests\unit\test_cursor_tool_contract.py:47: AssertionError
_ test_cursor_only_dispatch_returns_all_retained_evidence_for_each_reader[community_thread] _

app = <starlette.applications.Starlette object at 0x000001C0F461AFC0>
tool = 'community_thread'

    @pytest.mark.parametrize("tool", READERS)
    async def test_cursor_only_dispatch_returns_all_retained_evidence_for_each_reader(app, tool):
        body = "Retained source evidence must survive every cursor-only call. " * 100
        result = ProviderResult("contract-fixture", [
            EvidenceItem(url="https://example.org/research", retrieved_at="2026-09-03T03:00:00Z", content=body)
        ])
        page = app.state.halo_service._envelope(tool, result, 2000)
        content, pages = "", 0
        assert page["page"]["next_cursor"]
        while True:
            assert page["ok"] and page["tool"] == tool
            assert page["provider"] == "contract-fixture"
            assert len(json.dumps(page, indent=2, ensure_ascii=False)) == page["page"]["serialized_chars"] <= 2000
            content += "".join(item.get("content") or "" for item in page["items"])
            pages += 1
            cursor = page["page"]["next_cursor"]
            if not cursor:
                break
            assert pages < 100
>           page = await dispatch(app, tool, {"cursor": cursor, "max_chars": 2000})
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_cursor_tool_contract.py:77: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

app = <starlette.applications.Starlette object at 0x000001C0F461AFC0>
tool = 'community_thread'
arguments = {'cursor': 'eyJiIjoyMDAwLCJjIjoxLCJleHAiOjE3ODg0MTEwMDYsImkiOjEsImsiOiIiLCJuIjoyLCJzIjoiNDlmMDVlNDY2Y2U0OWYwMzAxYTQwYz...OTJjZWY3MjRhMSIsInQiOiJjb21tdW5pdHlfdGhyZWFkIiwidiI6Mn0G1DkxqBKIo-pqb0do2-4DVM6QWLvLjUdtq43HTQg9fg', 'max_chars': 2000}

    async def dispatch(app, tool, arguments):
        context = Context(
            request_context=SimpleNamespace(request=SimpleNamespace(headers={})),
            mcp_server=app.state.mcp_server,
        )
        rejected = None
        try:
            result = await app.state.mcp_server._tool_manager.call_tool(tool, arguments, context)
        except Exception as exc:
            rejected = str(exc)
            result = None
>       assert rejected is None, f"MCP rejected a valid continuation or missing-input envelope: {rejected}"
E       AssertionError: MCP rejected a valid continuation or missing-input envelope: Error executing tool community_thread: 1 validation error for community_threadArguments
E         url
E           Field required [type=missing, input_value={'cursor': 'eyJiIjoyMDAwL...9fg', 'max_chars': 2000}, input_type=dict]
E             For further information visit https://errors.pydantic.dev/2.13/v/missing
E       assert "Error executing tool community_thread: 1 validation error for community_threadArguments\nurl\n  Field required [type=...g', 'max_chars': 2000}, input_type=dict]\n    For further information visit https://errors.pydantic.dev/2.13/v/missing" is None

tests\unit\test_cursor_tool_contract.py:47: AssertionError
_ test_missing_selector_without_cursor_still_returns_policy_error[deep_research] _

app = <starlette.applications.Starlette object at 0x000001C0F4450200>
tool = 'deep_research'

    @pytest.mark.parametrize("tool", REPAIRED)
    async def test_missing_selector_without_cursor_still_returns_policy_error(app, tool):
>       result = await dispatch(app, tool, {})
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_cursor_tool_contract.py:83: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

app = <starlette.applications.Starlette object at 0x000001C0F4450200>
tool = 'deep_research', arguments = {}

    async def dispatch(app, tool, arguments):
        context = Context(
            request_context=SimpleNamespace(request=SimpleNamespace(headers={})),
            mcp_server=app.state.mcp_server,
        )
        rejected = None
        try:
            result = await app.state.mcp_server._tool_manager.call_tool(tool, arguments, context)
        except Exception as exc:
            rejected = str(exc)
            result = None
>       assert rejected is None, f"MCP rejected a valid continuation or missing-input envelope: {rejected}"
E       AssertionError: MCP rejected a valid continuation or missing-input envelope: Error executing tool deep_research: 1 validation error for deep_researchArguments
E         question
E           Field required [type=missing, input_value={}, input_type=dict]
E             For further information visit https://errors.pydantic.dev/2.13/v/missing
E       assert 'Error executing tool deep_research: 1 validation error for deep_researchArguments\nquestion\n  Field required [type=missing, input_value={}, input_type=dict]\n    For further information visit https://errors.pydantic.dev/2.13/v/missing' is None

tests\unit\test_cursor_tool_contract.py:47: AssertionError
_ test_missing_selector_without_cursor_still_returns_policy_error[transcript_fetch] _

app = <starlette.applications.Starlette object at 0x000001C0F0F6E5A0>
tool = 'transcript_fetch'

    @pytest.mark.parametrize("tool", REPAIRED)
    async def test_missing_selector_without_cursor_still_returns_policy_error(app, tool):
>       result = await dispatch(app, tool, {})
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_cursor_tool_contract.py:83: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

app = <starlette.applications.Starlette object at 0x000001C0F0F6E5A0>
tool = 'transcript_fetch', arguments = {}

    async def dispatch(app, tool, arguments):
        context = Context(
            request_context=SimpleNamespace(request=SimpleNamespace(headers={})),
            mcp_server=app.state.mcp_server,
        )
        rejected = None
        try:
            result = await app.state.mcp_server._tool_manager.call_tool(tool, arguments, context)
        except Exception as exc:
            rejected = str(exc)
            result = None
>       assert rejected is None, f"MCP rejected a valid continuation or missing-input envelope: {rejected}"
E       AssertionError: MCP rejected a valid continuation or missing-input envelope: Error executing tool transcript_fetch: 1 validation error for transcript_fetchArguments
E         url
E           Field required [type=missing, input_value={}, input_type=dict]
E             For further information visit https://errors.pydantic.dev/2.13/v/missing
E       assert 'Error executing tool transcript_fetch: 1 validation error for transcript_fetchArguments\nurl\n  Field required [type=missing, input_value={}, input_type=dict]\n    For further information visit https://errors.pydantic.dev/2.13/v/missing' is None

tests\unit\test_cursor_tool_contract.py:47: AssertionError
_ test_missing_selector_without_cursor_still_returns_policy_error[community_search] _

app = <starlette.applications.Starlette object at 0x000001C0F49BFDD0>
tool = 'community_search'

    @pytest.mark.parametrize("tool", REPAIRED)
    async def test_missing_selector_without_cursor_still_returns_policy_error(app, tool):
>       result = await dispatch(app, tool, {})
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_cursor_tool_contract.py:83: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

app = <starlette.applications.Starlette object at 0x000001C0F49BFDD0>
tool = 'community_search', arguments = {}

    async def dispatch(app, tool, arguments):
        context = Context(
            request_context=SimpleNamespace(request=SimpleNamespace(headers={})),
            mcp_server=app.state.mcp_server,
        )
        rejected = None
        try:
            result = await app.state.mcp_server._tool_manager.call_tool(tool, arguments, context)
        except Exception as exc:
            rejected = str(exc)
            result = None
>       assert rejected is None, f"MCP rejected a valid continuation or missing-input envelope: {rejected}"
E       AssertionError: MCP rejected a valid continuation or missing-input envelope: Error executing tool community_search: 1 validation error for community_searchArguments
E         query
E           Field required [type=missing, input_value={}, input_type=dict]
E             For further information visit https://errors.pydantic.dev/2.13/v/missing
E       assert 'Error executing tool community_search: 1 validation error for community_searchArguments\nquery\n  Field required [type=missing, input_value={}, input_type=dict]\n    For further information visit https://errors.pydantic.dev/2.13/v/missing' is None

tests\unit\test_cursor_tool_contract.py:47: AssertionError
_ test_missing_selector_without_cursor_still_returns_policy_error[community_thread] _

app = <starlette.applications.Starlette object at 0x000001C0F4A01D00>
tool = 'community_thread'

    @pytest.mark.parametrize("tool", REPAIRED)
    async def test_missing_selector_without_cursor_still_returns_policy_error(app, tool):
>       result = await dispatch(app, tool, {})
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_cursor_tool_contract.py:83: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

app = <starlette.applications.Starlette object at 0x000001C0F4A01D00>
tool = 'community_thread', arguments = {}

    async def dispatch(app, tool, arguments):
        context = Context(
            request_context=SimpleNamespace(request=SimpleNamespace(headers={})),
            mcp_server=app.state.mcp_server,
        )
        rejected = None
        try:
            result = await app.state.mcp_server._tool_manager.call_tool(tool, arguments, context)
        except Exception as exc:
            rejected = str(exc)
            result = None
>       assert rejected is None, f"MCP rejected a valid continuation or missing-input envelope: {rejected}"
E       AssertionError: MCP rejected a valid continuation or missing-input envelope: Error executing tool community_thread: 1 validation error for community_threadArguments
E         url
E           Field required [type=missing, input_value={}, input_type=dict]
E             For further information visit https://errors.pydantic.dev/2.13/v/missing
E       assert 'Error executing tool community_thread: 1 validation error for community_threadArguments\nurl\n  Field required [type=missing, input_value={}, input_type=dict]\n    For further information visit https://errors.pydantic.dev/2.13/v/missing' is None

tests\unit\test_cursor_tool_contract.py:47: AssertionError
_ test_invalid_cursor_without_selector_reaches_cursor_validation[deep_research] _

app = <starlette.applications.Starlette object at 0x000001C0F4A915E0>
tool = 'deep_research'

    @pytest.mark.parametrize("tool", REPAIRED)
    async def test_invalid_cursor_without_selector_reaches_cursor_validation(app, tool):
>       result = await dispatch(app, tool, {"cursor": "not-a-valid-cursor"})
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_cursor_tool_contract.py:89: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

app = <starlette.applications.Starlette object at 0x000001C0F4A915E0>
tool = 'deep_research', arguments = {'cursor': 'not-a-valid-cursor'}

    async def dispatch(app, tool, arguments):
        context = Context(
            request_context=SimpleNamespace(request=SimpleNamespace(headers={})),
            mcp_server=app.state.mcp_server,
        )
        rejected = None
        try:
            result = await app.state.mcp_server._tool_manager.call_tool(tool, arguments, context)
        except Exception as exc:
            rejected = str(exc)
            result = None
>       assert rejected is None, f"MCP rejected a valid continuation or missing-input envelope: {rejected}"
E       AssertionError: MCP rejected a valid continuation or missing-input envelope: Error executing tool deep_research: 1 validation error for deep_researchArguments
E         question
E           Field required [type=missing, input_value={'cursor': 'not-a-valid-cursor'}, input_type=dict]
E             For further information visit https://errors.pydantic.dev/2.13/v/missing
E       assert "Error executing tool deep_research: 1 validation error for deep_researchArguments\nquestion\n  Field required [type=m... 'not-a-valid-cursor'}, input_type=dict]\n    For further information visit https://errors.pydantic.dev/2.13/v/missing" is None

tests\unit\test_cursor_tool_contract.py:47: AssertionError
_ test_invalid_cursor_without_selector_reaches_cursor_validation[transcript_fetch] _

app = <starlette.applications.Starlette object at 0x000001C0F49BE720>
tool = 'transcript_fetch'

    @pytest.mark.parametrize("tool", REPAIRED)
    async def test_invalid_cursor_without_selector_reaches_cursor_validation(app, tool):
>       result = await dispatch(app, tool, {"cursor": "not-a-valid-cursor"})
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_cursor_tool_contract.py:89: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

app = <starlette.applications.Starlette object at 0x000001C0F49BE720>
tool = 'transcript_fetch', arguments = {'cursor': 'not-a-valid-cursor'}

    async def dispatch(app, tool, arguments):
        context = Context(
            request_context=SimpleNamespace(request=SimpleNamespace(headers={})),
            mcp_server=app.state.mcp_server,
        )
        rejected = None
        try:
            result = await app.state.mcp_server._tool_manager.call_tool(tool, arguments, context)
        except Exception as exc:
            rejected = str(exc)
            result = None
>       assert rejected is None, f"MCP rejected a valid continuation or missing-input envelope: {rejected}"
E       AssertionError: MCP rejected a valid continuation or missing-input envelope: Error executing tool transcript_fetch: 1 validation error for transcript_fetchArguments
E         url
E           Field required [type=missing, input_value={'cursor': 'not-a-valid-cursor'}, input_type=dict]
E             For further information visit https://errors.pydantic.dev/2.13/v/missing
E       assert "Error executing tool transcript_fetch: 1 validation error for transcript_fetchArguments\nurl\n  Field required [type=... 'not-a-valid-cursor'}, input_type=dict]\n    For further information visit https://errors.pydantic.dev/2.13/v/missing" is None

tests\unit\test_cursor_tool_contract.py:47: AssertionError
_ test_invalid_cursor_without_selector_reaches_cursor_validation[community_search] _

app = <starlette.applications.Starlette object at 0x000001C0F4A90770>
tool = 'community_search'

    @pytest.mark.parametrize("tool", REPAIRED)
    async def test_invalid_cursor_without_selector_reaches_cursor_validation(app, tool):
>       result = await dispatch(app, tool, {"cursor": "not-a-valid-cursor"})
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_cursor_tool_contract.py:89: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

app = <starlette.applications.Starlette object at 0x000001C0F4A90770>
tool = 'community_search', arguments = {'cursor': 'not-a-valid-cursor'}

    async def dispatch(app, tool, arguments):
        context = Context(
            request_context=SimpleNamespace(request=SimpleNamespace(headers={})),
            mcp_server=app.state.mcp_server,
        )
        rejected = None
        try:
            result = await app.state.mcp_server._tool_manager.call_tool(tool, arguments, context)
        except Exception as exc:
            rejected = str(exc)
            result = None
>       assert rejected is None, f"MCP rejected a valid continuation or missing-input envelope: {rejected}"
E       AssertionError: MCP rejected a valid continuation or missing-input envelope: Error executing tool community_search: 1 validation error for community_searchArguments
E         query
E           Field required [type=missing, input_value={'cursor': 'not-a-valid-cursor'}, input_type=dict]
E             For further information visit https://errors.pydantic.dev/2.13/v/missing
E       assert "Error executing tool community_search: 1 validation error for community_searchArguments\nquery\n  Field required [typ... 'not-a-valid-cursor'}, input_type=dict]\n    For further information visit https://errors.pydantic.dev/2.13/v/missing" is None

tests\unit\test_cursor_tool_contract.py:47: AssertionError
_ test_invalid_cursor_without_selector_reaches_cursor_validation[community_thread] _

app = <starlette.applications.Starlette object at 0x000001C0F461EC00>
tool = 'community_thread'

    @pytest.mark.parametrize("tool", REPAIRED)
    async def test_invalid_cursor_without_selector_reaches_cursor_validation(app, tool):
>       result = await dispatch(app, tool, {"cursor": "not-a-valid-cursor"})
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_cursor_tool_contract.py:89: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

app = <starlette.applications.Starlette object at 0x000001C0F461EC00>
tool = 'community_thread', arguments = {'cursor': 'not-a-valid-cursor'}

    async def dispatch(app, tool, arguments):
        context = Context(
            request_context=SimpleNamespace(request=SimpleNamespace(headers={})),
            mcp_server=app.state.mcp_server,
        )
        rejected = None
        try:
            result = await app.state.mcp_server._tool_manager.call_tool(tool, arguments, context)
        except Exception as exc:
            rejected = str(exc)
            result = None
>       assert rejected is None, f"MCP rejected a valid continuation or missing-input envelope: {rejected}"
E       AssertionError: MCP rejected a valid continuation or missing-input envelope: Error executing tool community_thread: 1 validation error for community_threadArguments
E         url
E           Field required [type=missing, input_value={'cursor': 'not-a-valid-cursor'}, input_type=dict]
E             For further information visit https://errors.pydantic.dev/2.13/v/missing
E       assert "Error executing tool community_thread: 1 validation error for community_threadArguments\nurl\n  Field required [type=... 'not-a-valid-cursor'}, input_type=dict]\n    For further information visit https://errors.pydantic.dev/2.13/v/missing" is None

tests\unit\test_cursor_tool_contract.py:47: AssertionError
___ test_direct_service_also_accepts_cursor_without_selector[deep_research] ___

app = <starlette.applications.Starlette object at 0x000001C0F45F2AB0>
tool = 'deep_research'

    @pytest.mark.parametrize("tool", REPAIRED)
    async def test_direct_service_also_accepts_cursor_without_selector(app, tool):
        first = app.state.halo_service._envelope(tool, ProviderResult("contract-fixture", [
            EvidenceItem(url="https://example.org/research", retrieved_at="2026-09-03T03:00:00Z", content="evidence " * 500)
        ]), 2000)
        rejected = None
        try:
            resumed = await getattr(app.state.halo_service, tool)(cursor=first["page"]["next_cursor"], max_chars=2000)
        except TypeError as exc:
            rejected = str(exc)
            resumed = None
>       assert rejected is None, f"Service still requires an irrelevant seed argument: {rejected}"
E       AssertionError: Service still requires an irrelevant seed argument: HaloService.deep_research() missing 1 required positional argument: 'question'
E       assert "HaloService.deep_research() missing 1 required positional argument: 'question'" is None

tests\unit\test_cursor_tool_contract.py:104: AssertionError
_ test_direct_service_also_accepts_cursor_without_selector[transcript_fetch] __

app = <starlette.applications.Starlette object at 0x000001C0F45B8DA0>
tool = 'transcript_fetch'

    @pytest.mark.parametrize("tool", REPAIRED)
    async def test_direct_service_also_accepts_cursor_without_selector(app, tool):
        first = app.state.halo_service._envelope(tool, ProviderResult("contract-fixture", [
            EvidenceItem(url="https://example.org/research", retrieved_at="2026-09-03T03:00:00Z", content="evidence " * 500)
        ]), 2000)
        rejected = None
        try:
            resumed = await getattr(app.state.halo_service, tool)(cursor=first["page"]["next_cursor"], max_chars=2000)
        except TypeError as exc:
            rejected = str(exc)
            resumed = None
>       assert rejected is None, f"Service still requires an irrelevant seed argument: {rejected}"
E       AssertionError: Service still requires an irrelevant seed argument: HaloService.transcript_fetch() missing 1 required positional argument: 'url'
E       assert "HaloService.transcript_fetch() missing 1 required positional argument: 'url'" is None

tests\unit\test_cursor_tool_contract.py:104: AssertionError
_ test_direct_service_also_accepts_cursor_without_selector[community_search] __

app = <starlette.applications.Starlette object at 0x000001C0F4619550>
tool = 'community_search'

    @pytest.mark.parametrize("tool", REPAIRED)
    async def test_direct_service_also_accepts_cursor_without_selector(app, tool):
        first = app.state.halo_service._envelope(tool, ProviderResult("contract-fixture", [
            EvidenceItem(url="https://example.org/research", retrieved_at="2026-09-03T03:00:00Z", content="evidence " * 500)
        ]), 2000)
        rejected = None
        try:
            resumed = await getattr(app.state.halo_service, tool)(cursor=first["page"]["next_cursor"], max_chars=2000)
        except TypeError as exc:
            rejected = str(exc)
            resumed = None
>       assert rejected is None, f"Service still requires an irrelevant seed argument: {rejected}"
E       AssertionError: Service still requires an irrelevant seed argument: HaloService.community_search() missing 1 required positional argument: 'query'
E       assert "HaloService.community_search() missing 1 required positional argument: 'query'" is None

tests\unit\test_cursor_tool_contract.py:104: AssertionError
_ test_direct_service_also_accepts_cursor_without_selector[community_thread] __

app = <starlette.applications.Starlette object at 0x000001C0F4764980>
tool = 'community_thread'

    @pytest.mark.parametrize("tool", REPAIRED)
    async def test_direct_service_also_accepts_cursor_without_selector(app, tool):
        first = app.state.halo_service._envelope(tool, ProviderResult("contract-fixture", [
            EvidenceItem(url="https://example.org/research", retrieved_at="2026-09-03T03:00:00Z", content="evidence " * 500)
        ]), 2000)
        rejected = None
        try:
            resumed = await getattr(app.state.halo_service, tool)(cursor=first["page"]["next_cursor"], max_chars=2000)
        except TypeError as exc:
            rejected = str(exc)
            resumed = None
>       assert rejected is None, f"Service still requires an irrelevant seed argument: {rejected}"
E       AssertionError: Service still requires an irrelevant seed argument: HaloService.community_thread() missing 1 required positional argument: 'url'
E       assert "HaloService.community_thread() missing 1 required positional argument: 'url'" is None

tests\unit\test_cursor_tool_contract.py:104: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_cursor_tool_contract.py::test_schema_does_not_require_original_selector_for_continuation[deep_research]
FAILED tests/unit/test_cursor_tool_contract.py::test_schema_does_not_require_original_selector_for_continuation[transcript_fetch]
FAILED tests/unit/test_cursor_tool_contract.py::test_schema_does_not_require_original_selector_for_continuation[community_search]
FAILED tests/unit/test_cursor_tool_contract.py::test_schema_does_not_require_original_selector_for_continuation[community_thread]
FAILED tests/unit/test_cursor_tool_contract.py::test_cursor_only_dispatch_returns_all_retained_evidence_for_each_reader[deep_research]
FAILED tests/unit/test_cursor_tool_contract.py::test_cursor_only_dispatch_returns_all_retained_evidence_for_each_reader[transcript_fetch]
FAILED tests/unit/test_cursor_tool_contract.py::test_cursor_only_dispatch_returns_all_retained_evidence_for_each_reader[community_search]
FAILED tests/unit/test_cursor_tool_contract.py::test_cursor_only_dispatch_returns_all_retained_evidence_for_each_reader[community_thread]
FAILED tests/unit/test_cursor_tool_contract.py::test_missing_selector_without_cursor_still_returns_policy_error[deep_research]
FAILED tests/unit/test_cursor_tool_contract.py::test_missing_selector_without_cursor_still_returns_policy_error[transcript_fetch]
FAILED tests/unit/test_cursor_tool_contract.py::test_missing_selector_without_cursor_still_returns_policy_error[community_search]
FAILED tests/unit/test_cursor_tool_contract.py::test_missing_selector_without_cursor_still_returns_policy_error[community_thread]
FAILED tests/unit/test_cursor_tool_contract.py::test_invalid_cursor_without_selector_reaches_cursor_validation[deep_research]
FAILED tests/unit/test_cursor_tool_contract.py::test_invalid_cursor_without_selector_reaches_cursor_validation[transcript_fetch]
FAILED tests/unit/test_cursor_tool_contract.py::test_invalid_cursor_without_selector_reaches_cursor_validation[community_search]
FAILED tests/unit/test_cursor_tool_contract.py::test_invalid_cursor_without_selector_reaches_cursor_validation[community_thread]
FAILED tests/unit/test_cursor_tool_contract.py::test_direct_service_also_accepts_cursor_without_selector[deep_research]
FAILED tests/unit/test_cursor_tool_contract.py::test_direct_service_also_accepts_cursor_without_selector[transcript_fetch]
FAILED tests/unit/test_cursor_tool_contract.py::test_direct_service_also_accepts_cursor_without_selector[community_search]
FAILED tests/unit/test_cursor_tool_contract.py::test_direct_service_also_accepts_cursor_without_selector[community_thread]
20 failed, 9 passed in 3.50s

```

### First targeted run (original output truncated by tool)

Command:

```powershell
uv run --locked ruff format src/halo_research_gateway/app.py src/halo_research_gateway/service.py tests/unit/test_cursor_tool_contract.py
uv run --locked pytest -q tests/unit/test_cursor_tool_contract.py tests/unit/test_transcript_community.py tests/unit/test_deep_research.py tests/unit/test_result_retention.py
```

```text
Warning: truncated output (original token count: 2994)
Total output lines: 213

2 files reformatted, 1 file left unchanged
FFFF...............................................................      [100%]
================================== FAILURES ===================================
_ test_schema_does_not_require_original_selector_for_continuation[deep_research] _

app = <starlette.applications.Starlette object at 0x0000020E3DF61CA0>
tool = 'deep_research'

    @pytest.mark.parametrize("tool", REPAIRED)
    async def test_schema_does_not_require_original_selector_for_continuation(app, tool):
        definitions = {entry.name: entry for entry in await app.state.mcp_server.list_tools()}
        selector, _ = REPAIRED[tool]
>       assert selector not in definitions[tool].inputSchema.get("required", []), (
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            f"{tool} advertises a cursor but requires {selector} before dispatch"
        )

tests\unit\test_cursor_tool_contract.py:68: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = Tool(name='deep_research', title=None, description='Collect a bounded multi-source evidence packet; returns evidence, ...eep_researchArguments', 'type': 'object'}, execution=None, output_schema=None, icons=None, annotations=None, meta=None)
item = 'inputSchema'

    def __getattr__(self, item: str) -> Any:
        private_attributes = object.__getattribute__(self, '__private_attributes__')
        if item in private_attributes:
            attribute = private_attributes[item]
            if hasattr(attribute, '__get__'):
                return attribute.__get__(self, type(self))  # type: ignore
    
            try:
                # Note: self.__pydantic_private__ cannot be None if self.__private_attributes__ has items
                return self.__pydantic_private__[item]  # type: ignore
            except KeyError as exc:
                raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}') from exc
        else:
            # `__pydantic_extra__` can fail to be set if the model is not yet fully initialized.
            # See `BaseModel.__repr_args__` for more details
            try:
                pydantic_extra = object.__getattribute__(self, '__pydantic_extra__')
            except AttributeError:
                pydantic_extra = None
    
            if pydantic_extra and item in pydantic_extra:
                return pydantic_extra[item]
            else:
                if hasattr(self.__class__, item):
                    return super().__getattribute__(item)  # Raises AttributeError if appropriate
                else:
                    # this is the current error
>                   raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}')
E                   AttributeError: 'Tool' object has no attribute 'inputSchema'. Did you mean: 'input_schema'?

.venv\Lib\site-packages\pydantic\main.py:1042: AttributeError
_ test_schema_does_not_require_original_selector_for_continuation[transcript_fetch] _

app = <starlette.applications.Starlette object at 0x0000020E3E2B0770>
tool = 'transcript_fetch'

    @pytest.mark.parametrize("tool", REPAIRED)
    async def test_schema_does_not_require_original_selector_for_continuation(app, tool):
        definitions = {entry.name: entry for entry in await app.state.mcp_server.list_tools()}
        selector, _ = REPAIRED[tool]
>       assert selector not in definitions[tool].inputSchema.get("required", []), (
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            f"{tool} advertises a cursor but requires {selector} before dispatch"
        )

tests\unit\test_cursor_tool_contract.py:68: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = Tool(name='transcript_fetch', title=None, description='Retrieve public captions or transcript text for a known media U...script_fetchArguments', 'type': 'object'}, execution=None, output_schema=None, icons=None, annotations=None, meta=None)
item = 'inputSchema'

    def __getattr__(self, item: str) -> Any:
        private_attributes = object.__getattribute__(self, '__private_attributes__')
        if item in private_attributes:
            attribute = private_attributes[item]
            if hasattr(attribute, '__get__'):
                return attribute.__get_…794 tokens truncated…    else:
            # `__pydantic_extra__` can fail to be set if the model is not yet fully initialized.
            # See `BaseModel.__repr_args__` for more details
            try:
                pydantic_extra = object.__getattribute__(self, '__pydantic_extra__')
            except AttributeError:
                pydantic_extra = None
    
            if pydantic_extra and item in pydantic_extra:
                return pydantic_extra[item]
            else:
                if hasattr(self.__class__, item):
                    return super().__getattribute__(item)  # Raises AttributeError if appropriate
                else:
                    # this is the current error
>                   raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}')
E                   AttributeError: 'Tool' object has no attribute 'inputSchema'. Did you mean: 'input_schema'?

.venv\Lib\site-packages\pydantic\main.py:1042: AttributeError
_ test_schema_does_not_require_original_selector_for_continuation[community_thread] _

app = <starlette.applications.Starlette object at 0x0000020E3E7A4C80>
tool = 'community_thread'

    @pytest.mark.parametrize("tool", REPAIRED)
    async def test_schema_does_not_require_original_selector_for_continuation(app, tool):
        definitions = {entry.name: entry for entry in await app.state.mcp_server.list_tools()}
        selector, _ = REPAIRED[tool]
>       assert selector not in definitions[tool].inputSchema.get("required", []), (
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            f"{tool} advertises a cursor but requires {selector} before dispatch"
        )

tests\unit\test_cursor_tool_contract.py:68: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = Tool(name='community_thread', title=None, description='Read one public community discussion thread; Reddit routes to r...unity_threadArguments', 'type': 'object'}, execution=None, output_schema=None, icons=None, annotations=None, meta=None)
item = 'inputSchema'

    def __getattr__(self, item: str) -> Any:
        private_attributes = object.__getattribute__(self, '__private_attributes__')
        if item in private_attributes:
            attribute = private_attributes[item]
            if hasattr(attribute, '__get__'):
                return attribute.__get__(self, type(self))  # type: ignore
    
            try:
                # Note: self.__pydantic_private__ cannot be None if self.__private_attributes__ has items
                return self.__pydantic_private__[item]  # type: ignore
            except KeyError as exc:
                raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}') from exc
        else:
            # `__pydantic_extra__` can fail to be set if the model is not yet fully initialized.
            # See `BaseModel.__repr_args__` for more details
            try:
                pydantic_extra = object.__getattribute__(self, '__pydantic_extra__')
            except AttributeError:
                pydantic_extra = None
    
            if pydantic_extra and item in pydantic_extra:
                return pydantic_extra[item]
            else:
                if hasattr(self.__class__, item):
                    return super().__getattribute__(item)  # Raises AttributeError if appropriate
                else:
                    # this is the current error
>                   raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}')
E                   AttributeError: 'Tool' object has no attribute 'inputSchema'. Did you mean: 'input_schema'?

.venv\Lib\site-packages\pydantic\main.py:1042: AttributeError
=========================== short test summary info ===========================
FAILED tests/unit/test_cursor_tool_contract.py::test_schema_does_not_require_original_selector_for_continuation[deep_research]
FAILED tests/unit/test_cursor_tool_contract.py::test_schema_does_not_require_original_selector_for_continuation[transcript_fetch]
FAILED tests/unit/test_cursor_tool_contract.py::test_schema_does_not_require_original_selector_for_continuation[community_search]
FAILED tests/unit/test_cursor_tool_contract.py::test_schema_does_not_require_original_selector_for_continuation[community_thread]
4 failed, 63 passed in 5.72s

```

### Complete unchanged rerun of schema-test errors

Command:

```powershell
uv run --locked pytest -q tests/unit/test_cursor_tool_contract.py tests/unit/test_transcript_community.py tests/unit/test_deep_research.py tests/unit/test_result_retention.py
```

```text
FFFF...............................................................      [100%]
================================== FAILURES ===================================
_ test_schema_does_not_require_original_selector_for_continuation[deep_research] _

app = <starlette.applications.Starlette object at 0x0000022DF9197C20>
tool = 'deep_research'

    @pytest.mark.parametrize("tool", REPAIRED)
    async def test_schema_does_not_require_original_selector_for_continuation(app, tool):
        definitions = {entry.name: entry for entry in await app.state.mcp_server.list_tools()}
        selector, _ = REPAIRED[tool]
>       assert selector not in definitions[tool].inputSchema.get("required", []), (
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            f"{tool} advertises a cursor but requires {selector} before dispatch"
        )

tests\unit\test_cursor_tool_contract.py:68: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = Tool(name='deep_research', title=None, description='Collect a bounded multi-source evidence packet; returns evidence, ...eep_researchArguments', 'type': 'object'}, execution=None, output_schema=None, icons=None, annotations=None, meta=None)
item = 'inputSchema'

    def __getattr__(self, item: str) -> Any:
        private_attributes = object.__getattribute__(self, '__private_attributes__')
        if item in private_attributes:
            attribute = private_attributes[item]
            if hasattr(attribute, '__get__'):
                return attribute.__get__(self, type(self))  # type: ignore
    
            try:
                # Note: self.__pydantic_private__ cannot be None if self.__private_attributes__ has items
                return self.__pydantic_private__[item]  # type: ignore
            except KeyError as exc:
                raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}') from exc
        else:
            # `__pydantic_extra__` can fail to be set if the model is not yet fully initialized.
            # See `BaseModel.__repr_args__` for more details
            try:
                pydantic_extra = object.__getattribute__(self, '__pydantic_extra__')
            except AttributeError:
                pydantic_extra = None
    
            if pydantic_extra and item in pydantic_extra:
                return pydantic_extra[item]
            else:
                if hasattr(self.__class__, item):
                    return super().__getattribute__(item)  # Raises AttributeError if appropriate
                else:
                    # this is the current error
>                   raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}')
E                   AttributeError: 'Tool' object has no attribute 'inputSchema'. Did you mean: 'input_schema'?

.venv\Lib\site-packages\pydantic\main.py:1042: AttributeError
_ test_schema_does_not_require_original_selector_for_continuation[transcript_fetch] _

app = <starlette.applications.Starlette object at 0x0000022DF91EE420>
tool = 'transcript_fetch'

    @pytest.mark.parametrize("tool", REPAIRED)
    async def test_schema_does_not_require_original_selector_for_continuation(app, tool):
        definitions = {entry.name: entry for entry in await app.state.mcp_server.list_tools()}
        selector, _ = REPAIRED[tool]
>       assert selector not in definitions[tool].inputSchema.get("required", []), (
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            f"{tool} advertises a cursor but requires {selector} before dispatch"
        )

tests\unit\test_cursor_tool_contract.py:68: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = Tool(name='transcript_fetch', title=None, description='Retrieve public captions or transcript text for a known media U...script_fetchArguments', 'type': 'object'}, execution=None, output_schema=None, icons=None, annotations=None, meta=None)
item = 'inputSchema'

    def __getattr__(self, item: str) -> Any:
        private_attributes = object.__getattribute__(self, '__private_attributes__')
        if item in private_attributes:
            attribute = private_attributes[item]
            if hasattr(attribute, '__get__'):
                return attribute.__get__(self, type(self))  # type: ignore
    
            try:
                # Note: self.__pydantic_private__ cannot be None if self.__private_attributes__ has items
                return self.__pydantic_private__[item]  # type: ignore
            except KeyError as exc:
                raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}') from exc
        else:
            # `__pydantic_extra__` can fail to be set if the model is not yet fully initialized.
            # See `BaseModel.__repr_args__` for more details
            try:
                pydantic_extra = object.__getattribute__(self, '__pydantic_extra__')
            except AttributeError:
                pydantic_extra = None
    
            if pydantic_extra and item in pydantic_extra:
                return pydantic_extra[item]
            else:
                if hasattr(self.__class__, item):
                    return super().__getattribute__(item)  # Raises AttributeError if appropriate
                else:
                    # this is the current error
>                   raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}')
E                   AttributeError: 'Tool' object has no attribute 'inputSchema'. Did you mean: 'input_schema'?

.venv\Lib\site-packages\pydantic\main.py:1042: AttributeError
_ test_schema_does_not_require_original_selector_for_continuation[community_search] _

app = <starlette.applications.Starlette object at 0x0000022DF92BDA90>
tool = 'community_search'

    @pytest.mark.parametrize("tool", REPAIRED)
    async def test_schema_does_not_require_original_selector_for_continuation(app, tool):
        definitions = {entry.name: entry for entry in await app.state.mcp_server.list_tools()}
        selector, _ = REPAIRED[tool]
>       assert selector not in definitions[tool].inputSchema.get("required", []), (
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            f"{tool} advertises a cursor but requires {selector} before dispatch"
        )

tests\unit\test_cursor_tool_contract.py:68: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = Tool(name='community_search', title=None, description='Search public technical discussions outside Reddit.', input_sch...unity_searchArguments', 'type': 'object'}, execution=None, output_schema=None, icons=None, annotations=None, meta=None)
item = 'inputSchema'

    def __getattr__(self, item: str) -> Any:
        private_attributes = object.__getattribute__(self, '__private_attributes__')
        if item in private_attributes:
            attribute = private_attributes[item]
            if hasattr(attribute, '__get__'):
                return attribute.__get__(self, type(self))  # type: ignore
    
            try:
                # Note: self.__pydantic_private__ cannot be None if self.__private_attributes__ has items
                return self.__pydantic_private__[item]  # type: ignore
            except KeyError as exc:
                raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}') from exc
        else:
            # `__pydantic_extra__` can fail to be set if the model is not yet fully initialized.
            # See `BaseModel.__repr_args__` for more details
            try:
                pydantic_extra = object.__getattribute__(self, '__pydantic_extra__')
            except AttributeError:
                pydantic_extra = None
    
            if pydantic_extra and item in pydantic_extra:
                return pydantic_extra[item]
            else:
                if hasattr(self.__class__, item):
                    return super().__getattribute__(item)  # Raises AttributeError if appropriate
                else:
                    # this is the current error
>                   raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}')
E                   AttributeError: 'Tool' object has no attribute 'inputSchema'. Did you mean: 'input_schema'?

.venv\Lib\site-packages\pydantic\main.py:1042: AttributeError
_ test_schema_does_not_require_original_selector_for_continuation[community_thread] _

app = <starlette.applications.Starlette object at 0x0000022DF9305100>
tool = 'community_thread'

    @pytest.mark.parametrize("tool", REPAIRED)
    async def test_schema_does_not_require_original_selector_for_continuation(app, tool):
        definitions = {entry.name: entry for entry in await app.state.mcp_server.list_tools()}
        selector, _ = REPAIRED[tool]
>       assert selector not in definitions[tool].inputSchema.get("required", []), (
                               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            f"{tool} advertises a cursor but requires {selector} before dispatch"
        )

tests\unit\test_cursor_tool_contract.py:68: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = Tool(name='community_thread', title=None, description='Read one public community discussion thread; Reddit routes to r...unity_threadArguments', 'type': 'object'}, execution=None, output_schema=None, icons=None, annotations=None, meta=None)
item = 'inputSchema'

    def __getattr__(self, item: str) -> Any:
        private_attributes = object.__getattribute__(self, '__private_attributes__')
        if item in private_attributes:
            attribute = private_attributes[item]
            if hasattr(attribute, '__get__'):
                return attribute.__get__(self, type(self))  # type: ignore
    
            try:
                # Note: self.__pydantic_private__ cannot be None if self.__private_attributes__ has items
                return self.__pydantic_private__[item]  # type: ignore
            except KeyError as exc:
                raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}') from exc
        else:
            # `__pydantic_extra__` can fail to be set if the model is not yet fully initialized.
            # See `BaseModel.__repr_args__` for more details
            try:
                pydantic_extra = object.__getattribute__(self, '__pydantic_extra__')
            except AttributeError:
                pydantic_extra = None
    
            if pydantic_extra and item in pydantic_extra:
                return pydantic_extra[item]
            else:
                if hasattr(self.__class__, item):
                    return super().__getattribute__(item)  # Raises AttributeError if appropriate
                else:
                    # this is the current error
>                   raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}')
E                   AttributeError: 'Tool' object has no attribute 'inputSchema'. Did you mean: 'input_schema'?

.venv\Lib\site-packages\pydantic\main.py:1042: AttributeError
=========================== short test summary info ===========================
FAILED tests/unit/test_cursor_tool_contract.py::test_schema_does_not_require_original_selector_for_continuation[deep_research]
FAILED tests/unit/test_cursor_tool_contract.py::test_schema_does_not_require_original_selector_for_continuation[transcript_fetch]
FAILED tests/unit/test_cursor_tool_contract.py::test_schema_does_not_require_original_selector_for_continuation[community_search]
FAILED tests/unit/test_cursor_tool_contract.py::test_schema_does_not_require_original_selector_for_continuation[community_thread]
4 failed, 63 passed in 5.31s

```

### Correct schema assertion RED against original app signatures

Command:

```powershell
uv run --locked pytest -q tests/unit/test_cursor_tool_contract.py -k schema
```

```text
FFFF                                                                     [100%]
================================== FAILURES ===================================
_ test_schema_does_not_require_original_selector_for_continuation[deep_research] _

app = <starlette.applications.Starlette object at 0x000002254E37F7A0>
tool = 'deep_research'

    @pytest.mark.parametrize("tool", REPAIRED)
    async def test_schema_does_not_require_original_selector_for_continuation(app, tool):
        definitions = {entry.name: entry for entry in await app.state.mcp_server.list_tools()}
        selector, _ = REPAIRED[tool]
>       assert selector not in definitions[tool].input_schema.get("required", []), (
            f"{tool} advertises a cursor but requires {selector} before dispatch"
        )
E       AssertionError: deep_research advertises a cursor but requires question before dispatch
E       assert 'question' not in ['question']
E        +  where ['question'] = <built-in method get of dict object at 0x000002254E433FC0>('required', [])
E        +    where <built-in method get of dict object at 0x000002254E433FC0> = {'properties': {'question': {'title': 'Question', 'type': 'string'}, 'seed_urls': {'anyOf': [{'items': {'type': 'strin...None, 'title': 'Exclude Domains'}, ...}, 'required': ['question'], 'title': 'deep_researchArguments', 'type': 'object'}.get
E        +      where {'properties': {'question': {'title': 'Question', 'type': 'string'}, 'seed_urls': {'anyOf': [{'items': {'type': 'strin...None, 'title': 'Exclude Domains'}, ...}, 'required': ['question'], 'title': 'deep_researchArguments', 'type': 'object'} = Tool(name='deep_research', title=None, description='Collect a bounded multi-source evidence packet; returns evidence, ...eep_researchArguments', 'type': 'object'}, execution=None, output_schema=None, icons=None, annotations=None, meta=None).input_schema

tests\unit\test_cursor_tool_contract.py:68: AssertionError
_ test_schema_does_not_require_original_selector_for_continuation[transcript_fetch] _

app = <starlette.applications.Starlette object at 0x000002254E4D7AD0>
tool = 'transcript_fetch'

    @pytest.mark.parametrize("tool", REPAIRED)
    async def test_schema_does_not_require_original_selector_for_continuation(app, tool):
        definitions = {entry.name: entry for entry in await app.state.mcp_server.list_tools()}
        selector, _ = REPAIRED[tool]
>       assert selector not in definitions[tool].input_schema.get("required", []), (
            f"{tool} advertises a cursor but requires {selector} before dispatch"
        )
E       AssertionError: transcript_fetch advertises a cursor but requires url before dispatch
E       assert 'url' not in ['url']
E        +  where ['url'] = <built-in method get of dict object at 0x000002254E3E9240>('required', [])
E        +    where <built-in method get of dict object at 0x000002254E3E9240> = {'properties': {'url': {'title': 'Url', 'type': 'string'}, 'language': {'anyOf': [{'type': 'string'}, {'type': 'null'}...fault': None, 'title': 'Max Chars'}, ...}, 'required': ['url'], 'title': 'transcript_fetchArguments', 'type': 'object'}.get
E        +      where {'properties': {'url': {'title': 'Url', 'type': 'string'}, 'language': {'anyOf': [{'type': 'string'}, {'type': 'null'}...fault': None, 'title': 'Max Chars'}, ...}, 'required': ['url'], 'title': 'transcript_fetchArguments', 'type': 'object'} = Tool(name='transcript_fetch', title=None, description='Retrieve public captions or transcript text for a known media U...script_fetchArguments', 'type': 'object'}, execution=None, output_schema=None, icons=None, annotations=None, meta=None).input_schema

tests\unit\test_cursor_tool_contract.py:68: AssertionError
_ test_schema_does_not_require_original_selector_for_continuation[community_search] _

app = <starlette.applications.Starlette object at 0x000002254E511CA0>
tool = 'community_search'

    @pytest.mark.parametrize("tool", REPAIRED)
    async def test_schema_does_not_require_original_selector_for_continuation(app, tool):
        definitions = {entry.name: entry for entry in await app.state.mcp_server.list_tools()}
        selector, _ = REPAIRED[tool]
>       assert selector not in definitions[tool].input_schema.get("required", []), (
            f"{tool} advertises a cursor but requires {selector} before dispatch"
        )
E       AssertionError: community_search advertises a cursor but requires query before dispatch
E       assert 'query' not in ['query']
E        +  where ['query'] = <built-in method get of dict object at 0x000002254E4CCA40>('required', [])
E        +    where <built-in method get of dict object at 0x000002254E4CCA40> = {'properties': {'query': {'title': 'Query', 'type': 'string'}, 'sources': {'anyOf': [{'items': {'type': 'string'}, 'ty... None, 'title': 'Freshness Days'}, ...}, 'required': ['query'], 'title': 'community_searchArguments', 'type': 'object'}.get
E        +      where {'properties': {'query': {'title': 'Query', 'type': 'string'}, 'sources': {'anyOf': [{'items': {'type': 'string'}, 'ty... None, 'title': 'Freshness Days'}, ...}, 'required': ['query'], 'title': 'community_searchArguments', 'type': 'object'} = Tool(name='community_search', title=None, description='Search public technical discussions outside Reddit.', input_sch...unity_searchArguments', 'type': 'object'}, execution=None, output_schema=None, icons=None, annotations=None, meta=None).input_schema

tests\unit\test_cursor_tool_contract.py:68: AssertionError
_ test_schema_does_not_require_original_selector_for_continuation[community_thread] _

app = <starlette.applications.Starlette object at 0x000002254E5A8EC0>
tool = 'community_thread'

    @pytest.mark.parametrize("tool", REPAIRED)
    async def test_schema_does_not_require_original_selector_for_continuation(app, tool):
        definitions = {entry.name: entry for entry in await app.state.mcp_server.list_tools()}
        selector, _ = REPAIRED[tool]
>       assert selector not in definitions[tool].input_schema.get("required", []), (
            f"{tool} advertises a cursor but requires {selector} before dispatch"
        )
E       AssertionError: community_thread advertises a cursor but requires url before dispatch
E       assert 'url' not in ['url']
E        +  where ['url'] = <built-in method get of dict object at 0x000002254E62CF40>('required', [])
E        +    where <built-in method get of dict object at 0x000002254E62CF40> = {'properties': {'url': {'title': 'Url', 'type': 'string'}, 'max_replies': {'default': 40, 'title': 'Max Replies', 'typ...fault': None, 'title': 'Max Chars'}, ...}, 'required': ['url'], 'title': 'community_threadArguments', 'type': 'object'}.get
E        +      where {'properties': {'url': {'title': 'Url', 'type': 'string'}, 'max_replies': {'default': 40, 'title': 'Max Replies', 'typ...fault': None, 'title': 'Max Chars'}, ...}, 'required': ['url'], 'title': 'community_threadArguments', 'type': 'object'} = Tool(name='community_thread', title=None, description='Read one public community discussion thread; Reddit routes to r...unity_threadArguments', 'type': 'object'}, execution=None, output_schema=None, icons=None, annotations=None, meta=None).input_schema

tests\unit\test_cursor_tool_contract.py:68: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_cursor_tool_contract.py::test_schema_does_not_require_original_selector_for_continuation[deep_research]
FAILED tests/unit/test_cursor_tool_contract.py::test_schema_does_not_require_original_selector_for_continuation[transcript_fetch]
FAILED tests/unit/test_cursor_tool_contract.py::test_schema_does_not_require_original_selector_for_continuation[community_search]
FAILED tests/unit/test_cursor_tool_contract.py::test_schema_does_not_require_original_selector_for_continuation[community_thread]
4 failed, 25 deselected in 1.24s

```

### Final targeted GREEN

Command:

```powershell
uv run --locked pytest -q tests/unit/test_cursor_tool_contract.py tests/unit/test_transcript_community.py tests/unit/test_deep_research.py tests/unit/test_result_retention.py
```

```text
...................................................................      [100%]
67 passed in 5.83s

```

### Full product gate

Command:

```powershell
pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Commit
```

```text
[GATE] lock check
Resolved 130 packages in 1ms
[GATE] format
91 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
.................................................
```

```text
....................... [ 20%]
........................................................................ [ 41%]
................................................
```

```text
........................ [ 62%]
........................................................................ [ 83%]
.......................................................                  [100%]
343 passed in 74.63s (0:01:14)
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Commit)

```

### Initial tracked-script lint findings

Command:

```powershell
uv run --locked ruff check --fix tests/acceptance/search_fallback_native_live.py tests/acceptance/github_mcp_native_live.py
uv run --locked ruff format tests/acceptance/search_fallback_native_live.py tests/acceptance/github_mcp_native_live.py
uv run --locked ruff check src tests
```

```text
ASYNC240 Async functions should not use pathlib.Path methods, use trio.Path or anyio.path
  --> tests\acceptance\github_mcp_native_live.py:38:21
   |
36 |         connections = ConnectionStore(database, root / "vault")
37 |         connections.create("GitHub", "Disposable authenticated public-source canary", "token", {"token": token})
38 |         for path in root.rglob("*"):
   |                     ^^^^^^^^^^
39 |             if path.is_file():
40 |                 assert token.encode() not in path.read_bytes(), "Credential persisted without encryption"
   |

ASYNC240 Async functions should not use pathlib.Path methods, use trio.Path or anyio.path
   --> tests\acceptance\github_mcp_native_live.py:154:64
    |
152 |             assert token.encode() not in stdout, "Credential found in native Gateway log"
153 |             print(json.dumps({"owned_native_process_stopped": process.returncode is not None}), flush=True)
154 |     print(json.dumps({"temporary_vault_and_state_removed": not root.exists()}), flush=True)
    |                                                                ^^^^^^^^^^^
155 |
156 | if __name__ == "__main__":
    |

Found 4 errors (2 fixed, 2 remaining).
2 files reformatted
ASYNC240 Async functions should not use pathlib.Path methods, use trio.Path or anyio.path
  --> tests\acceptance\github_mcp_native_live.py:39:21
   |
37 |         connections = ConnectionStore(database, root / "vault")
38 |         connections.create("GitHub", "Disposable authenticated public-source canary", "token", {"token": token})
39 |         for path in root.rglob("*"):
   |                     ^^^^^^^^^^
40 |             if path.is_file():
41 |                 assert token.encode() not in path.read_bytes(), "Credential persisted without encryption"
   |

ASYNC240 Async functions should not use pathlib.Path methods, use trio.Path or anyio.path
   --> tests\acceptance\github_mcp_native_live.py:221:64
    |
219 |             assert token.encode() not in stdout, "Credential found in native Gateway log"
220 |             print(json.dumps({"owned_native_process_stopped": process.returncode is not None}), flush=True)
221 |     print(json.dumps({"temporary_vault_and_state_removed": not root.exists()}), flush=True)
    |                                                                ^^^^^^^^^^^

Found 2 errors.

```

### Final tracked native live acceptance

Command:

```powershell
uv run --locked ruff format tests/acceptance/github_mcp_native_live.py
uv run --locked ruff check src tests
if($LASTEXITCODE){exit $LASTEXITCODE}
uv run --locked python tests/acceptance/search_fallback_native_live.py
if($LASTEXITCODE){exit $LASTEXITCODE}
uv run --locked python tests/acceptance/github_mcp_native_live.py
```

```text
1 file left unchanged
All checks passed!
{"case": "primary_attempt", "provider": "exa-anonymous", "urls": ["https://docs.python.org/3/library/asyncio-task.html", "https://docs.python.org/release/3.11.0/library/asyncio-task.html", "https://docs.python.org/release/3.12.1/library/asyncio-task.html"], "pages": 34, "warnings": ["RESULT_TRUNCATED"], "exa_ledger": {"window": "2026-09-03", "requests": 1, "consecutive_429": 0, "circuit": "closed", "circuit_until": null}}
{"case": "quota_induced_real_ddgs_fallback", "provider": "ddgs-accountless", "urls": ["https://docs.python.org/3/library/asyncio-exceptions.html", "https://docs.python.org/3/library/asyncio-task.html", "https://docs.python.org/3/library/asyncio.html"], "pages": 2, "warnings": ["PROVIDER_FALLBACK_USED", "RESULT_TRUNCATED"], "exa_admissions_unchanged": true}
{"case": "fallback_source_read", "url": "https://docs.python.org/3/library/asyncio-exceptions.html", "chars": 2664, "sha256": "af554e59402bf4f7f84d514c21333e0e218c2190df8b7ca84a44f8e0d090932b", "pages": 1, "warnings": []}
Live native Gateway Exa admission -> quota fallback -> DDGS -> source fetch PASS
NATIVE GATEWAY OUTPUT: [09/02/26 21:55:48] INFO     StreamableHTTP      streamable_http_manager.py:148
                             session manager                                   
                             started                                           
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     HTTP Request: POST                 _client.py:1740
                             https://mcp.exa.ai/mcp?tools=web_s                
                             earch_exa,web_fetch_exa "HTTP/1.1                 
                             200 OK"                                           
                    INFO     Received session ID:        streamable_http.py:146
                             224b01ba-601f-471a-9106-028                       
                             209c09b26                                         
                    INFO     GET stream disconnected,    streamable_http.py:240
                             reconnecting in 1000ms...                         
                    INFO     HTTP Request: POST                 _client.py:1740
                             https://mcp.exa.ai/mcp?tools=web_s                
                             earch_exa,web_fetch_exa "HTTP/1.1                 
                             202 Accepted"                                     
[09/02/26 21:55:49] INFO     HTTP Request: POST                 _client.py:1740
                             https://mcp.exa.ai/mcp?tools=web_s                
                             earch_exa,web_fetch_exa "HTTP/1.1                 
                             200 OK"                                           
                    INFO     HTTP Request: POST                 _client.py:1740
                             https://mcp.exa.ai/mcp?tools=web_s                
                             earch_exa,web_fetch_exa "HTTP/1.1                 
                             200 OK"                                           
[09/02/26 21:55:50] INFO     HTTP Request: DELETE               _client.py:1740
                             https://mcp.exa.ai/mcp?tools=web_s                
                             earch_exa,web_fetch_exa "HTTP/1.1                 
                             405 Method Not Allowed"                           
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     response:                               lib.rs:429
                             https://en.wikipedia.org/w/api.php?acti           
                             on=opensearch&profile=fuzzy&limit=1&sea           
                             rch=site%3Adocs.python.org%20asyncio%20           
                             cancellation%20CancelledError%20excepti           
                             on 200                                            
                    INFO     response:                               lib.rs:429
                             https://grokipedia.com/api/typeahead?qu           
                             ery=site%3Adocs.python.org+asyncio+canc           
                             ellation+CancelledError+exception&limit           
                             =1 200                                            
[09/02/26 21:55:51] INFO     response:                               lib.rs:429
                             https://html.duckduckgo.com/html/ 200             
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     HTTP Request: GET                  _client.py:1740
                             https://docs.python.org/3/library/                
                             asyncio-exceptions.html "HTTP/1.1                 
                             200 OK"                                           
                    INFO     Terminating session: None   streamable_http.py:814

{"owned_native_process_stopped": true}
{"case": "authenticated_mcp_discussion_search", "urls": ["https://github.com/foodcoops/foodsoft/discussions/1258", "https://github.com/unclecode/crawl4ai/discussions/2118", "https://github.com/unclecode/crawl4ai/discussions/508"], "pages": 1, "warnings": ["GITHUB_RESULTS_LIMIT_REACHED"], "selected_reply_count": 19}
{"case": "authenticated_mcp_discussion_thread", "root_url": "https://github.com/unclecode/crawl4ai/discussions/508", "unique_items": 20, "depths": [0, 1], "pages": 8, "warnings": ["RESULT_TRUNCATED"], "items": {"https://github.com/unclecode/crawl4ai/discussions/508": {"depth": 0, "chars": 1225}, "https://github.com/unclecode/crawl4ai/discussions/508#discussioncomment-11897816": {"depth": 1, "chars": 731}, "https://github.com/unclecode/crawl4ai/discussions/508#discussioncomment-11897817": {"depth": 1, "chars": 317}, "https://github.com/unclecode/crawl4ai/discussions/508#discussioncomment-11897818": {"depth": 1, "chars": 7}, "https://github.com/unclecode/crawl4ai/discussions/508#discussioncomment-11897819": {"depth": 1, "chars": 621}, "https://github.com/unclecode/crawl4ai/discussions/508#discussioncomment-11897820": {"depth": 1, "chars": 804}, "https://github.com/unclecode/crawl4ai/discussions/508#discussioncomment-11897821": {"depth": 1, "chars": 682}, "https://github.com/unclecode/crawl4ai/discussions/508#discussioncomment-11897822": {"depth": 1, "chars": 2471}, "https://github.com/unclecode/crawl4ai/discussions/508#discussioncomment-11897823": {"depth": 1, "chars": 827}, "https://github.com/unclecode/crawl4ai/discussions/508#discussioncomment-11897824": {"depth": 1, "chars": 2560}, "https://github.com/unclecode/crawl4ai/discussions/508#discussioncomment-11897825": {"depth": 1, "chars": 2137}, "https://github.com/unclecode/crawl4ai/discussions/508#discussioncomment-11897826": {"depth": 1, "chars": 2233}, "https://github.com/unclecode/crawl4ai/discussions/508#discussioncomment-11897827": {"depth": 1, "chars": 1133}, "https://github.com/unclecode/crawl4ai/discussions/508#discussioncomment-11897828": {"depth": 1, "chars": 2266}, "https://github.com/unclecode/crawl4ai/discussions/508#discussioncomment-11897829": {"depth": 1, "chars": 117}, "https://github.com/unclecode/crawl4ai/discussions/508#discussioncomment-11897830": {"depth": 1, "chars": 116}, "https://github.com/unclecode/crawl4ai/discussions/508#discussioncomment-11897831": {"depth": 1, "chars": 699}, "https://github.com/unclecode/crawl4ai/discussions/508#discussioncomment-11897832": {"depth": 1, "chars": 985}, "https://github.com/unclecode/crawl4ai/discussions/508#discussioncomment-11897833": {"depth": 1, "chars": 212}, "https://github.com/unclecode/crawl4ai/discussions/508#discussioncomment-15996534": {"depth": 1, "chars": 523}}}

```

```text
{"case": "additional_discussion_nested_coverage", "root_url": "https://github.com/foodcoops/foodsoft/discussions/1258", "nested_urls": ["https://github.com/foodcoops/foodsoft/discussions/1258#discussioncomment-15340219", "https://github.com/foodcoops/foodsoft/discussions/1258#discussioncomment-15340413", "https://github.com/foodcoops/foodsoft/discussions/1258#discussioncomment-15347795", "https://github.com/foodcoops/foodsoft/discussions/1258#discussioncomment-15351402", "https://github.com/foodcoops/foodsoft/discussions/1258#discussioncomment-15351417", "https://github.com/foodcoops/foodsoft/discussions/1258#discussioncomment-15352514", "https://github.com/foodcoops/foodsoft/discussions/1258#discussioncomment-15352520", "https://github.com/foodcoops/foodsoft/discussions/1258#discussioncomment-15352551", "https://github.com/foodcoops/foodsoft/discussions/1258#discussioncomment-15355608", "https://github.com/foodcoops/foodsoft/discussions/1258#discussioncomment-15356963", "https://github.com/foodcoops/foodsoft/discussions/1258#discussioncomment-15359041", "https://github.com/foodcoops/foodsoft/discussions/1258#discussioncomment-15359061", "https://github.com/foodcoops/foodsoft/discussions/1258#discussioncomment-15362808", "https://github.com/foodcoops/foodsoft/discussions/1258#discussioncomment-15364294", "https://github.com/foodcoops/foodsoft/discussions/1258#discussioncomment-15364663", "https://github.com/foodcoops/foodsoft/discussions/1258#discussioncomment-15369336", "https://github.com/foodcoops/foodsoft/discussions/1258#discussioncomment-15369491"], "pages": 7, "warnings": ["REPLY_LIMIT_REACHED", "RESULT_TRUNCATED"]}
{"live_nested_reply_observed": true}
{"case": "authenticated_mcp_ref_pinned_document", "url": "https://github.com/microsoft/playwright/blob/e9163e238dcc3951b8cfbd45e0ebc8b6e3c4d194/README.md", "sha": "e9163e238dcc3951b8cfbd45e0ebc8b6e3c4d194", "chars": 11261, "text_sha256": "d195f41bed2845ab708a213675900fd3f80084268a637214495444a1b96e8e7a", "pages": 46, "warnings": ["GITHUB_REF_LITERAL_SEARCH", "GITHUB_REF_SCAN_LIMIT_REACHED", "RESULT_TRUNCATED"]}
{"authenticated_disk_cache_entries": 0, "temporary_connection_ready": true}
Authenticated native MCP GitHub search/thread/ref/pagination PASS
NATIVE GATEWAY OUTPUT: [09/02/26 21:55:53] INFO     StreamableHTTP      streamable_http_manager.py:148
                             session manager                                   
                             started                                           
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
[09/02/26 21:55:54] INFO     HTTP Request: POST                 _client.py:1740
                             https://api.github.com/graphql                    
                             "HTTP/1.1 200 OK"                                 
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
[09/02/26 21:55:55] INFO     HTTP Request: POST                 _client.py:1740
                             https://api.github.com/graphql                    
                             "HTTP/1.1 200 OK"                                 
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
[09/02/26 21:55:57] INFO     HTTP Request: POST                 _client.py:1740
                             https://api.github.com/graphql                    
                             "HTTP/1.1 200 OK"                                 
[09/02/26 21:55:58] INFO     HTTP Request: POST                 _client.py:1740
                             https://api.github.com/graphql                    
                             "HTTP/1.1 200 OK"                                 
                    INFO     HTTP Request: POST                 _client.py:1740
                             https://api.github.com/graphql                    
                             "HTTP/1.1 200 OK"                                 
[09/02/26 21:55:59] INFO     HTTP Request: POST                 _client.py:1740
                             https://api.github.com/graphql                    
                             "HTTP/1.1 200 OK"                                 
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     HTTP Request: GET                  _client.py:1740
                             https://api.github.com/repos/micro                
                             soft/playwright/commits/main                      
                             "HTTP/1.1 200 OK"                                 
[09/02/26 21:56:00] INFO     HTTP Request: GET                  _client.py:1740
                             https://api.github.com/repos/micro                
                             soft/playwright/git/trees/7fd81077                
                             ce3b71652f9d13489ea52f4dfd472a3b?r                
                             ecursive=1 "HTTP/1.1 200 OK"                      
                    INFO     HTTP Request: GET                  _client.py:1740
                             https://api.github.com/repos/micro                
                             soft/playwright/git/blobs/6705c323                
                             4f2074d73acdb89b02ca7d9e629dd94b                  
                             "HTTP/1.1 200 OK"                                 
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
[09/02/26 21:56:01] INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814

{"owned_native_process_stopped": true}
{"temporary_vault_and_state_removed": true}

```


