# Shared cache-limit evidence - 2026-09-02

Research-only checkpoint based on source `5cf171d417ea34da1ae3e59ffe003e5a94d23194`.
Product version remains 0.2.0; result schema 1.5, database schema 3 and cursor
layout 3 are unchanged. No dependency added. This file proves the candidate
changes, not a future Git SHA, CI run, installed reload or DSH success.

## Outcome and boundary

Every HaloService cache writer now enforces compressed-payload capacity in the
same SQLite transaction as insertion. Cache hits and misses remove expired or
over-limit rows; an entry at its expiry timestamp is no longer usable. Lowered
limits reconcile existing rows on cache activity or explicit maintenance.
The configured total/entry capacities must be positive and are visible in stats.

Results that exceed either cache admission limit retain their usable evidence
and existing bounded in-memory pagination, with `RESULT_NOT_CACHED_TOO_LARGE`
and an empty disk-cache key. Job-result views use the same behavior. Restart
cannot recover an uncached cursor; durable job checkpoints remain separate.
Other storage errors are not silently swallowed.

The low-level Cache constructor defaults to its existing manual-eviction API
for compatibility with frozen tests and migration/fixture callers. HaloService
always constructs it with `enforce_limits=True`; there is no per-write opt-out
or operator configuration switch. Existing frozen cache tests are unchanged.

Only `cache_entries` rows are pruned. No jobs, connections, provider circuits,
vault records, receipts or personal data are deleted. Evicted cache evidence can
be fetched again, but its old immutable cursor may no longer recover on restart.

## Verification coverage

Read before editing: cache implementation and frozen cache tests, config, service
cache/job paths, result-retention/job/transcript tests, repository scope/AGENTS,
manual, operations, README, changelog, progress/status and canonical skill scope.

Baseline: 359 tests. Added 23 cases in `test_cache_runtime_limits.py`.
The first run had 14 assertion failures and one passing max-age preservation
guard. Four lowered-entry-limit cases and one stats-cap case then failed before
their fixes. Three transaction/concurrency falsification cases already passed
the first candidate: observer visibility before prune, insert rollback on prune
failure, and six independent SQLite writers performing 72 writes under one cap.
These three are not represented as assertion REDs. No frozen test was weakened.

Full post-change gate: 382 tests. Focused cache/retention/job/transcript set: 84.
Raw commands and output follow. Native acceptance is separate from fixture tests.

The native test launched disposable loopback Windows Gateway processes, with two
independent network MCP clients and nine distinct public Python-document URLs.
At a 4096-byte cap, 111 observed samples peaked at 3607 compressed bytes and only
two cache entries remained. The 2664-character source survived memory pagination
after actual disk eviction. After restart, the evicted cursor returned
`CURSOR_EVICTED`; the retained cursor reconstructed identical source text.
Lowering the disposable limits to 100 bytes purged the old cache and preserved
the newly fetched evidence through pages, with the uncached warning and zero
saved entries. All owned processes stopped and temporary state was removed.
Installed config, DSH, accounts, profiles and paid providers were not changed.

## Security and limitations

- Trust-boundary inputs: storage capacities reject zero/negative values; cache
  keys/values use parameterized SQL and fixed table names. Upstream research
  evidence remains untrusted. Existing source and credential policies unchanged.
- New/changed endpoints: none; the existing redacted stats adds capacity numbers.
- Secrets: native test uses only public Python documentation and disposable state.
  Repository-wide credential-pattern and ignore checks are required before push.
- Rendering/eval/deserialization: no new eval, unsafe rendering or new deserializer.
  Existing gzip/JSON use remains; corrupted-cache handling is not fixed here.
- Dependencies: none added; no new dependency vulnerability review is applicable.

Capacity means logical compressed payload bytes, not physical SQLite/WAL size,
backups, logs, total Python/native RAM or temporary serialization. No VACUUM,
idle-prune timer, cache I/O offloading or strict event-loop wall-clock bound is
claimed. Stats and memory-only cursor activity do not prune disk entries.
Native source limits, local/GitHub shared response bounds, arbitrary job fields,
browser/DNS/OOPIF/shutdown/clean-install coverage remain unfinished.

DSH still has the separately recorded pre-dispatch tools-package `prepare`
failure. Repair/restart approval remains outstanding. Installed research login,
human challenge/optional-provider routing, paid use and a complete DSH research
workflow are not proved by this cache checkpoint.

## Complete verification outputs

Native SDK INFO/session logs still appear despite the test's ERROR setting;
they are retained below. No observed errors/warnings are removed. Per-test dots
are also retained. A documentation patch initially failed because its table
match used a partial line; it made no changes, then succeeded with full-line
context. A read-only .gitignore check initially targeted the task directory
instead of the repository; it was rerun against the canonical repository.

### Untouched baseline

Command:

```powershell
pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Full
```

Output:

```text
[GATE] lock check
Resolved 130 packages in 1ms
[GATE] format
95 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
........................................................................ [ 20%]
........................................................................ [ 40%]
........................................................................ [ 60%]
........................................................................ [ 80%]
.......................................................................  [100%]
359 passed in 70.94s (0:01:10)
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Full)

```

Exit code: 0.

### Initial assertion RED

Command:

```powershell
uv run --locked python -m pytest -q tests/unit/test_cache_runtime_limits.py
```

Output:

```text
FFFFFFFFFFFFFF.                                                          [100%]
================================== FAILURES ===================================
_____ test_ordinary_writes_enforce_total_limit_and_preserve_recent_reads ______

service = <halo_research_gateway.service.HaloService object at 0x000001C9A61C8080>

    async def test_ordinary_writes_enforce_total_limit_and_preserve_recent_reads(service):
        sizes = [len(gzip.compress(service._encode_result(sample(key)))) for key in ("a", "b", "c")]
        service.cache.max_bytes = max(sizes) * 2 + 10
        for key in ("a", "b"):
            await store_result(service, key)
            service.cache.clock.advance()
        assert service.cache.get("a")
        service.cache.clock.advance()
        await store_result(service, "c")
>       assert service.cache.stats()["total_compressed_bytes"] <= service.cache.max_bytes, "Ordinary writes bypass total cache cap"
E       AssertionError: Ordinary writes bypass total cache cap
E       assert 4974 <= 3328
E        +  where 3328 = <halo_research_gateway.cache.Cache object at 0x000001C9A60E94C0>.max_bytes
E        +    where <halo_research_gateway.cache.Cache object at 0x000001C9A60E94C0> = <halo_research_gateway.service.HaloService object at 0x000001C9A61C8080>.cache

tests\unit\test_cache_runtime_limits.py:66: AssertionError
__________ test_ordinary_traffic_removes_other_expired_results[hit] ___________

service = <halo_research_gateway.service.HaloService object at 0x000001C9A62CC9B0>
trigger = 'hit'

    @pytest.mark.parametrize("trigger", ["hit", "miss", "write"])
    async def test_ordinary_traffic_removes_other_expired_results(service, trigger):
        await store_result(service, "expired", ttl=1)
        await store_result(service, "fresh", ttl=100)
        service.cache.clock.advance(2)
        if trigger == "write":
            await store_result(service, "new")
        else:
            service.cache.get("fresh" if trigger == "hit" else "missing")
        with closing(sqlite3.connect(service.cache.db_path)) as db:
            count = db.execute("SELECT COUNT(*) FROM cache_entries WHERE cache_key='expired'").fetchone()[0]
>       assert count == 0, "Expired payload remains stored after ordinary cache traffic"
E       AssertionError: Expired payload remains stored after ordinary cache traffic
E       assert 1 == 0

tests\unit\test_cache_runtime_limits.py:82: AssertionError
__________ test_ordinary_traffic_removes_other_expired_results[miss] __________

service = <halo_research_gateway.service.HaloService object at 0x000001C9A62CDAF0>
trigger = 'miss'

    @pytest.mark.parametrize("trigger", ["hit", "miss", "write"])
    async def test_ordinary_traffic_removes_other_expired_results(service, trigger):
        await store_result(service, "expired", ttl=1)
        await store_result(service, "fresh", ttl=100)
        service.cache.clock.advance(2)
        if trigger == "write":
            await store_result(service, "new")
        else:
            service.cache.get("fresh" if trigger == "hit" else "missing")
        with closing(sqlite3.connect(service.cache.db_path)) as db:
            count = db.execute("SELECT COUNT(*) FROM cache_entries WHERE cache_key='expired'").fetchone()[0]
>       assert count == 0, "Expired payload remains stored after ordinary cache traffic"
E       AssertionError: Expired payload remains stored after ordinary cache traffic
E       assert 1 == 0

tests\unit\test_cache_runtime_limits.py:82: AssertionError
_________ test_ordinary_traffic_removes_other_expired_results[write] __________

service = <halo_research_gateway.service.HaloService object at 0x000001C9A62CEE10>
trigger = 'write'

    @pytest.mark.parametrize("trigger", ["hit", "miss", "write"])
    async def test_ordinary_traffic_removes_other_expired_results(service, trigger):
        await store_result(service, "expired", ttl=1)
        await store_result(service, "fresh", ttl=100)
        service.cache.clock.advance(2)
        if trigger == "write":
            await store_result(service, "new")
        else:
            service.cache.get("fresh" if trigger == "hit" else "missing")
        with closing(sqlite3.connect(service.cache.db_path)) as db:
            count = db.execute("SELECT COUNT(*) FROM cache_entries WHERE cache_key='expired'").fetchone()[0]
>       assert count == 0, "Expired payload remains stored after ordinary cache traffic"
E       AssertionError: Expired payload remains stored after ordinary cache traffic
E       assert 1 == 0

tests\unit\test_cache_runtime_limits.py:82: AssertionError
_________________ test_expiry_boundary_is_not_served_as_fresh _________________

service = <halo_research_gateway.service.HaloService object at 0x000001C9A636FD70>

    async def test_expiry_boundary_is_not_served_as_fresh(service):
        await store_result(service, "expired", ttl=1)
        service.cache.clock.advance(1)
>       assert service.cache.get("expired") is None, "Entry at expires_at was still served"
E       AssertionError: Entry at expires_at was still served
E       assert b'{"provider":"fixture","items":[{"title":null,"url":"https://example.org/expired","published_at":null,"retrieved_at":...747a62583af96a8d4a98eb5afa92831f2ed25b0b227f239ef08f6515af1d2aae87f6316e286bac6511f"}],"warnings":[],"available":null}' is None
E        +  where b'{"provider":"fixture","items":[{"title":null,"url":"https://example.org/expired","published_at":null,"retrieved_at":...747a62583af96a8d4a98eb5afa92831f2ed25b0b227f239ef08f6515af1d2aae87f6316e286bac6511f"}],"warnings":[],"available":null}' = get('expired')
E        +    where get = <halo_research_gateway.cache.Cache object at 0x000001C9A636E900>.get
E        +      where <halo_research_gateway.cache.Cache object at 0x000001C9A636E900> = <halo_research_gateway.service.HaloService object at 0x000001C9A636FD70>.cache

tests\unit\test_cache_runtime_limits.py:88: AssertionError
_ test_read_reconciles_preexisting_over_limit_cache_without_touching_rate_state _

service = <halo_research_gateway.service.HaloService object at 0x000001C9A636CA10>

    async def test_read_reconciles_preexisting_over_limit_cache_without_touching_rate_state(service):
        service.cache.max_bytes = 2500
        with closing(sqlite3.connect(service.cache.db_path)) as db:
            db.execute("INSERT INTO rate_state(bucket_key) VALUES ('cache-bound-fixture')")
            db.commit()
        # Simulates pre-upgrade data through the existing low-level manual-eviction API.
        for key in ("old-a", "old-b", "old-c"):
            service.cache.put(key, service._encode_result(sample(key)), 60)
            service.cache.clock.advance()
        assert service.cache.stats()["total_compressed_bytes"] > service.cache.max_bytes
        service.cache.get("missing")
>       assert service.cache.stats()["total_compressed_bytes"] <= service.cache.max_bytes, "Old over-limit cache not reconciled"
E       AssertionError: Old over-limit cache not reconciled
E       assert 4994 <= 2500
E        +  where 2500 = <halo_research_gateway.cache.Cache object at 0x000001C9A636CBF0>.max_bytes
E        +    where <halo_research_gateway.cache.Cache object at 0x000001C9A636CBF0> = <halo_research_gateway.service.HaloService object at 0x000001C9A636CA10>.cache

tests\unit\test_cache_runtime_limits.py:102: AssertionError
______ test_oversized_cache_entry_does_not_hide_readable_evidence[entry] ______

service = <halo_research_gateway.service.HaloService object at 0x000001C9A636DD90>
limit = 'entry'

    @pytest.mark.parametrize("limit", ["entry", "total"])
    async def test_oversized_cache_entry_does_not_hide_readable_evidence(service, limit):
        setattr(service.cache, "entry_max_bytes" if limit == "entry" else "max_bytes", 100)
        result = sample("large")
        async def fetch(url):
            return result
        service.http.fetch = fetch
        first = await service.web_fetch(result.items[0].url, max_chars=2000)
>       assert first["ok"], f"Cache admission failure hid usable evidence: {first.get('error')}"
E       AssertionError: Cache admission failure hid usable evidence: {'code': 'UPSTREAM_UNAVAILABLE', 'message': 'EntryTooLargeError: operation did not complete'}
E       assert False

tests\unit\test_cache_runtime_limits.py:115: AssertionError
______ test_oversized_cache_entry_does_not_hide_readable_evidence[total] ______

service = <halo_research_gateway.service.HaloService object at 0x000001C9A62CF8F0>
limit = 'total'

    @pytest.mark.parametrize("limit", ["entry", "total"])
    async def test_oversized_cache_entry_does_not_hide_readable_evidence(service, limit):
        setattr(service.cache, "entry_max_bytes" if limit == "entry" else "max_bytes", 100)
        result = sample("large")
        async def fetch(url):
            return result
        service.http.fetch = fetch
        first = await service.web_fetch(result.items[0].url, max_chars=2000)
        assert first["ok"], f"Cache admission failure hid usable evidence: {first.get('error')}"
>       assert first["cache"]["key"] == "", "Uncached response advertises a disk-recoverable key"
E       AssertionError: Uncached response advertises a disk-recoverable key
E       assert 'fetch:v2:072...7c4224f93b3ab' == ''
E
E         + fetch:v2:0723d74daf6b5024063ab73f0d9ca9205c0c8074a0d9c507ddc7c4224f93b3ab

tests\unit\test_cache_runtime_limits.py:116: AssertionError
_________ test_job_evidence_survives_cache_admission_rejection[entry] _________

service = <halo_research_gateway.service.HaloService object at 0x000001C9A62CD5B0>
limit = 'entry'

    @pytest.mark.parametrize("limit", ["entry", "total"])
    async def test_job_evidence_survives_cache_admission_rejection(service, limit):
        setattr(service.cache, "entry_max_bytes" if limit == "entry" else "max_bytes", 100)
        status = {
            "state": "complete", "error_code": None,
            "progress": {"checkpoint": {"items": [sample("job").items[0].as_dict()], "warnings": []}},
        }
        error = None
        try:
            view = service._job_status_view(status)
        except Exception as exc:
            view, error = None, str(exc)
>       assert error is None, f"Completed job evidence hidden by cache capacity: {error}"
E       AssertionError: Completed job evidence hidden by cache capacity: Entry size 1661 exceeds maximum allowed 100 bytes
E       assert 'Entry size 1661 exceeds maximum allowed 100 bytes' is None

tests\unit\test_cache_runtime_limits.py:152: AssertionError
_________ test_job_evidence_survives_cache_admission_rejection[total] _________

service = <halo_research_gateway.service.HaloService object at 0x000001C9A62CE900>
limit = 'total'

    @pytest.mark.parametrize("limit", ["entry", "total"])
    async def test_job_evidence_survives_cache_admission_rejection(service, limit):
        setattr(service.cache, "entry_max_bytes" if limit == "entry" else "max_bytes", 100)
        status = {
            "state": "complete", "error_code": None,
            "progress": {"checkpoint": {"items": [sample("job").items[0].as_dict()], "warnings": []}},
        }
        error = None
        try:
            view = service._job_status_view(status)
        except Exception as exc:
            view, error = None, str(exc)
        assert error is None, f"Completed job evidence hidden by cache capacity: {error}"
        assert view["progress"]["result"]["ok"]
>       assert view["progress"]["result"]["cache"]["key"] == ""
E       AssertionError: assert 'job-evidence...6876985c3cc73' == ''
E
E         + job-evidence:201a2ff73b5c83fce0c394bc4df9e629064ca28f911a5231e576876985c3cc73

tests\unit\test_cache_runtime_limits.py:154: AssertionError
________ test_storage_cache_limits_must_be_positive[0-cache_max_bytes] ________

field = 'cache_max_bytes', value = 0

    @pytest.mark.parametrize("field", ["cache_max_bytes", "entry_max_bytes"])
    @pytest.mark.parametrize("value", [0, -1])
    def test_storage_cache_limits_must_be_positive(field, value):
        rejected = False
        try:
            StorageConfig.model_validate({field: value})
        except ValidationError:
            rejected = True
>       assert rejected, f"{field} accepted nonpositive capacity"
E       AssertionError: cache_max_bytes accepted nonpositive capacity
E       assert False

tests\unit\test_cache_runtime_limits.py:166: AssertionError
________ test_storage_cache_limits_must_be_positive[0-entry_max_bytes] ________

field = 'entry_max_bytes', value = 0

    @pytest.mark.parametrize("field", ["cache_max_bytes", "entry_max_bytes"])
    @pytest.mark.parametrize("value", [0, -1])
    def test_storage_cache_limits_must_be_positive(field, value):
        rejected = False
        try:
            StorageConfig.model_validate({field: value})
        except ValidationError:
            rejected = True
>       assert rejected, f"{field} accepted nonpositive capacity"
E       AssertionError: entry_max_bytes accepted nonpositive capacity
E       assert False

tests\unit\test_cache_runtime_limits.py:166: AssertionError
_______ test_storage_cache_limits_must_be_positive[-1-cache_max_bytes] ________

field = 'cache_max_bytes', value = -1

    @pytest.mark.parametrize("field", ["cache_max_bytes", "entry_max_bytes"])
    @pytest.mark.parametrize("value", [0, -1])
    def test_storage_cache_limits_must_be_positive(field, value):
        rejected = False
        try:
            StorageConfig.model_validate({field: value})
        except ValidationError:
            rejected = True
>       assert rejected, f"{field} accepted nonpositive capacity"
E       AssertionError: cache_max_bytes accepted nonpositive capacity
E       assert False

tests\unit\test_cache_runtime_limits.py:166: AssertionError
_______ test_storage_cache_limits_must_be_positive[-1-entry_max_bytes] ________

field = 'entry_max_bytes', value = -1

    @pytest.mark.parametrize("field", ["cache_max_bytes", "entry_max_bytes"])
    @pytest.mark.parametrize("value", [0, -1])
    def test_storage_cache_limits_must_be_positive(field, value):
        rejected = False
        try:
            StorageConfig.model_validate({field: value})
        except ValidationError:
            rejected = True
>       assert rejected, f"{field} accepted nonpositive capacity"
E       AssertionError: entry_max_bytes accepted nonpositive capacity
E       assert False

tests\unit\test_cache_runtime_limits.py:166: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_cache_runtime_limits.py::test_ordinary_writes_enforce_total_limit_and_preserve_recent_reads
FAILED tests/unit/test_cache_runtime_limits.py::test_ordinary_traffic_removes_other_expired_results[hit]
FAILED tests/unit/test_cache_runtime_limits.py::test_ordinary_traffic_removes_other_expired_results[miss]
FAILED tests/unit/test_cache_runtime_limits.py::test_ordinary_traffic_removes_other_expired_results[write]
FAILED tests/unit/test_cache_runtime_limits.py::test_expiry_boundary_is_not_served_as_fresh
FAILED tests/unit/test_cache_runtime_limits.py::test_read_reconciles_preexisting_over_limit_cache_without_touching_rate_state
FAILED tests/unit/test_cache_runtime_limits.py::test_oversized_cache_entry_does_not_hide_readable_evidence[entry]
FAILED tests/unit/test_cache_runtime_limits.py::test_oversized_cache_entry_does_not_hide_readable_evidence[total]
FAILED tests/unit/test_cache_runtime_limits.py::test_job_evidence_survives_cache_admission_rejection[entry]
FAILED tests/unit/test_cache_runtime_limits.py::test_job_evidence_survives_cache_admission_rejection[total]
FAILED tests/unit/test_cache_runtime_limits.py::test_storage_cache_limits_must_be_positive[0-cache_max_bytes]
FAILED tests/unit/test_cache_runtime_limits.py::test_storage_cache_limits_must_be_positive[0-entry_max_bytes]
FAILED tests/unit/test_cache_runtime_limits.py::test_storage_cache_limits_must_be_positive[-1-cache_max_bytes]
FAILED tests/unit/test_cache_runtime_limits.py::test_storage_cache_limits_must_be_positive[-1-entry_max_bytes]
14 failed, 1 passed in 2.12s

```

Exit code: 1.

### First focused GREEN

Command:

```powershell
uv run --locked ruff format src/halo_research_gateway/cache.py src/halo_research_gateway/config.py src/halo_research_gateway/service.py tests/unit/test_cache_runtime_limits.py
uv run --locked python -m pytest -q tests/unit/test_cache_runtime_limits.py tests/unit/test_cache.py tests/unit/test_result_retention.py tests/unit/test_job_continuation.py tests/unit/test_transcript_paging.py
```

Output:

```text
3 files reformatted, 1 file left unchanged
........................................................................ [ 94%]
....                                                                     [100%]
76 passed in 7.82s

```

Exit code: 0.

### Lowered-limit falsification RED and transaction checks

Command:

```powershell
uv run --locked python -m pytest -q tests/unit/test_cache_runtime_limits.py -k 'lowered_entry or bounded_write or failed_prune or concurrent_bounded'
```

Output:

```text
FFFF...                                                                  [100%]
================================== FAILURES ===================================
______ test_lowered_entry_limit_removes_preexisting_oversized_rows[hit] _______

service = <halo_research_gateway.service.HaloService object at 0x0000018AF16F4200>
trigger = 'hit'

    @pytest.mark.parametrize("trigger", ["hit", "miss", "write", "maintenance"])
    async def test_lowered_entry_limit_removes_preexisting_oversized_rows(service, trigger):
        await store_result(service, "old")
        service.cache.entry_max_bytes = 100
        if trigger == "write":
            await store_result(service, "new")
        elif trigger == "maintenance":
            service.cache.evict()
        else:
            value = service.cache.get("old" if trigger == "hit" else "missing")
>           assert value is None, "Old oversized cache entry was served after lowering the entry limit"
E           AssertionError: Old oversized cache entry was served after lowering the entry limit
E           assert b'{"provider":"fixture","items":[{"title":null,"url":"https://example.org/old","published_at":null,"retrieved_at":"202...cbcdf97661dfbabb97f8acc49ed5e8a936330bd1aef3e0879130b9222273d1733efc5c3876f02a0a14a"}],"warnings":[],"available":null}' is None

tests\unit\test_cache_runtime_limits.py:208: AssertionError
______ test_lowered_entry_limit_removes_preexisting_oversized_rows[miss] ______

service = <halo_research_gateway.service.HaloService object at 0x0000018AF189E390>
trigger = 'miss'

    @pytest.mark.parametrize("trigger", ["hit", "miss", "write", "maintenance"])
    async def test_lowered_entry_limit_removes_preexisting_oversized_rows(service, trigger):
        await store_result(service, "old")
        service.cache.entry_max_bytes = 100
        if trigger == "write":
            await store_result(service, "new")
        elif trigger == "maintenance":
            service.cache.evict()
        else:
            value = service.cache.get("old" if trigger == "hit" else "missing")
            assert value is None, "Old oversized cache entry was served after lowering the entry limit"
>       assert service.cache.stats()["entries"] == 0, "Entry limit ignored for previously stored rows"
E       AssertionError: Entry limit ignored for previously stored rows
E       assert 1 == 0

tests\unit\test_cache_runtime_limits.py:209: AssertionError
_____ test_lowered_entry_limit_removes_preexisting_oversized_rows[write] ______

service = <halo_research_gateway.service.HaloService object at 0x0000018AF189F890>
trigger = 'write'

    @pytest.mark.parametrize("trigger", ["hit", "miss", "write", "maintenance"])
    async def test_lowered_entry_limit_removes_preexisting_oversized_rows(service, trigger):
        await store_result(service, "old")
        service.cache.entry_max_bytes = 100
        if trigger == "write":
            await store_result(service, "new")
        elif trigger == "maintenance":
            service.cache.evict()
        else:
            value = service.cache.get("old" if trigger == "hit" else "missing")
            assert value is None, "Old oversized cache entry was served after lowering the entry limit"
>       assert service.cache.stats()["entries"] == 0, "Entry limit ignored for previously stored rows"
E       AssertionError: Entry limit ignored for previously stored rows
E       assert 1 == 0

tests\unit\test_cache_runtime_limits.py:209: AssertionError
__ test_lowered_entry_limit_removes_preexisting_oversized_rows[maintenance] ___

service = <halo_research_gateway.service.HaloService object at 0x0000018AF189EF00>
trigger = 'maintenance'

    @pytest.mark.parametrize("trigger", ["hit", "miss", "write", "maintenance"])
    async def test_lowered_entry_limit_removes_preexisting_oversized_rows(service, trigger):
        await store_result(service, "old")
        service.cache.entry_max_bytes = 100
        if trigger == "write":
            await store_result(service, "new")
        elif trigger == "maintenance":
            service.cache.evict()
        else:
            value = service.cache.get("old" if trigger == "hit" else "missing")
            assert value is None, "Old oversized cache entry was served after lowering the entry limit"
>       assert service.cache.stats()["entries"] == 0, "Entry limit ignored for previously stored rows"
E       AssertionError: Entry limit ignored for previously stored rows
E       assert 1 == 0

tests\unit\test_cache_runtime_limits.py:209: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_cache_runtime_limits.py::test_lowered_entry_limit_removes_preexisting_oversized_rows[hit]
FAILED tests/unit/test_cache_runtime_limits.py::test_lowered_entry_limit_removes_preexisting_oversized_rows[miss]
FAILED tests/unit/test_cache_runtime_limits.py::test_lowered_entry_limit_removes_preexisting_oversized_rows[write]
FAILED tests/unit/test_cache_runtime_limits.py::test_lowered_entry_limit_removes_preexisting_oversized_rows[maintenance]
4 failed, 3 passed, 15 deselected in 2.05s

```

Exit code: 1.

### Visible-cap assertion RED

Command:

```powershell
uv run --locked python -m pytest -q tests/unit/test_cache_runtime_limits.py -k cache_stats
```

Output:

```text
F                                                                        [100%]
================================== FAILURES ===================================
_________________ test_cache_stats_expose_the_enforced_limits _________________

service = <halo_research_gateway.service.HaloService object at 0x000001F2304A62D0>

    async def test_cache_stats_expose_the_enforced_limits(service):
        stats = service.cache.stats()
>       assert stats.get("max_bytes") == service.cache.max_bytes, "Total cache cap is not visible"
E       AssertionError: Total cache cap is not visible
E       assert None == 1073741824
E        +  where None = <built-in method get of dict object at 0x000001F23080D740>('max_bytes')
E        +    where <built-in method get of dict object at 0x000001F23080D740> = {'entries': 0, 'total_compressed_bytes': 0}.get
E        +  and   1073741824 = <halo_research_gateway.cache.Cache object at 0x000001F23081DDF0>.max_bytes
E        +    where <halo_research_gateway.cache.Cache object at 0x000001F23081DDF0> = <halo_research_gateway.service.HaloService object at 0x000001F2304A62D0>.cache

tests\unit\test_cache_runtime_limits.py:275: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_cache_runtime_limits.py::test_cache_stats_expose_the_enforced_limits
1 failed, 22 deselected in 0.99s

```

Exit code: 1.

### Final focused GREEN

Command:

```powershell
uv run --locked ruff format src/halo_research_gateway/cache.py src/halo_research_gateway/service.py tests/unit/test_cache_runtime_limits.py
uv run --locked python -m pytest -q tests/unit/test_cache_runtime_limits.py tests/unit/test_cache.py tests/unit/test_result_retention.py tests/unit/test_job_continuation.py tests/unit/test_transcript_paging.py
```

Output:

```text
3 files left unchanged
........................................................................ [ 85%]
............                                                             [100%]
84 passed in 8.84s

```

Exit code: 0.

### Full post-change gate

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
382 passed in 75.37s (0:01:15)
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Full)

```

Exit code: 0.

### Real native Windows MCP canary

Command:

```powershell
uv run --locked ruff format tests/acceptance/cache_limits_native_live.py
uv run --locked ruff check src tests
if ($LASTEXITCODE) { exit $LASTEXITCODE }
uv run --locked python tests/acceptance/cache_limits_native_live.py
```

Output:

```text
1 file reformatted
All checks passed!
{"case": "two_native_mcp_clients_shared_cache", "unique_urls": 9, "samples": 111, "peak_compressed_bytes": 3607, "limit": 4096, "retained_entries": 2, "body_chars": 2664, "evicted_source_memory_pages": 11, "recent_source_cache_hit": true}
NATIVE GATEWAY OUTPUT: [09/02/26 22:53:13] INFO     StreamableHTTP      streamable_http_manager.py:148
                             session manager
                             started
[09/02/26 22:53:14] INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     HTTP Request: GET                  _client.py:1740
                             https://docs.python.org/3/library/
                             asyncio-exceptions.html?halo_cache
                             _case=0 "HTTP/1.1 200 OK"
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
[09/02/26 22:53:15] INFO     HTTP Request: GET                  _client.py:1740
                             https://docs.python.org/3/library/
                             asyncio-exceptions.html?halo_cache
                             _case=2 "HTTP/1.1 200 OK"
                    INFO     Terminating session: None   streamable_http.py:814
[09/02/26 22:53:16] INFO     HTTP Request: GET                  _client.py:1740
                             https://docs.python.org/3/library/
                             asyncio-exceptions.html?halo_cache
                             _case=1 "HTTP/1.1 200 OK"
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
[09/02/26 22:53:17] INFO     HTTP Request: GET                  _client.py:1740
                             https://docs.python.org/3/library/
                             asyncio-exceptions.html?halo_cache
                             _case=3 "HTTP/1.1 200 OK"
                    INFO     Terminating session: None   streamable_http.py:814
[09/02/26 22:53:18] INFO     HTTP Request: GET                  _client.py:1740
                             https://docs.python.org/3/library/
                             asyncio-exceptions.html?halo_cache
                             _case=4 "HTTP/1.1 200 OK"
                    INFO     Terminating session: None   streamable_http.py:814
[09/02/26 22:53:19] INFO     HTTP Request: GET                  _client.py:1740
                             https://docs.python.org/3/library/
                             asyncio-exceptions.html?halo_cache
                             _case=5 "HTTP/1.1 200 OK"
                    INFO     Terminating session: None   streamable_http.py:814
[09/02/26 22:53:20] INFO     HTTP Request: GET                  _client.py:1740
                             https://docs.python.org/3/library/
                             asyncio-exceptions.html?halo_cache
                             _case=6 "HTTP/1.1 200 OK"
                    INFO     Terminating session: None   streamable_http.py:814
[09/02/26 22:53:21] INFO     HTTP Request: GET                  _client.py:1740
                             https://docs.python.org/3/library/
                             asyncio-exceptions.html?halo_cache
                             _case=7 "HTTP/1.1 200 OK"
                    INFO     Terminating session: None   streamable_http.py:814
[09/02/26 22:53:22] INFO     HTTP Request: GET                  _client.py:1740
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
NATIVE GATEWAY OUTPUT: [09/02/26 22:53:24] INFO     StreamableHTTP      streamable_http_manager.py:148
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
NATIVE GATEWAY OUTPUT: [09/02/26 22:53:26] INFO     StreamableHTTP      streamable_http_manager.py:148
                             session manager
                             started
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     HTTP Request: GET                  _client.py:1740
                             https://docs.python.org/3/library/
                             asyncio-exceptions.html?halo_cache
                             _case=8 "HTTP/1.1 200 OK"
[09/02/26 22:53:27] INFO     Terminating session: None   streamable_http.py:814
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
