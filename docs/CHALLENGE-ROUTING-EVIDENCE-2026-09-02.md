# Challenge routing evidence - 2026-09-02

Research-only candidate based on `e99ebaf3b5e479f1a0249db6e12b5c1509be5300`.
Version stays 0.2.0; result schema 1.5, DB schema 3 and cursor layout 3 unchanged.
No new dependency, installed credential/profile or DSH configuration change.

## Outcome

Previously the registered optional providers had no caller in the crawl path;
a recognized HTTP-200 challenge page could be returned as source evidence.
Auto public crawling now connects the configured Bright Data adapter to
recognized challenge pages, and disabled/disallowed/unsolved cases fail explicitly.
Earlier good pages remain available when later pages fail or exhaust budgets.

The browser begins in standard mode. Specific challenge headers or gate titles
combined with actual challenge DOM markers trigger classification. Articles that
merely discuss CAPTCHAs, or ordinary HTTP 404/500 failures, do not themselves
activate paid retrieval. This is not universal detection of every login, paywall
or challenge provider; timeouts/stripped or novel signals can still fail generically.

Eligible fallback is public auto mode without a managed profile, recognized
sensitive URL or explicit scrolling. The requested public URL is revalidated and
must match the operator's exact allowed domain. Browser cookies, headers, passwords,
local/private targets and import profiles are not forwarded. This preserves
research authentication boundaries; it does not add general account actions.

Retrieved HTML is treated as untrusted evidence and extracted without running its
scripts. Existing page/depth/content/queue/response budgets remain. Native/API
timeouts propagate and owned browsers close. Unsolved gates, bad status/shape,
empty bodies and unmatched selectors cannot become fake successful evidence.
Metadata reports actual proxy mode/provider, not standard browsing.


## Commit-gate cache failure and repair

The first normal commit hook stopped this checkpoint with a cache failure from
base e99ebaf. No commit or push occurred. This was not dismissed as flaky:
a separate real-SQLite reader test reproduced the journal-mode collision, and
simultaneous first owners also reproduced database-is-locked. Cache construction
now prepares persistent WAL before requests and retries only SQLite BUSY during
initialization, on fresh connections within a five-second budget. Ordinary
get/put/evict/stats no longer change journal mode. Migrations remain unchanged;
existing cache/concurrency/frozen tests were not weakened. Four new cases cover
an existing reader, simultaneous first owners, a short existing transaction and
a bounded startup-lock failure. Ordinary database locks/I/O and native memory
remain possible; this is not a universal storage guarantee.

This supersedes the earlier 419-test pre-commit green result below. After the
repair, ten unchanged cache/concurrency repetitions passed and the final full
gate reports 423 tests. Counts and complete failures follow.

### Rejected first commit/push attempt

Command:

```powershell
$ErrorActionPreference='Stop'
$taskFiles=@('BUILD-MANIFEST.json','CHANGELOG.md','README.md','config/config.example.toml','docs/FINISH-PROGRESS-2026-09-02.md','docs/RESEARCH-ONLY-SCOPE.md','docs/USER-MANUAL.md','docs/implementation-status.md','docs/operations.md','skills/halo-research/references/RESEARCH-ONLY-SCOPE.md','src/halo_research_gateway/config.py','src/halo_research_gateway/providers/crawl4ai_provider.py','src/halo_research_gateway/providers/optional.py','src/halo_research_gateway/providers/paid.py','src/halo_research_gateway/service.py','docs/CHALLENGE-ROUTING-EVIDENCE-2026-09-02.md','tests/acceptance/test_challenge_native.py','tests/unit/test_challenge_routing.py','tests/unit/test_optional_budget_integrity.py','tests/unit/test_paid_response_limits.py')
git -c safe.directory=C:/Users/scott/Desktop/Code/halo-research-gateway add -- $taskFiles
if($LASTEXITCODE){throw 'Scoped staging failed.'}
git -c safe.directory=C:/Users/scott/Desktop/Code/halo-research-gateway diff --cached --check
if($LASTEXITCODE){throw 'Staged diff check failed.'}
git -c safe.directory=C:/Users/scott/Desktop/Code/halo-research-gateway commit -m "Route recognized crawl challenges through configured research retrieval"
if($LASTEXITCODE){throw 'Commit failed.'}
git -c safe.directory=C:/Users/scott/Desktop/Code/halo-research-gateway push origin main
if($LASTEXITCODE){throw 'Push failed.'}
git -c safe.directory=C:/Users/scott/Desktop/Code/halo-research-gateway rev-parse HEAD
git -c safe.directory=C:/Users/scott/Desktop/Code/halo-research-gateway status --short --branch
```

Output:

```text
warning: in the working copy of 'CHANGELOG.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'README.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'config/config.example.toml', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'docs/FINISH-PROGRESS-2026-09-02.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'docs/RESEARCH-ONLY-SCOPE.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'docs/USER-MANUAL.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'docs/implementation-status.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'docs/operations.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'skills/halo-research/references/RESEARCH-ONLY-SCOPE.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'src/halo_research_gateway/config.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'src/halo_research_gateway/providers/crawl4ai_provider.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'src/halo_research_gateway/providers/optional.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'src/halo_research_gateway/providers/paid.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'src/halo_research_gateway/service.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'docs/CHALLENGE-ROUTING-EVIDENCE-2026-09-02.md', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'tests/acceptance/test_challenge_native.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'tests/unit/test_challenge_routing.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'tests/unit/test_optional_budget_integrity.py', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'tests/unit/test_paid_response_limits.py', LF will be replaced by CRLF the next time Git touches it
[GATE] lock check
Resolved 130 packages in 2ms
[GATE] format
101 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
............................................F........................... [ 17%]
........................................................................ [ 34%]
........................................................................ [ 51%]
........................................................................ [ 68%]
........................................................................ [ 85%]
...........................................................              [100%]
================================== FAILURES ===================================
_________ test_concurrent_bounded_writers_share_one_observable_limit __________

service = <halo_research_gateway.service.HaloService object at 0x00000162CFF0C0B0>

    async def test_concurrent_bounded_writers_share_one_observable_limit(service):
        db = service.cache.db_path
        cap, samples = 5000, []

        def writer(number):
            cache = Cache(db, cap, 10000, enforce_limits=True)
            for index in range(12):
                value = service._encode_result(sample(f"{number}-{index}"))
                cache.put(f"{number}-{index}", value, 60)
                assert cache.stats()["total_compressed_bytes"] <= cap

        observer = Cache(db, cap, 10000)
        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = [pool.submit(writer, number) for number in range(6)]
            while not all(future.done() for future in futures):
                samples.append(observer.stats()["total_compressed_bytes"])
            for future in futures:
>               future.result(timeout=5)

tests\unit\test_cache_runtime_limits.py:269:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
..\..\..\AppData\Local\Programs\Python\Python312\Lib\concurrent\futures\_base.py:449: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
..\..\..\AppData\Local\Programs\Python\Python312\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
..\..\..\AppData\Local\Programs\Python\Python312\Lib\concurrent\futures\thread.py:59: in run
    result = self.fn(*self.args, **self.kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\unit\test_cache_runtime_limits.py:260: in writer
    cache.put(f"{number}-{index}", value, 60)
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <halo_research_gateway.cache.Cache object at 0x00000162CFEFD0D0>
key = '0-0'
value = b'{"provider":"fixture","items":[{"title":null,"url":"https://example.org/0-0","published_at":null,"retrieved_at":"202...22ef1683845ccad489d39d6a8fe1c6be13b9919d6d0e839fd49f8943c85b075631b827fa32e48783a9b"}],"warnings":[],"available":null}'
ttl_seconds = 60

    def put(self, key: str, value: bytes, ttl_seconds: int) -> None:
        """
        Store a value in cache with TTL.

        Args:
            key: Cache key
            value: Value to store (bytes)
            ttl_seconds: Time-to-live in seconds

        Raises:
            EntryTooLargeError: If the compressed entry exceeds an admission limit
        """
        # Compress the value
        try:
            compressed_value = gzip.compress(value)
        except Exception as e:
            raise EntryTooLargeError(f"Failed to compress entry: {str(e)}") from e

        limit = min(self.entry_max_bytes, self.max_bytes) if self.enforce_limits else self.entry_max_bytes
        if len(compressed_value) > limit:
            raise EntryTooLargeError(f"Entry size {len(compressed_value)} exceeds maximum allowed {limit} bytes")

        with closing(sqlite3.connect(self.db_path)) as conn:
>           conn.execute("PRAGMA journal_mode=WAL")
E           sqlite3.OperationalError: database is locked

src\halo_research_gateway\cache.py:55: OperationalError
=========================== short test summary info ===========================
FAILED tests/unit/test_cache_runtime_limits.py::test_concurrent_bounded_writers_share_one_observable_limit
1 failed, 418 passed in 80.23s (0:01:20)
Exception: C:\Users\scott\Desktop\Code\halo-research-gateway\scripts\Invoke-QualityGate.ps1:9
Line |
   9 |  … EXITCODE -ne 0) { throw "$Name failed with exit code $LASTEXITCODE" }
     |                      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | unit and fixture tests failed with exit code 1
Exception:
Line |
   9 |  if($LASTEXITCODE){throw 'Commit failed.'}
     |                    ~~~~~~~~~~~~~~~~~~~~~~
     | Commit failed.
```

Exit code: 1.

### Cache journal assertion reproduction

Command:

```powershell
uv run --locked python -m pytest -q tests/unit/test_cache_journal_initialization.py
```

Output:

```text
FF.                                                                      [100%]
================================== FAILURES ===================================
________ test_cache_is_ready_before_another_connection_starts_reading _________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-2040/test_cache_is_ready_before_ano0')

    def test_cache_is_ready_before_another_connection_starts_reading(tmp_path):
        db = str(tmp_path / "gateway.db")
        migrate(db, str(tmp_path / "backups"))
        cache = Cache(db, 10000, 10000, enforce_limits=True)
        error = None
        with closing(sqlite3.connect(db)) as reader:
            reader.execute("BEGIN")
            reader.execute("SELECT COUNT(*) FROM cache_entries").fetchone()
            try:
                assert cache.stats()["entries"] == 0
                cache.put("source", b"readable evidence", 60)
                assert cache.get("source") == b"readable evidence"
                cache.evict()
                # A concurrent reader keeps its original snapshot until it commits.
                assert reader.execute("SELECT COUNT(*) FROM cache_entries").fetchone()[0] == 0
            except sqlite3.OperationalError as exc:
                error = str(exc)
            finally:
                reader.rollback()
>       assert error is None, f"Ordinary cache request tried to reconfigure a live database: {error}"
E       AssertionError: Ordinary cache request tried to reconfigure a live database: database is locked
E       assert 'database is locked' is None

tests\unit\test_cache_journal_initialization.py:31: AssertionError
_____ test_simultaneous_first_cache_owners_preserve_all_committed_results _____

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-2040/test_simultaneous_first_cache_0')

    def test_simultaneous_first_cache_owners_preserve_all_committed_results(tmp_path):
        db = str(tmp_path / "gateway.db")
        migrate(db, str(tmp_path / "backups"))
        start = Barrier(8)

        def owner(number):
            start.wait(timeout=5)
            cache = Cache(db, 10000, 10000, enforce_limits=True)
            cache.put(str(number), str(number).encode(), 60)
            return cache.get(str(number))

        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = [pool.submit(owner, number) for number in range(8)]
>           assert [future.result(timeout=10) for future in futures] == [str(i).encode() for i in range(8)]
                    ^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_cache_journal_initialization.py:48:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
..\..\..\AppData\Local\Programs\Python\Python312\Lib\concurrent\futures\_base.py:449: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
..\..\..\AppData\Local\Programs\Python\Python312\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
..\..\..\AppData\Local\Programs\Python\Python312\Lib\concurrent\futures\thread.py:59: in run
    result = self.fn(*self.args, **self.kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\unit\test_cache_journal_initialization.py:43: in owner
    cache.put(str(number), str(number).encode(), 60)
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <halo_research_gateway.cache.Cache object at 0x000001D60329BB00>
key = '1', value = b'1', ttl_seconds = 60

    def put(self, key: str, value: bytes, ttl_seconds: int) -> None:
        """
        Store a value in cache with TTL.

        Args:
            key: Cache key
            value: Value to store (bytes)
            ttl_seconds: Time-to-live in seconds

        Raises:
            EntryTooLargeError: If the compressed entry exceeds an admission limit
        """
        # Compress the value
        try:
            compressed_value = gzip.compress(value)
        except Exception as e:
            raise EntryTooLargeError(f"Failed to compress entry: {str(e)}") from e

        limit = min(self.entry_max_bytes, self.max_bytes) if self.enforce_limits else self.entry_max_bytes
        if len(compressed_value) > limit:
            raise EntryTooLargeError(f"Entry size {len(compressed_value)} exceeds maximum allowed {limit} bytes")

        with closing(sqlite3.connect(self.db_path)) as conn:
>           conn.execute("PRAGMA journal_mode=WAL")
E           sqlite3.OperationalError: database is locked

src\halo_research_gateway\cache.py:55: OperationalError
=========================== short test summary info ===========================
FAILED tests/unit/test_cache_journal_initialization.py::test_cache_is_ready_before_another_connection_starts_reading
FAILED tests/unit/test_cache_journal_initialization.py::test_simultaneous_first_cache_owners_preserve_all_committed_results
2 failed, 1 passed in 6.40s
```

Exit code: 1.

### Initialization deadline assertion reproduction

Command:

```powershell
uv run --locked python -m pytest -q tests/unit/test_cache_journal_initialization.py -k deadline
```

Output:

```text
F                                                                        [100%]
================================== FAILURES ===================================
________________ test_initialization_contention_has_a_deadline ________________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-2042/test_initialization_contention0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000018874A0B5F0>

    def test_initialization_contention_has_a_deadline(tmp_path, monkeypatch):
        db = str(tmp_path / "gateway.db")
        migrate(db, str(tmp_path / "backups"))
        monkeypatch.setattr(Cache, "journal_timeout_seconds", 0.05, raising=False)
        with closing(sqlite3.connect(db)) as reader:
            reader.execute("BEGIN")
            reader.execute("SELECT COUNT(*) FROM cache_entries").fetchone()
            started = time.monotonic()
>           with pytest.raises(sqlite3.OperationalError, match="locked"):
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           Failed: DID NOT RAISE OperationalError

tests\unit\test_cache_journal_initialization.py:86: Failed
=========================== short test summary info ===========================
FAILED tests/unit/test_cache_journal_initialization.py::test_initialization_contention_has_a_deadline
1 failed, 3 deselected in 0.43s
```

Exit code: 1.

### Cache and migration green

Command:

```powershell
uv run --locked ruff format src/halo_research_gateway/cache.py tests/unit/test_cache_journal_initialization.py
if ($LASTEXITCODE) { throw 'format failed' }
uv run --locked ruff check src/halo_research_gateway/cache.py tests/unit/test_cache_journal_initialization.py
if ($LASTEXITCODE) { throw 'lint failed' }
uv run --locked python -m pytest -q tests/unit/test_cache_journal_initialization.py tests/unit/test_cache_runtime_limits.py tests/unit/test_cache.py tests/unit/test_migrations.py
```

Output:

```text
2 files left unchanged
All checks passed!
........................................                                 [100%]
40 passed in 3.81s
```

Exit code: 0.

### Ten cache repetitions and final full gate

Command:

```powershell
1..10 | ForEach-Object {
    Write-Output "Cache concurrency repetition $_ of 10"
    uv run --locked python -m pytest -q tests/unit/test_cache_journal_initialization.py tests/unit/test_cache_runtime_limits.py
    if ($LASTEXITCODE) { throw "Cache concurrency repetition $_ failed" }
}
pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Full
```

Output:

```text
Cache concurrency repetition 1 of 10
...........................                                              [100%]
27 passed in 2.72s
Cache concurrency repetition 2 of 10
...........................                                              [100%]
27 passed in 3.08s
Cache concurrency repetition 3 of 10
...........................                                              [100%]
27 passed in 3.85s
Cache concurrency repetition 4 of 10
...........................                                              [100%]
27 passed in 3.17s
Cache concurrency repetition 5 of 10
...........................                                              [100%]
27 passed in 3.49s
Cache concurrency repetition 6 of 10
...........................                                              [100%]
27 passed in 3.49s
Cache concurrency repetition 7 of 10
...........................                                              [100%]
27 passed in 3.75s
Cache concurrency repetition 8 of 10
...........................                                              [100%]
27 passed in 3.34s
Cache concurrency repetition 9 of 10
...........................                                              [100%]
27 passed in 2.97s
Cache concurrency repetition 10 of 10
...........................                                              [100%]
27 passed in 2.97s
[GATE] lock check
Resolved 130 packages in 2ms
[GATE] format
102 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
........................................................................ [ 17%]
........................................................................ [ 34%]
........................................................................ [ 51%]
........................................................................ [ 68%]
........................................................................ [ 85%]
...............................................................          [100%]
423 passed in 74.00s (0:01:13)
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Full)
```

Exit code: 0.


## Post-repair native browser and process recovery verification

Re-ran the existing native challenge and cache canaries against the final cache
initialization fix. The cache test uses separate native Gateway processes, two
network MCP clients and actual public Python documentation; it verifies eviction,
retained/evicted cursors after restart, lowered limits and owned-process cleanup.
The challenge test uses the same public echo/local fake-vendor interception
described above. No installed service, DSH, personal profile or paid API changed.
SDK INFO output still appears despite ERROR configuration; retained below rather
than hidden. This is a known logging/configuration issue, not a clean-log claim.

Command:

```powershell
uv run --locked python -m pytest -q -s tests/acceptance/test_challenge_native.py
if ($LASTEXITCODE) { throw 'Native challenge routing failed' }
uv run --locked python tests/acceptance/cache_limits_native_live.py
if ($LASTEXITCODE) { throw 'Native cache recovery failed' }
```

Output:

```text
..{"native_chrome_public_header_echo": true, "native_network_mcp_clients": 2, "local_fake_vendor_requests": 1, "real_paid_requests": 0, "content_chars": 1742, "pages": 25, "cache_reuse": true, "reserved_estimated_usd": 0.02}
Native Chrome/MCP fake-vendor routing, durable budget and owned-browser cleanup PASS
.
3 passed in 7.48s
{"case": "two_native_mcp_clients_shared_cache", "unique_urls": 9, "samples": 113, "peak_compressed_bytes": 3608, "limit": 4096, "retained_entries": 2, "body_chars": 2664, "evicted_source_memory_pages": 11, "recent_source_cache_hit": true}
NATIVE GATEWAY OUTPUT: [09/02/26 23:51:36] INFO     StreamableHTTP      streamable_http_manager.py:148
                             session manager
                             started
[09/02/26 23:51:37] INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     HTTP Request: GET                  _client.py:1740
                             https://docs.python.org/3/library/
                             asyncio-exceptions.html?halo_cache
                             _case=0 "HTTP/1.1 200 OK"
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
[09/02/26 23:51:38] INFO     HTTP Request: GET                  _client.py:1740
                             https://docs.python.org/3/library/
                             asyncio-exceptions.html?halo_cache
                             _case=2 "HTTP/1.1 200 OK"
                    INFO     Terminating session: None   streamable_http.py:814
[09/02/26 23:51:39] INFO     HTTP Request: GET                  _client.py:1740
                             https://docs.python.org/3/library/
                             asyncio-exceptions.html?halo_cache
                             _case=1 "HTTP/1.1 200 OK"
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
[09/02/26 23:51:40] INFO     HTTP Request: GET                  _client.py:1740
                             https://docs.python.org/3/library/
                             asyncio-exceptions.html?halo_cache
                             _case=3 "HTTP/1.1 200 OK"
                    INFO     Terminating session: None   streamable_http.py:814
[09/02/26 23:51:41] INFO     HTTP Request: GET                  _client.py:1740
                             https://docs.python.org/3/library/
                             asyncio-exceptions.html?halo_cache
                             _case=4 "HTTP/1.1 200 OK"
                    INFO     Terminating session: None   streamable_http.py:814
[09/02/26 23:51:42] INFO     HTTP Request: GET                  _client.py:1740
                             https://docs.python.org/3/library/
                             asyncio-exceptions.html?halo_cache
                             _case=5 "HTTP/1.1 200 OK"
                    INFO     Terminating session: None   streamable_http.py:814
[09/02/26 23:51:43] INFO     HTTP Request: GET                  _client.py:1740
                             https://docs.python.org/3/library/
                             asyncio-exceptions.html?halo_cache
                             _case=6 "HTTP/1.1 200 OK"
                    INFO     Terminating session: None   streamable_http.py:814
[09/02/26 23:51:44] INFO     HTTP Request: GET                  _client.py:1740
                             https://docs.python.org/3/library/
                             asyncio-exceptions.html?halo_cache
                             _case=7 "HTTP/1.1 200 OK"
                    INFO     Terminating session: None   streamable_http.py:814
[09/02/26 23:51:45] INFO     HTTP Request: GET                  _client.py:1740
                             https://docs.python.org/3/library/
                             asyncio-exceptions.html?halo_cache
                             _case=8 "HTTP/1.1 200 OK"
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

{"case": "restart", "evicted_cursor": "CURSOR_EVICTED", "retained_cursor_identical": true, "remaining_pages": 10}
NATIVE GATEWAY OUTPUT: [09/02/26 23:51:47] INFO     StreamableHTTP      streamable_http_manager.py:148
                             session manager
                             started
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

{"case": "lowered_cache_limit", "body_preserved": true, "warning": "RESULT_NOT_CACHED_TOO_LARGE", "cache": {"entries": 0, "total_compressed_bytes": 0, "max_bytes": 100, "entry_max_bytes": 100}}
Native shared cache limit, eviction/restart and uncached evidence PASS
NATIVE GATEWAY OUTPUT: [09/02/26 23:51:48] INFO     StreamableHTTP      streamable_http_manager.py:148
                             session manager
                             started
[09/02/26 23:51:49] INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     HTTP Request: GET                  _client.py:1740
                             https://docs.python.org/3/library/
                             asyncio-exceptions.html?halo_cache
                             _case=8 "HTTP/1.1 200 OK"
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
Temporary native Gateway state removed

```

Exit code: 0.

## Vendor protocol and attribution

The documented Unlocker endpoint accepts structured JSON versus raw output and
returns status, headers and body. The adapter previously requested raw output
then unconditionally JSON-decoded it. Auto fallback now requests JSON; explicit
raw adapter calls remain supported by decoding the raw body separately.
Source: [Bright Data Unlocker API](https://docs.brightdata.com/api-reference/rest-api/unlocker/unlock-website).

The documented response does not attest the final redirect URL. This is an
inference from the returned fields, not proof that the vendor never redirects.
Results identify their requested URL, with PROXY_FINAL_URL_UNVERIFIED,
citation_url_kind=requested and final_url_verified=false. Relative links are not
resolved against an unknown final base. Vendor DNS, redirect and subresource
behavior is outside the locally verified requested-domain boundary. No live paid
vendor test or independently canonical final citation is claimed.

## Budget and transport corrections

Optional request estimates must be finite positive numbers, not booleans, zero,
negative values or non-finite floats. A configured request_cost_usd supplies the
default; zero/missing refuses automatic use while preserving old config loading.
Estimates round up to microdollars; limits round down. The existing SQLite
transaction reserves attempts/cost before dispatch. Failed/cancelled requests
retain reservations because the remote vendor may already have received them.
Stats explicitly label spend as estimated and show the per-request estimate.

These are reservations, not actual invoice reconciliation or a guaranteed
vendor-billing ceiling. The operator must set a conservative estimate and use
vendor-side controls for a hard billing cap. Installed providers remain disabled
and unused; fixture estimates are not quotes for real service pricing.

The fixed APIs stream at most 20 MiB decoded body with a 45-second total I/O
deadline including DNS. Invalid JSON/object shape fails without echoing body.
CapSolver's entire create/poll sequence has a 120-second deadline, including
requests and sleeps, with the existing 40-poll bound. It remains an adapter;
browser-token application and visible human challenge handoff are unfinished.
These are not hard native RAM/CPU-parser or all-browser-subresource guarantees.

Fresh web/local-crawl and forum requests use new cache namespaces, preventing
reuse of previously misclassified gate-page results. No historical rows, jobs,
receipts or issued cursors were deleted; a fresh request applies classification.

## Verification and scope

Read before editing: repository AGENTS/scope, coding/QA skill, cache checkpoint,
service crawl/forum/cache paths, config, optional registry, paid adapters,
crawler/HTML extractor, current tests and manual/README/operations/changelog/
implementation/finish/scope/config docs. Operator AGENTS also read for delivery.

Baseline 382 tests; pre-commit routing gate 419 tests. Added 37 unit cases across
test_challenge_routing.py (22), test_optional_budget_integrity.py (10) and
test_paid_response_limits.py (5). Existing tests remain unchanged. Full raw
RED/GREEN commands follow, including intermediate failures and the lint stop.
The later commit-gate cache failure and four added journal regressions bring
the repaired full gate to 423 tests; that failure/repair is recorded above.
Do not count passing preservation checks as assertion REDs.

Falsification covers wrong/disabled domains, sensitive/managed/local controls,
different HTTP codes, actual source versus gate content, unsolved/malformed/
empty vendor results, partial budget exhaustion, source attribution and relative
links, selector mismatch, legacy forum cache, cancellation/reservation retention,
tiny/negative/non-finite costs, streaming early-stop/close, raw responses and
the total CapSolver deadline. A final assertion caught proxy output mislabeled
as standard mode; its corrected final full/native runs are included.

Three explicit native tests ran outside the deterministic gate:
- Actual owned Chrome rejects local HTTP-200 and HTTP-403 gate fixtures.
- Actual owned Chrome loads a public HTTPBingo header echo intentionally carrying
  cf-mitigated=challenge. This is a simulated signal, not a real gate bypass.
- Two independent network MCP clients reach the real Gateway app, registry and
  Bright Data adapter; test-only transport interception sends all vendor traffic
  to a local fake HTTP API. It cannot contact the real paid API. The fixture
  verifies the actual JSON request/body, one coalesced vendor call, cache reuse,
  1742 characters across 25 bounded pages, durable 0.02 USD fixture reservation,
  refusal after service reconstruction and no remaining owned browser children.

Native Gateway HTTP ran in the test process on a disposable loopback port, not
the installed service and not a separate-process restart test. Fake credentials/
state are temporary pytest fixtures, not real accounts. Source body is clearly
fixture evidence, not factual research obtained from the echoed public URL.
No real paid API, personal profile, operator login or DSH model was used.
The final native run: three tests passed; full output below.

## Security checklist and remaining work

- Inputs validated: exact public requested URL/domain, finite positive estimate,
  selector and response shape/status/body bounds; parameterized budget SQL.
- Auth/routes: no new endpoint or model-visible action. Existing fourteen-tool
  research surface and encrypted connection mechanism retained.
- Secrets: only fake native credentials; results omit vendor secret/headers.
  Whole-repository credential-pattern/ignore scan is required before private push.
- Rendering/eval: no new script execution or unsafe rendering; provider HTML is
  untrusted source text. No universal prose/embedded-URL redaction is claimed.
- Dependencies: none added, so no new dependency vulnerability review applies.

Human handoff, operator-selected login/app-bound cookies, CapSolver browser-token
application, real paid-provider acceptance, complete DSH workflow, wider retrieval/
resource/lifecycle/install work and final publication alignment remain open.
The DSH tools-package repair/restart and three previously denied installed host
scope-reference overwrites are not authorized by this checkpoint.

## Execution notes

Initial read-only searches guessed a few obsolete/nonexistent filenames before
using the actual provider paths. No files were changed by those lookup failures.
The first documentation patch was rejected for duplicate file operations and made
no changes; grouped per-file patches succeeded. Lint caught two import-order
issues and one unused import before tests; its exact output is retained.
A temporary candidate rejected raw adapter mode; a regression exposed that
narrowing and it was corrected before delivery. Raw support was not removed.

Terminal right-padding is normalized for Markdown; all diagnostic words,
failure tracebacks, warnings and complete summary lines remain below.

### Untouched baseline

Command:

```powershell
pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Full
```

Output:

```text
[GATE] lock check
Resolved 130 packages in 2ms
[GATE] format
97 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
........................................................................ [ 18%]
........................................................................ [ 37%]
........................................................................ [ 56%]
........................................................................ [ 75%]
........................................................................ [ 94%]
......................                                                   [100%]
382 passed in 78.46s (0:01:18)
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Full)

```

Exit code: 0.

### Initial routing assertions RED

Command:

```powershell
uv run --locked python -m pytest -q tests/unit/test_challenge_routing.py
```

Output:

```text
FFFFFFFFFFFFF..F                                                         [100%]
================================== FAILURES ===================================
______ test_auto_crawl_uses_configured_proxy_and_returns_citable_source _______

setup = (<starlette.applications.Starlette object at 0x0000015731CB3320>, <halo_research_gateway.service.HaloService object at...e><h1>Independent source evidence</h1><p>Collected research facts.</p>', api_status=200, calls=[], closed=1, links=[]))

    async def test_auto_crawl_uses_configured_proxy_and_returns_citable_source(setup):
        app, service, state = setup
        result = await call(app)
>       assert len(state.calls) == 1, "Configured proxy is never invoked by the actual MCP crawl"
E       AssertionError: Configured proxy is never invoked by the actual MCP crawl
E       assert 0 == 1
E        +  where 0 = len([])
E        +    where [] = namespace(html='<title>Just a moment...</title><script src="/cdn-cgi/challenge-platform/x.js"></script><p>Verify you a...le><h1>Independent source evidence</h1><p>Collected research facts.</p>', api_status=200, calls=[], closed=1, links=[]).calls

tests\unit\test_challenge_routing.py:73: AssertionError
____ test_disabled_proxy_returns_explicit_challenge_not_fake_evidence[200] ____

setup = (<starlette.applications.Starlette object at 0x0000015731D066C0>, <halo_research_gateway.service.HaloService object at...e><h1>Independent source evidence</h1><p>Collected research facts.</p>', api_status=200, calls=[], closed=1, links=[]))
status = 200

    @pytest.mark.parametrize("status", [200, 403, 429, 503])
    async def test_disabled_proxy_returns_explicit_challenge_not_fake_evidence(setup, status):
        app, service, state = setup
        state.status = status
        service.optional_providers.configs["proxy"].enabled = False
        result = await call(app)
>       assert not result["ok"], "Challenge page was called useful research"
E       AssertionError: Challenge page was called useful research
E       assert not True

tests\unit\test_challenge_routing.py:93: AssertionError
____ test_disabled_proxy_returns_explicit_challenge_not_fake_evidence[403] ____

setup = (<starlette.applications.Starlette object at 0x0000015731E05A60>, <halo_research_gateway.service.HaloService object at...e><h1>Independent source evidence</h1><p>Collected research facts.</p>', api_status=200, calls=[], closed=1, links=[]))
status = 403

    @pytest.mark.parametrize("status", [200, 403, 429, 503])
    async def test_disabled_proxy_returns_explicit_challenge_not_fake_evidence(setup, status):
        app, service, state = setup
        state.status = status
        service.optional_providers.configs["proxy"].enabled = False
        result = await call(app)
        assert not result["ok"], "Challenge page was called useful research"
>       assert result["error"]["code"] == "CRAWL_CHALLENGE_REQUIRED"
E       AssertionError: assert 'CRAWL_NO_EVIDENCE' == 'CRAWL_CHALLENGE_REQUIRED'
E
E         - CRAWL_CHALLENGE_REQUIRED
E         + CRAWL_NO_EVIDENCE

tests\unit\test_challenge_routing.py:94: AssertionError
____ test_disabled_proxy_returns_explicit_challenge_not_fake_evidence[429] ____

setup = (<starlette.applications.Starlette object at 0x0000015731DA7590>, <halo_research_gateway.service.HaloService object at...e><h1>Independent source evidence</h1><p>Collected research facts.</p>', api_status=200, calls=[], closed=1, links=[]))
status = 429

    @pytest.mark.parametrize("status", [200, 403, 429, 503])
    async def test_disabled_proxy_returns_explicit_challenge_not_fake_evidence(setup, status):
        app, service, state = setup
        state.status = status
        service.optional_providers.configs["proxy"].enabled = False
        result = await call(app)
        assert not result["ok"], "Challenge page was called useful research"
>       assert result["error"]["code"] == "CRAWL_CHALLENGE_REQUIRED"
E       AssertionError: assert 'CRAWL_NO_EVIDENCE' == 'CRAWL_CHALLENGE_REQUIRED'
E
E         - CRAWL_CHALLENGE_REQUIRED
E         + CRAWL_NO_EVIDENCE

tests\unit\test_challenge_routing.py:94: AssertionError
____ test_disabled_proxy_returns_explicit_challenge_not_fake_evidence[503] ____

setup = (<starlette.applications.Starlette object at 0x0000015731F30A40>, <halo_research_gateway.service.HaloService object at...e><h1>Independent source evidence</h1><p>Collected research facts.</p>', api_status=200, calls=[], closed=1, links=[]))
status = 503

    @pytest.mark.parametrize("status", [200, 403, 429, 503])
    async def test_disabled_proxy_returns_explicit_challenge_not_fake_evidence(setup, status):
        app, service, state = setup
        state.status = status
        service.optional_providers.configs["proxy"].enabled = False
        result = await call(app)
        assert not result["ok"], "Challenge page was called useful research"
>       assert result["error"]["code"] == "CRAWL_CHALLENGE_REQUIRED"
E       AssertionError: assert 'CRAWL_NO_EVIDENCE' == 'CRAWL_CHALLENGE_REQUIRED'
E
E         - CRAWL_CHALLENGE_REQUIRED
E         + CRAWL_NO_EVIDENCE

tests\unit\test_challenge_routing.py:94: AssertionError
_ test_challenge_does_not_silently_export_session_or_ignore_explicit_controls[options0] _

setup = (<starlette.applications.Starlette object at 0x0000015731FBC1D0>, <halo_research_gateway.service.HaloService object at...e><h1>Independent source evidence</h1><p>Collected research facts.</p>', api_status=200, calls=[], closed=1, links=[]))
options = {'mode': 'standard'}

    @pytest.mark.parametrize("options", [{"mode": "standard"}, {"mode": "managed_profile", "profile": "research"},
                                         {"interaction": "scroll"}])
    async def test_challenge_does_not_silently_export_session_or_ignore_explicit_controls(setup, options):
        app, service, state = setup
        result = await call(app, **options)
>       assert not result["ok"] and result["error"]["code"] == "CRAWL_CHALLENGE_REQUIRED"
E       assert (not True)

tests\unit\test_challenge_routing.py:103: AssertionError
_ test_challenge_does_not_silently_export_session_or_ignore_explicit_controls[options1] _

setup = (<starlette.applications.Starlette object at 0x000001573204EFC0>, <halo_research_gateway.service.HaloService object at...e><h1>Independent source evidence</h1><p>Collected research facts.</p>', api_status=200, calls=[], closed=1, links=[]))
options = {'mode': 'managed_profile', 'profile': 'research'}

    @pytest.mark.parametrize("options", [{"mode": "standard"}, {"mode": "managed_profile", "profile": "research"},
                                         {"interaction": "scroll"}])
    async def test_challenge_does_not_silently_export_session_or_ignore_explicit_controls(setup, options):
        app, service, state = setup
        result = await call(app, **options)
>       assert not result["ok"] and result["error"]["code"] == "CRAWL_CHALLENGE_REQUIRED"
E       assert (not True)

tests\unit\test_challenge_routing.py:103: AssertionError
_ test_challenge_does_not_silently_export_session_or_ignore_explicit_controls[options2] _

setup = (<starlette.applications.Starlette object at 0x00000157320C7860>, <halo_research_gateway.service.HaloService object at...e><h1>Independent source evidence</h1><p>Collected research facts.</p>', api_status=200, calls=[], closed=1, links=[]))
options = {'interaction': 'scroll'}

    @pytest.mark.parametrize("options", [{"mode": "standard"}, {"mode": "managed_profile", "profile": "research"},
                                         {"interaction": "scroll"}])
    async def test_challenge_does_not_silently_export_session_or_ignore_explicit_controls(setup, options):
        app, service, state = setup
        result = await call(app, **options)
>       assert not result["ok"] and result["error"]["code"] == "CRAWL_CHALLENGE_REQUIRED"
E       assert (not True)

tests\unit\test_challenge_routing.py:103: AssertionError
_____________ test_proxy_domain_denial_is_visible_and_never_sent ______________

setup = (<starlette.applications.Starlette object at 0x0000015732105B20>, <halo_research_gateway.service.HaloService object at...e><h1>Independent source evidence</h1><p>Collected research facts.</p>', api_status=200, calls=[], closed=1, links=[]))

    async def test_proxy_domain_denial_is_visible_and_never_sent(setup):
        app, service, state = setup
        service.optional_providers.configs["proxy"].allowed_domains = ["other.example"]
        result = await call(app)
>       assert not result["ok"] and result["error"]["code"] == "OPTIONAL_PROVIDER_DOMAIN_NOT_ALLOWED"
E       assert (not True)

tests\unit\test_challenge_routing.py:111: AssertionError
_ test_unsolved_or_bad_proxy_result_is_not_success[200-<title>Just a moment...</title><script src="/cdn-cgi/challenge-platform/x.js"></script><p>Verify you are human</p>-CRAWL_CHALLENGE_REQUIRED] _

setup = (<starlette.applications.Starlette object at 0x0000015732105130>, <halo_research_gateway.service.HaloService object at.../cdn-cgi/challenge-platform/x.js"></script><p>Verify you are human</p>', api_status=200, calls=[], closed=1, links=[]))
status = 200
body = '<title>Just a moment...</title><script src="/cdn-cgi/challenge-platform/x.js"></script><p>Verify you are human</p>'
code = 'CRAWL_CHALLENGE_REQUIRED'

    @pytest.mark.parametrize("status,body,code", [(200, CHALLENGE, "CRAWL_CHALLENGE_REQUIRED"),
        (403, SOURCE, "PROXY_SOURCE_HTTP_ERROR"), (200, "", "PROXY_EMPTY_EVIDENCE"),
        (302, SOURCE, "PROXY_SOURCE_HTTP_ERROR")])
    async def test_unsolved_or_bad_proxy_result_is_not_success(setup, status, body, code):
        app, service, state = setup
        state.api_status, state.api_body = status, body
        result = await call(app)
>       assert not result["ok"] and result["error"]["code"] == code
E       assert (not True)

tests\unit\test_challenge_routing.py:122: AssertionError
_ test_unsolved_or_bad_proxy_result_is_not_success[403-<title>Research source</title><h1>Independent source evidence</h1><p>Collected research facts.</p>-PROXY_SOURCE_HTTP_ERROR] _

setup = (<starlette.applications.Starlette object at 0x0000015732218D40>, <halo_research_gateway.service.HaloService object at...e><h1>Independent source evidence</h1><p>Collected research facts.</p>', api_status=403, calls=[], closed=1, links=[]))
status = 403
body = '<title>Research source</title><h1>Independent source evidence</h1><p>Collected research facts.</p>'
code = 'PROXY_SOURCE_HTTP_ERROR'

    @pytest.mark.parametrize("status,body,code", [(200, CHALLENGE, "CRAWL_CHALLENGE_REQUIRED"),
        (403, SOURCE, "PROXY_SOURCE_HTTP_ERROR"), (200, "", "PROXY_EMPTY_EVIDENCE"),
        (302, SOURCE, "PROXY_SOURCE_HTTP_ERROR")])
    async def test_unsolved_or_bad_proxy_result_is_not_success(setup, status, body, code):
        app, service, state = setup
        state.api_status, state.api_body = status, body
        result = await call(app)
>       assert not result["ok"] and result["error"]["code"] == code
E       assert (not True)

tests\unit\test_challenge_routing.py:122: AssertionError
_ test_unsolved_or_bad_proxy_result_is_not_success[200--PROXY_EMPTY_EVIDENCE] _

setup = (<starlette.applications.Starlette object at 0x0000015732298EF0>, <halo_research_gateway.service.HaloService object at...rm/x.js"></script><p>Verify you are human</p>', status=200, api_body='', api_status=200, calls=[], closed=1, links=[]))
status = 200, body = '', code = 'PROXY_EMPTY_EVIDENCE'

    @pytest.mark.parametrize("status,body,code", [(200, CHALLENGE, "CRAWL_CHALLENGE_REQUIRED"),
        (403, SOURCE, "PROXY_SOURCE_HTTP_ERROR"), (200, "", "PROXY_EMPTY_EVIDENCE"),
        (302, SOURCE, "PROXY_SOURCE_HTTP_ERROR")])
    async def test_unsolved_or_bad_proxy_result_is_not_success(setup, status, body, code):
        app, service, state = setup
        state.api_status, state.api_body = status, body
        result = await call(app)
>       assert not result["ok"] and result["error"]["code"] == code
E       assert (not True)

tests\unit\test_challenge_routing.py:122: AssertionError
_ test_unsolved_or_bad_proxy_result_is_not_success[302-<title>Research source</title><h1>Independent source evidence</h1><p>Collected research facts.</p>-PROXY_SOURCE_HTTP_ERROR] _

setup = (<starlette.applications.Starlette object at 0x000001577FA568A0>, <halo_research_gateway.service.HaloService object at...e><h1>Independent source evidence</h1><p>Collected research facts.</p>', api_status=302, calls=[], closed=1, links=[]))
status = 302
body = '<title>Research source</title><h1>Independent source evidence</h1><p>Collected research facts.</p>'
code = 'PROXY_SOURCE_HTTP_ERROR'

    @pytest.mark.parametrize("status,body,code", [(200, CHALLENGE, "CRAWL_CHALLENGE_REQUIRED"),
        (403, SOURCE, "PROXY_SOURCE_HTTP_ERROR"), (200, "", "PROXY_EMPTY_EVIDENCE"),
        (302, SOURCE, "PROXY_SOURCE_HTTP_ERROR")])
    async def test_unsolved_or_bad_proxy_result_is_not_success(setup, status, body, code):
        app, service, state = setup
        state.api_status, state.api_body = status, body
        result = await call(app)
>       assert not result["ok"] and result["error"]["code"] == code
E       assert (not True)

tests\unit\test_challenge_routing.py:122: AssertionError
_____ test_proxy_cancellation_closes_browser_and_retains_reserved_attempt _____

setup = (<starlette.applications.Starlette object at 0x0000015732137530>, <halo_research_gateway.service.HaloService object at...e><h1>Independent source evidence</h1><p>Collected research facts.</p>', api_status=200, calls=[], closed=1, links=[]))

    async def test_proxy_cancellation_closes_browser_and_retains_reserved_attempt(setup):
        app, service, state = setup
        entered = asyncio.Event()

        async def stalled(**values):
            entered.set()
            await asyncio.Event().wait()

        service.optional_providers.register("proxy", "brightdata", stalled)
        task = asyncio.create_task(call(app))
        try:
            for _ in range(100):
                if entered.is_set() or task.done():
                    break
                await asyncio.sleep(0.01)
>           assert entered.is_set(), "Crawl never reached configured proxy"
E           AssertionError: Crawl never reached configured proxy
E           assert False
E            +  where False = is_set()
E            +    where is_set = <asyncio.locks.Event object at 0x0000015732105130 [unset]>.is_set

tests\unit\test_challenge_routing.py:156: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_challenge_routing.py::test_auto_crawl_uses_configured_proxy_and_returns_citable_source
FAILED tests/unit/test_challenge_routing.py::test_disabled_proxy_returns_explicit_challenge_not_fake_evidence[200]
FAILED tests/unit/test_challenge_routing.py::test_disabled_proxy_returns_explicit_challenge_not_fake_evidence[403]
FAILED tests/unit/test_challenge_routing.py::test_disabled_proxy_returns_explicit_challenge_not_fake_evidence[429]
FAILED tests/unit/test_challenge_routing.py::test_disabled_proxy_returns_explicit_challenge_not_fake_evidence[503]
FAILED tests/unit/test_challenge_routing.py::test_challenge_does_not_silently_export_session_or_ignore_explicit_controls[options0]
FAILED tests/unit/test_challenge_routing.py::test_challenge_does_not_silently_export_session_or_ignore_explicit_controls[options1]
FAILED tests/unit/test_challenge_routing.py::test_challenge_does_not_silently_export_session_or_ignore_explicit_controls[options2]
FAILED tests/unit/test_challenge_routing.py::test_proxy_domain_denial_is_visible_and_never_sent
FAILED tests/unit/test_challenge_routing.py::test_unsolved_or_bad_proxy_result_is_not_success[200-<title>Just a moment...</title><script src="/cdn-cgi/challenge-platform/x.js"></script><p>Verify you are human</p>-CRAWL_CHALLENGE_REQUIRED]
FAILED tests/unit/test_challenge_routing.py::test_unsolved_or_bad_proxy_result_is_not_success[403-<title>Research source</title><h1>Independent source evidence</h1><p>Collected research facts.</p>-PROXY_SOURCE_HTTP_ERROR]
FAILED tests/unit/test_challenge_routing.py::test_unsolved_or_bad_proxy_result_is_not_success[200--PROXY_EMPTY_EVIDENCE]
FAILED tests/unit/test_challenge_routing.py::test_unsolved_or_bad_proxy_result_is_not_success[302-<title>Research source</title><h1>Independent source evidence</h1><p>Collected research facts.</p>-PROXY_SOURCE_HTTP_ERROR]
FAILED tests/unit/test_challenge_routing.py::test_proxy_cancellation_closes_browser_and_retains_reserved_attempt
14 failed, 2 passed in 5.68s

```

Exit code: 1.

### Budget integrity assertions RED

Command:

```powershell
uv run --locked python -m pytest -q tests/unit/test_optional_budget_integrity.py
```

Output:

```text
FFFFFFFFF.                                                               [100%]
================================== FAILURES ===================================
_______ test_invalid_estimated_cost_never_reaches_adapter_or_ledger[-1] _______

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-2022/test_invalid_estimated_cost_ne0')
cost = -1

    @pytest.mark.parametrize("cost", [-1, 0, float("nan"), float("inf"), -float("inf"), True])
    async def test_invalid_estimated_cost_never_reaches_adapter_or_ledger(tmp_path, cost):
        registry, _ = make_registry(tmp_path)
        calls = []
        registry.register("captcha", "fixture", lambda **values: calls.append(values))
        error = None
        try:
            await registry.execute("captcha", "example.com", cost)
        except Exception as exc:
            error = exc
>       assert isinstance(error, OptionalProviderError) and str(error) == "OPTIONAL_PROVIDER_COST_REQUIRED"
E       assert (False)
E        +  where False = isinstance(None, OptionalProviderError)

tests\unit\test_optional_budget_integrity.py:22: AssertionError
_______ test_invalid_estimated_cost_never_reaches_adapter_or_ledger[0] ________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-2022/test_invalid_estimated_cost_ne1')
cost = 0

    @pytest.mark.parametrize("cost", [-1, 0, float("nan"), float("inf"), -float("inf"), True])
    async def test_invalid_estimated_cost_never_reaches_adapter_or_ledger(tmp_path, cost):
        registry, _ = make_registry(tmp_path)
        calls = []
        registry.register("captcha", "fixture", lambda **values: calls.append(values))
        error = None
        try:
            await registry.execute("captcha", "example.com", cost)
        except Exception as exc:
            error = exc
>       assert isinstance(error, OptionalProviderError) and str(error) == "OPTIONAL_PROVIDER_COST_REQUIRED"
E       assert (False)
E        +  where False = isinstance(None, OptionalProviderError)

tests\unit\test_optional_budget_integrity.py:22: AssertionError
______ test_invalid_estimated_cost_never_reaches_adapter_or_ledger[nan] _______

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-2022/test_invalid_estimated_cost_ne2')
cost = nan

    @pytest.mark.parametrize("cost", [-1, 0, float("nan"), float("inf"), -float("inf"), True])
    async def test_invalid_estimated_cost_never_reaches_adapter_or_ledger(tmp_path, cost):
        registry, _ = make_registry(tmp_path)
        calls = []
        registry.register("captcha", "fixture", lambda **values: calls.append(values))
        error = None
        try:
            await registry.execute("captcha", "example.com", cost)
        except Exception as exc:
            error = exc
>       assert isinstance(error, OptionalProviderError) and str(error) == "OPTIONAL_PROVIDER_COST_REQUIRED"
E       AssertionError: assert (False)
E        +  where False = isinstance(ValueError('cannot convert float NaN to integer'), OptionalProviderError)

tests\unit\test_optional_budget_integrity.py:22: AssertionError
______ test_invalid_estimated_cost_never_reaches_adapter_or_ledger[inf] _______

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-2022/test_invalid_estimated_cost_ne3')
cost = inf

    @pytest.mark.parametrize("cost", [-1, 0, float("nan"), float("inf"), -float("inf"), True])
    async def test_invalid_estimated_cost_never_reaches_adapter_or_ledger(tmp_path, cost):
        registry, _ = make_registry(tmp_path)
        calls = []
        registry.register("captcha", "fixture", lambda **values: calls.append(values))
        error = None
        try:
            await registry.execute("captcha", "example.com", cost)
        except Exception as exc:
            error = exc
>       assert isinstance(error, OptionalProviderError) and str(error) == "OPTIONAL_PROVIDER_COST_REQUIRED"
E       AssertionError: assert (False)
E        +  where False = isinstance(OverflowError('cannot convert float infinity to integer'), OptionalProviderError)

tests\unit\test_optional_budget_integrity.py:22: AssertionError
______ test_invalid_estimated_cost_never_reaches_adapter_or_ledger[-inf] ______

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-2022/test_invalid_estimated_cost_ne4')
cost = -inf

    @pytest.mark.parametrize("cost", [-1, 0, float("nan"), float("inf"), -float("inf"), True])
    async def test_invalid_estimated_cost_never_reaches_adapter_or_ledger(tmp_path, cost):
        registry, _ = make_registry(tmp_path)
        calls = []
        registry.register("captcha", "fixture", lambda **values: calls.append(values))
        error = None
        try:
            await registry.execute("captcha", "example.com", cost)
        except Exception as exc:
            error = exc
>       assert isinstance(error, OptionalProviderError) and str(error) == "OPTIONAL_PROVIDER_COST_REQUIRED"
E       AssertionError: assert (False)
E        +  where False = isinstance(OverflowError('cannot convert float infinity to integer'), OptionalProviderError)

tests\unit\test_optional_budget_integrity.py:22: AssertionError
______ test_invalid_estimated_cost_never_reaches_adapter_or_ledger[True] ______

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-2022/test_invalid_estimated_cost_ne5')
cost = True

    @pytest.mark.parametrize("cost", [-1, 0, float("nan"), float("inf"), -float("inf"), True])
    async def test_invalid_estimated_cost_never_reaches_adapter_or_ledger(tmp_path, cost):
        registry, _ = make_registry(tmp_path)
        calls = []
        registry.register("captcha", "fixture", lambda **values: calls.append(values))
        error = None
        try:
            await registry.execute("captcha", "example.com", cost)
        except Exception as exc:
            error = exc
>       assert isinstance(error, OptionalProviderError) and str(error) == "OPTIONAL_PROVIDER_COST_REQUIRED"
E       assert (False)
E        +  where False = isinstance(None, OptionalProviderError)

tests\unit\test_optional_budget_integrity.py:22: AssertionError
__________ test_tiny_positive_cost_reserves_at_least_one_microdollar __________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-2022/test_tiny_positive_cost_reserv0')

    async def test_tiny_positive_cost_reserves_at_least_one_microdollar(tmp_path):
        registry, _ = make_registry(tmp_path)
        registry.register("captcha", "fixture", lambda **values: {"ok": True})
        result = await registry.execute("captcha", "example.com", 0.00000001)
>       assert result["estimated_cost_usd"] == 0.000001, "Sub-micro estimates are rounded down to free"
E       AssertionError: Sub-micro estimates are rounded down to free
E       assert 0.0 == 1e-06

tests\unit\test_optional_budget_integrity.py:31: AssertionError
____________ test_default_cost_comes_from_operator_policy_not_zero ____________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-2022/test_default_cost_comes_from_o0')

    async def test_default_cost_comes_from_operator_policy_not_zero(tmp_path):
        registry, _ = make_registry(tmp_path)
        registry.configs["captcha"] = registry.configs["captcha"].model_copy(update={"request_cost_usd": 0.02})
        registry.register("captcha", "fixture", lambda **values: {"ok": True})
        result = await registry.execute("captcha", "example.com")
>       assert result["estimated_cost_usd"] == 0.02
E       assert 0.0 == 0.02

tests\unit\test_optional_budget_integrity.py:39: AssertionError
_______ test_operator_request_estimate_is_real_validated_configuration ________

    def test_operator_request_estimate_is_real_validated_configuration():
        config, error = None, None
        try:
            config = OptionalProviderConfig(request_cost_usd=0.02)
        except Exception as exc:
            error = exc
>       assert error is None, f"Request estimate rejected as an unknown configuration field: {error}"
E       AssertionError: Request estimate rejected as an unknown configuration field: 1 validation error for OptionalProviderConfig
E         request_cost_usd
E           Extra inputs are not permitted [type=extra_forbidden, input_value=0.02, input_type=float]
E             For further information visit https://errors.pydantic.dev/2.13/v/extra_forbidden
E       assert 1 validation error for OptionalProviderConfig\nrequest_cost_usd\n  Extra inputs are not permitted [type=extra_forbidden, input_value=0.02, input_type=float]\n    For further information visit https://errors.pydantic.dev/2.13/v/extra_forbidden is None

tests\unit\test_optional_budget_integrity.py:49: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_optional_budget_integrity.py::test_invalid_estimated_cost_never_reaches_adapter_or_ledger[-1]
FAILED tests/unit/test_optional_budget_integrity.py::test_invalid_estimated_cost_never_reaches_adapter_or_ledger[0]
FAILED tests/unit/test_optional_budget_integrity.py::test_invalid_estimated_cost_never_reaches_adapter_or_ledger[nan]
FAILED tests/unit/test_optional_budget_integrity.py::test_invalid_estimated_cost_never_reaches_adapter_or_ledger[inf]
FAILED tests/unit/test_optional_budget_integrity.py::test_invalid_estimated_cost_never_reaches_adapter_or_ledger[-inf]
FAILED tests/unit/test_optional_budget_integrity.py::test_invalid_estimated_cost_never_reaches_adapter_or_ledger[True]
FAILED tests/unit/test_optional_budget_integrity.py::test_tiny_positive_cost_reserves_at_least_one_microdollar
FAILED tests/unit/test_optional_budget_integrity.py::test_default_cost_comes_from_operator_policy_not_zero
FAILED tests/unit/test_optional_budget_integrity.py::test_operator_request_estimate_is_real_validated_configuration
9 failed, 1 passed in 1.39s

```

Exit code: 1.

### First candidate exposes raw versus JSON protocol mismatch

Command:

```powershell
uv run --locked ruff format src/halo_research_gateway/providers/crawl4ai_provider.py src/halo_research_gateway/providers/optional.py src/halo_research_gateway/config.py src/halo_research_gateway/service.py tests/unit/test_challenge_routing.py tests/unit/test_optional_budget_integrity.py
uv run --locked python -m pytest -q tests/unit/test_challenge_routing.py tests/unit/test_optional_budget_integrity.py tests/unit/test_optional_providers.py tests/unit/test_paid_adapters.py tests/unit/test_crawl_options.py
```

Output:

```text
3 files reformatted, 3 files left unchanged
F..............................................................          [100%]
================================== FAILURES ===================================
______ test_auto_crawl_uses_configured_proxy_and_returns_citable_source _______

setup = (<starlette.applications.Starlette object at 0x0000019FFFE9AAE0>, <halo_research_gateway.service.HaloService object at...}, {'zone': 'fixture', 'url': 'https://example.org/research', 'format': 'raw', 'method': 'GET'})], closed=1, links=[]))

    async def test_auto_crawl_uses_configured_proxy_and_returns_citable_source(setup):
        app, service, state = setup
        result = await call(app)
        assert len(state.calls) == 1, "Configured proxy is never invoked by the actual MCP crawl"
        assert result["ok"], result
        assert "Independent source evidence" in result["items"][0]["content"]
        assert "Verify you are human" not in str(result)
        assert result["items"][0]["url"] == URL
        assert result["items"][0]["metadata"]["retrieval_provider"] == "brightdata"
        assert result["items"][0]["metadata"]["final_url_verified"] is False
        assert "PROXY_FINAL_URL_UNVERIFIED" in result["warnings"]
        assert "fixture-key" not in str(result)
>       assert state.calls[0][3]["format"] == "json"
E       AssertionError: assert 'raw' == 'json'
E
E         - json
E         + raw

tests\unit\test_challenge_routing.py:102: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_challenge_routing.py::test_auto_crawl_uses_configured_proxy_and_returns_citable_source
1 failed, 62 passed in 16.84s

```

Exit code: 1.

### Broader routing/response falsification RED

Command:

```powershell
uv run --locked python -m pytest -q tests/unit/test_challenge_routing.py tests/unit/test_paid_response_limits.py
```

Output:

```text
F................FF..FFFF                                                [100%]
================================== FAILURES ===================================
______ test_auto_crawl_uses_configured_proxy_and_returns_citable_source _______

setup = (<starlette.applications.Starlette object at 0x0000018A585ED370>, <halo_research_gateway.service.HaloService object at...}, {'zone': 'fixture', 'url': 'https://example.org/research', 'format': 'raw', 'method': 'GET'})], closed=1, links=[]))

    async def test_auto_crawl_uses_configured_proxy_and_returns_citable_source(setup):
        app, service, state = setup
        result = await call(app)
        assert len(state.calls) == 1, "Configured proxy is never invoked by the actual MCP crawl"
        assert result["ok"], result
        assert "Independent source evidence" in result["items"][0]["content"]
        assert "Verify you are human" not in str(result)
        assert result["items"][0]["url"] == URL
        assert result["items"][0]["metadata"]["retrieval_provider"] == "brightdata"
        assert result["items"][0]["metadata"]["final_url_verified"] is False
        assert "PROXY_FINAL_URL_UNVERIFIED" in result["warnings"]
        assert "fixture-key" not in str(result)
>       assert state.calls[0][3]["format"] == "json"
E       AssertionError: assert 'raw' == 'json'
E
E         - json
E         + raw

tests\unit\test_challenge_routing.py:102: AssertionError
_ test_proxy_relative_links_are_not_resolved_against_an_unverified_final_url __

setup = (<starlette.applications.Starlette object at 0x0000018A588CB140>, <halo_research_gateway.service.HaloService object at...}, {'zone': 'fixture', 'url': 'https://example.org/research', 'format': 'raw', 'method': 'GET'})], closed=1, links=[]))

    async def test_proxy_relative_links_are_not_resolved_against_an_unverified_final_url(setup):
        app, service, state = setup
        state.api_body = SOURCE + '<a href="child">relative</a>'
        result = await call(app, max_pages=2, max_depth=1)
        assert result["ok"] and len(state.calls) == 1
>       assert "PROXY_RELATIVE_LINKS_SKIPPED" in result["warnings"]
E       AssertionError: assert 'PROXY_RELATIVE_LINKS_SKIPPED' in ['PROXY_FINAL_URL_UNVERIFIED', 'PROXY_RETRIEVAL_USED']

tests\unit\test_challenge_routing.py:209: AssertionError
________ test_unknown_provider_response_has_explicit_non_secret_error _________

setup = (<starlette.applications.Starlette object at 0x0000018A5876EBA0>, <halo_research_gateway.service.HaloService object at...e><h1>Independent source evidence</h1><p>Collected research facts.</p>', api_status=200, calls=[], closed=1, links=[]))

    async def test_unknown_provider_response_has_explicit_non_secret_error(setup):
        app, service, state = setup
        service.optional_providers.register("proxy", "brightdata", lambda **values: "unexpected fixture-key")
        result = await call(app)
>       assert not result["ok"] and result["error"]["code"] == "PROXY_RESPONSE_INVALID"
E       AssertionError: assert (not False and 'CRAWL_NO_EVIDENCE' == 'PROXY_RESPONSE_INVALID'
E
E         - PROXY_RESPONSE_INVALID
E         + CRAWL_NO_EVIDENCE)

tests\unit\test_challenge_routing.py:216: AssertionError
_________ test_legacy_cached_challenge_is_not_served_by_forum_reader __________

setup = (<starlette.applications.Starlette object at 0x0000018A589CA1B0>, <halo_research_gateway.service.HaloService object at...e><h1>Independent source evidence</h1><p>Collected research facts.</p>', api_status=200, calls=[], closed=0, links=[]))

    async def test_legacy_cached_challenge_is_not_served_by_forum_reader(setup):
        import hashlib
        import json

        from halo_research_gateway.models import EvidenceItem, ProviderResult

        app, service, state = setup
        key = "community-thread:" + hashlib.sha256(json.dumps([URL, 40, "source_default"], sort_keys=True).encode()).hexdigest()
        bad = ProviderResult("community-forum-crawl", [EvidenceItem(url=URL, retrieved_at="2026-09-03T00:00:00Z", content=CHALLENGE)])
        service.cache.put(key, service._encode_result(bad), 3600)
        result = await service.community_thread(URL)
>       assert not result["ok"] and result["error"]["code"] == "CRAWL_CHALLENGE_REQUIRED"
E       assert (not True)

tests\unit\test_challenge_routing.py:244: AssertionError
___________ test_paid_api_stops_reading_at_response_cap_and_closes ____________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000018A589CAC90>

    async def test_paid_api_stops_reading_at_response_cap_and_closes(monkeypatch):
        stream = Payload([b"x" * 65, b"never read"])
        install(monkeypatch, stream)
        adapter = paid.BrightDataUnlockerAdapter()
        adapter.max_response_bytes = 64
        error = None
        try:
            await adapter(domain="example.org", secret={"api_key": "fixture", "zone": "fixture"}, url="https://example.org")
        except Exception as exc:
            error = exc
>       assert isinstance(error, ValueError) and str(error) == "OPTIONAL_PROVIDER_RESPONSE_TOO_LARGE"
E       AssertionError: assert (True and 'Expecting va...mn 1 (char 0)' == 'OPTIONAL_PRO...NSE_TOO_LARGE'
E        +  where True = isinstance(JSONDecodeError('Expecting value: line 1 column 1 (char 0)'), ValueError)
E
E         - OPTIONAL_PROVIDER_RESPONSE_TOO_LARGE
E         + Expecting value: line 1 column 1 (char 0))

tests\unit\test_paid_response_limits.py:48: AssertionError
_________ test_paid_api_rejects_non_object_json_without_leaking_body __________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000018A5892BE90>

    async def test_paid_api_rejects_non_object_json_without_leaking_body(monkeypatch):
        stream = Payload([b'["fixture-private"]'])
        install(monkeypatch, stream)
        error = None
        try:
            await paid.BrightDataUnlockerAdapter()(domain="example.org", secret={"api_key": "fixture", "zone": "fixture"}, url="https://example.org")
        except Exception as exc:
            error = exc
>       assert isinstance(error, ValueError) and str(error) == "OPTIONAL_PROVIDER_RESPONSE_INVALID"
E       assert (False)
E        +  where False = isinstance(AttributeError("'list' object has no attribute 'get'"), ValueError)

tests\unit\test_paid_response_limits.py:60: AssertionError
_____________ test_paid_api_wall_clock_timeout_closes_slow_stream _____________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000018A58928DD0>

    async def test_paid_api_wall_clock_timeout_closes_slow_stream(monkeypatch):
        class Slow(Payload):
            async def __aiter__(self):
                await asyncio.sleep(0.1)
                yield json.dumps({"body": "late", "status_code": 200}).encode()

        stream = Slow([])
        install(monkeypatch, stream)
        adapter = paid.BrightDataUnlockerAdapter()
        adapter.timeout_seconds = 0.02
        error = None
        try:
            await adapter(domain="example.org", secret={"api_key": "fixture", "zone": "fixture"}, url="https://example.org")
        except Exception as exc:
            error = exc
>       assert isinstance(error, TimeoutError), "Paid response has no total wall-clock limit"
E       AssertionError: Paid response has no total wall-clock limit
E       assert False
E        +  where False = isinstance(None, TimeoutError)

tests\unit\test_paid_response_limits.py:79: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_challenge_routing.py::test_auto_crawl_uses_configured_proxy_and_returns_citable_source
FAILED tests/unit/test_challenge_routing.py::test_proxy_relative_links_are_not_resolved_against_an_unverified_final_url
FAILED tests/unit/test_challenge_routing.py::test_unknown_provider_response_has_explicit_non_secret_error
FAILED tests/unit/test_challenge_routing.py::test_legacy_cached_challenge_is_not_served_by_forum_reader
FAILED tests/unit/test_paid_response_limits.py::test_paid_api_stops_reading_at_response_cap_and_closes
FAILED tests/unit/test_paid_response_limits.py::test_paid_api_rejects_non_object_json_without_leaking_body
FAILED tests/unit/test_paid_response_limits.py::test_paid_api_wall_clock_timeout_closes_slow_stream
7 failed, 18 passed in 4.75s

```

Exit code: 1.

### Formatting/lint stop (tests not started)

Command:

```powershell
uv run --locked ruff format src tests/unit/test_challenge_routing.py tests/unit/test_optional_budget_integrity.py tests/unit/test_paid_response_limits.py
uv run --locked ruff check src tests
if ($LASTEXITCODE) { exit $LASTEXITCODE }
uv run --locked python -m pytest -q tests/unit/test_challenge_routing.py tests/unit/test_optional_budget_integrity.py tests/unit/test_optional_providers.py tests/unit/test_paid_adapters.py tests/unit/test_paid_response_limits.py tests/unit/test_crawl_options.py
```

Output:

```text
3 files reformatted, 42 files left unchanged
I001 [*] Import block is un-sorted or un-formatted
  --> src\halo_research_gateway\providers\crawl4ai_provider.py:3:1
   |
 1 |   """Lazy Crawl4AI adapter. Import failure degrades only browser tools."""
 2 |
 3 | / from __future__ import annotations
 4 | |
 5 | | import asyncio
 6 | | import contextlib
 7 | | import re
 8 | | from collections import deque
 9 | | from pathlib import Path
10 | | from types import SimpleNamespace
11 | | from urllib.parse import urljoin, urlsplit, urlunsplit
12 | |
13 | | from ..clock import SystemClock, rfc3339
14 | | from ..config import CrawlConfig
15 | | from ..models import EvidenceItem, LocalTarget, ProviderResult
16 | | from ..security import is_sensitive_url, redact_url, validate_url
17 | | from .deep import canonical_url
18 | | from .http_fetch import resolve_public
19 | | from .html import extract_html
20 | | from .optional import OptionalProviderError
   | |___________________________________________^
help: Organize imports
   |
17 | from .deep import canonical_url
18 + from .html import extract_html
19 | from .http_fetch import resolve_public
   - from .html import extract_html
20 | from .optional import OptionalProviderError
   |

I001 [*] Import block is un-sorted or un-formatted
 --> tests\unit\test_optional_budget_integrity.py:3:1
  |
1 |   """Optional retrieval must not bypass its operator's attempt/spend limits."""
2 |
3 | / import asyncio
4 | |
5 | | import pytest
6 | |
7 | | from halo_research_gateway.config import OptionalProviderConfig
8 | | from halo_research_gateway.providers.optional import OptionalProviderError
9 | | from test_optional_providers import make_registry
  | |_________________________________________________^
help: Organize imports
   |
5  | import pytest
6  + from test_optional_providers import make_registry
7  |
8  | from halo_research_gateway.config import OptionalProviderConfig
9  | from halo_research_gateway.providers.optional import OptionalProviderError
   - from test_optional_providers import make_registry
10 |
   |

F401 [*] `pytest` imported but unused
 --> tests\unit\test_paid_response_limits.py:7:8
  |
6 | import httpx
7 | import pytest
  |        ^^^^^^
8 |
9 | from halo_research_gateway.providers import paid
  |
help: Remove unused import: `pytest`
  |
6 | import httpx
  - import pytest
7 |
  |

Found 3 errors.
[*] 3 fixable with the `--fix` option.

```

Exit code: 1.

### Corrected lint and focused GREEN

Command:

```powershell
uv run --locked ruff check --fix src/halo_research_gateway/providers/crawl4ai_provider.py tests/unit/test_optional_budget_integrity.py tests/unit/test_paid_response_limits.py
uv run --locked python -m pytest -q tests/unit/test_challenge_routing.py tests/unit/test_optional_budget_integrity.py tests/unit/test_optional_providers.py tests/unit/test_paid_adapters.py tests/unit/test_paid_response_limits.py tests/unit/test_crawl_options.py
```

Output:

```text
Found 3 errors (3 fixed, 0 remaining).
........................................................................ [100%]
72 passed in 16.57s

```

Exit code: 0.

### First native acceptance

Command:

```powershell
uv run --locked ruff format tests/acceptance/test_challenge_native.py
uv run --locked ruff check src tests
if ($LASTEXITCODE) { exit $LASTEXITCODE }
uv run --locked python -m pytest -q -s tests/acceptance/test_challenge_native.py
```

Output:

```text
1 file reformatted
All checks passed!
..{"native_chrome_public_header_echo": true, "native_network_mcp_clients": 2, "local_fake_vendor_requests": 1, "real_paid_requests": 0, "content_chars": 1742, "pages": 25, "cache_reuse": true, "reserved_estimated_usd": 0.02}
Native Chrome/MCP fake-vendor routing, durable budget and owned-browser cleanup PASS
.
3 passed in 8.64s

```

Exit code: 0.

### Raw compatibility and total solver deadline RED

Command:

```powershell
uv run --locked python -m pytest -q tests/unit/test_paid_response_limits.py
```

Output:

```text
...FF                                                                    [100%]
================================== FAILURES ===================================
____________ test_explicit_raw_unlocker_response_remains_supported ____________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000027E54AAE870>

    async def test_explicit_raw_unlocker_response_remains_supported(monkeypatch):
        stream = Payload([b"<p>Raw source evidence</p>"])
        install(monkeypatch, stream)
        result, error = None, None
        try:
            result = await paid.BrightDataUnlockerAdapter()(domain="example.org", secret={"api_key": "fixture", "zone": "fixture"},
                                                            url="https://example.org", output_format="raw")
        except Exception as exc:
            error = exc
>       assert error is None, f"Raw Unlocker response cannot be decoded: {error}"
E       AssertionError: Raw Unlocker response cannot be decoded: BRIGHTDATA_FORMAT_INVALID
E       assert ValueError('BRIGHTDATA_FORMAT_INVALID') is None

tests\unit\test_paid_response_limits.py:93: AssertionError
_______ test_capsolver_total_deadline_includes_create_and_poll_requests _______

    async def test_capsolver_total_deadline_includes_create_and_poll_requests():
        async def pending(*args):
            await asyncio.sleep(0.1)
            return {"status": "ready", "solution": {"token": "fixture"}}

        adapter = paid.CapSolverAdapter(requester=pending)
        adapter.solve_timeout_seconds = 0.02
        error = None
        try:
            await adapter(domain="example.org", secret={"api_key": "fixture"}, task={"websiteURL": "https://example.org"})
        except Exception as exc:
            error = exc
>       assert isinstance(error, TimeoutError), "Solver creation bypasses the overall solve deadline"
E       AssertionError: Solver creation bypasses the overall solve deadline
E       assert False
E        +  where False = isinstance(None, TimeoutError)

tests\unit\test_paid_response_limits.py:110: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_paid_response_limits.py::test_explicit_raw_unlocker_response_remains_supported
FAILED tests/unit/test_paid_response_limits.py::test_capsolver_total_deadline_includes_create_and_poll_requests
2 failed, 3 passed in 0.33s

```

Exit code: 1.

### Focused GREEN after raw/deadline fixes

Command:

```powershell
uv run --locked ruff format src/halo_research_gateway/providers/paid.py tests/unit/test_paid_response_limits.py
uv run --locked python -m pytest -q tests/unit/test_challenge_routing.py tests/unit/test_optional_budget_integrity.py tests/unit/test_optional_providers.py tests/unit/test_paid_adapters.py tests/unit/test_paid_response_limits.py tests/unit/test_crawl_options.py
```

Output:

```text
2 files reformatted
........................................................................ [ 97%]
..                                                                       [100%]
74 passed in 16.87s

```

Exit code: 0.

### Full gate before metadata-label correction

Command:

```powershell
pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Full
```

Output:

```text
[GATE] lock check
Resolved 130 packages in 2ms
[GATE] format
101 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
........................................................................ [ 17%]
........................................................................ [ 34%]
........................................................................ [ 51%]
........................................................................ [ 68%]
........................................................................ [ 85%]
...........................................................              [100%]
419 passed in 75.59s (0:01:15)
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Full)

```

Exit code: 0.

### Native after adapter fixes

Command:

```powershell
uv run --locked python -m pytest -q -s tests/acceptance/test_challenge_native.py
```

Output:

```text
..{"native_chrome_public_header_echo": true, "native_network_mcp_clients": 2, "local_fake_vendor_requests": 1, "real_paid_requests": 0, "content_chars": 1742, "pages": 25, "cache_reuse": true, "reserved_estimated_usd": 0.02}
Native Chrome/MCP fake-vendor routing, durable budget and owned-browser cleanup PASS
.
3 passed in 7.80s

```

Exit code: 0.

### Actual fallback-mode reporting RED

Command:

```powershell
uv run --locked python -m pytest -q tests/unit/test_challenge_routing.py -k auto_crawl
```

Output:

```text
F                                                                        [100%]
================================== FAILURES ===================================
______ test_auto_crawl_uses_configured_proxy_and_returns_citable_source _______

setup = (<starlette.applications.Starlette object at 0x0000013DB21AF9E0>, <halo_research_gateway.service.HaloService object at..., {'zone': 'fixture', 'url': 'https://example.org/research', 'format': 'json', 'method': 'GET'})], closed=1, links=[]))

    async def test_auto_crawl_uses_configured_proxy_and_returns_citable_source(setup):
        app, service, state = setup
        result = await call(app)
        assert len(state.calls) == 1, "Configured proxy is never invoked by the actual MCP crawl"
        assert result["ok"], result
        assert "Independent source evidence" in result["items"][0]["content"]
        assert "Verify you are human" not in str(result)
        assert result["items"][0]["url"] == URL
        assert result["items"][0]["metadata"]["retrieval_provider"] == "brightdata"
>       assert result["items"][0]["metadata"]["mode"] == "proxy", "Actual fallback mode is mislabeled standard"
E       AssertionError: Actual fallback mode is mislabeled standard
E       assert 'standard' == 'proxy'
E
E         - proxy
E         + standard

tests\unit\test_challenge_routing.py:99: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_challenge_routing.py::test_auto_crawl_uses_configured_proxy_and_returns_citable_source
1 failed, 21 deselected in 1.88s

```

Exit code: 1.

### Final native acceptance

Command:

```powershell
uv run --locked python -m pytest -q -s tests/acceptance/test_challenge_native.py
```

Output:

```text
..{"native_chrome_public_header_echo": true, "native_network_mcp_clients": 2, "local_fake_vendor_requests": 1, "real_paid_requests": 0, "content_chars": 1742, "pages": 25, "cache_reuse": true, "reserved_estimated_usd": 0.02}
Native Chrome/MCP fake-vendor routing, durable budget and owned-browser cleanup PASS
.
3 passed in 8.35s

```

Exit code: 0.

### Final full gate

Command:

```powershell
pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Full
```

Output:

```text
[GATE] lock check
Resolved 130 packages in 1ms
[GATE] format
101 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
........................................................................ [ 17%]
........................................................................ [ 34%]
........................................................................ [ 51%]
........................................................................ [ 68%]
........................................................................ [ 85%]
...........................................................              [100%]
419 passed in 78.05s (0:01:18)
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Full)

```

Exit code: 0.
