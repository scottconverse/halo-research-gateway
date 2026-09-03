"""Regression evidence for sensitive redirects and immutable bounded pagination."""

import hashlib
import json
from types import SimpleNamespace

import pytest

from halo_research_gateway.config import GatewayConfig, OutputConfig
from halo_research_gateway.models import EvidenceItem, ProviderResult
from halo_research_gateway.service import HaloService


def service_at(tmp_path):
    config = GatewayConfig()
    config.storage.database = str(tmp_path / "state" / "gateway.db")
    config.storage.backup_directory = str(tmp_path / "backups")
    config.storage.content_directory = str(tmp_path / "content")
    return HaloService(config)


def test_snapshot_limits_are_operator_configurable():
    fields = OutputConfig.model_fields
    assert "snapshot_max_entries" in fields and "snapshot_max_bytes" in fields, "snapshot budgets are missing"


@pytest.mark.parametrize("field", ["cursor_ttl_seconds", "snapshot_max_entries", "snapshot_max_bytes"])
def test_snapshot_budgets_reject_zero(field):
    accepted = True
    try:
        OutputConfig.model_validate({field: 0})
    except ValueError:
        accepted = False
    assert not accepted, f"{field}=0 was accepted"


@pytest.mark.parametrize("limit", ["entries", "bytes"])
async def test_snapshot_store_evicts_old_non_disk_results_within_budgets(tmp_path, limit):
    service = service_at(tmp_path)
    service.config.output.snapshot_max_entries = 2 if limit == "entries" else 100
    service.config.output.snapshot_max_bytes = 50_000 if limit == "entries" else 15_000
    cursors = []
    try:
        for number in range(3):
            value = ProviderResult(
                "private-fixture",
                [
                    EvidenceItem(
                        url=f"https://example.org/{number}",
                        retrieved_at="2026-09-03T00:00:00Z",
                        content=str(number) * 9000,
                    )
                ],
            )
            result = service._envelope("web_crawl", value, 2000)
            cursors.append(result["page"]["next_cursor"])
        expired = service._resume("web_crawl", cursors[0], None)
        assert not expired["ok"], "old non-cacheable result survived its retention budget"
        assert expired["error"]["code"] == "CURSOR_EVICTED"
        current = service._resume("web_crawl", cursors[-1], None)
        assert current["ok"], current
        stats = service.stats().get("snapshots")
        assert stats is not None, "retained snapshot use is not visible"
        assert stats["entries"] <= service.config.output.snapshot_max_entries
        assert stats["payload_bytes"] <= service.config.output.snapshot_max_bytes
        assert service.cache.stats()["entries"] == 0
    finally:
        await service.close()


async def test_expired_snapshots_are_pruned_and_close_releases_all(tmp_path):
    service = service_at(tmp_path)
    clock = [10.0]
    service.clock.monotonic = lambda: clock[0]
    service.config.output.cursor_ttl_seconds = 5
    source = ProviderResult(
        "fixture",
        [EvidenceItem(url="https://example.org/", retrieved_at="2026-09-03T00:00:00Z", content="original" * 1000)],
    )
    try:
        first = service._envelope("web_crawl", source, 2000)
        clock[0] = 16.0
        gone = service._resume("web_crawl", first["page"]["next_cursor"], None)
        assert not gone["ok"], "expired non-disk snapshot still resumed"
        assert gone["error"]["code"] == "CURSOR_EVICTED"
        assert service.stats()["snapshots"]["entries"] == 0
        service._envelope("web_crawl", source, 2000)
        await service.close()
        assert service.stats()["snapshots"]["payload_bytes"] == 0
    finally:
        await service.close()


async def test_single_result_larger_than_snapshot_budget_fails_explicitly(tmp_path):
    service = service_at(tmp_path)
    service.config.output.snapshot_max_bytes = 2000

    async def fetch(url):
        return ProviderResult(
            "fixture", [EvidenceItem(url=url, retrieved_at="2026-09-03T00:00:00Z", content="x" * 9000)]
        )

    service.http.fetch = fetch
    try:
        result = await service.web_fetch("https://example.org/huge")
        assert not result["ok"], "oversized result exceeded snapshot budget"
        assert result["error"]["code"] == "SNAPSHOT_TOO_LARGE"
        assert service.stats()["snapshots"]["payload_bytes"] == 0
    finally:
        await service.close()


@pytest.mark.parametrize("tool", ["web_fetch", "document_extract"])
async def test_sensitive_final_http_url_is_redacted_and_never_cached(tmp_path, tool):
    service = service_at(tmp_path)
    calls = []
    start = "https://example.org/research"
    final = start + "?token=fixture-redirect-secret&q=public"

    async def download(url, *args):
        calls.append(url)
        return (
            final,
            SimpleNamespace(host="example.org"),
            {"content-type": "text/plain"},
            b"Public research evidence. " * 10,
        )

    service.http.download = download
    try:
        for _ in range(2):
            result = await getattr(service, tool)(start)
            assert result["ok"], result
            assert "fixture-redirect-secret" not in json.dumps(result), "signed redirect leaked into research output"
            assert "SENSITIVE_URL_NOT_CACHED" in result["warnings"]
        assert len(calls) >= 2
        assert service.cache.stats()["entries"] == 0, "sensitive redirect was persisted"
    finally:
        await service.close()


async def test_fetch_ignores_legacy_cache_that_predates_redirect_redaction(tmp_path):
    service = service_at(tmp_path)
    url = "https://example.org/research"
    legacy = ProviderResult(
        "legacy",
        [EvidenceItem(url=url + "?token=legacy-fixture-secret", retrieved_at="2026-09-03T00:00:00Z", content="old")],
    )
    service.cache.put("fetch:" + hashlib.sha256(url.encode()).hexdigest(), service._encode_result(legacy), 3600)

    async def fetch(url):
        return ProviderResult("fresh", [EvidenceItem(url=url, retrieved_at="2026-09-03T01:00:00Z", content="new")])

    service.http.fetch = fetch
    try:
        result = await service.web_fetch(url)
        assert result["provider"] == "fresh", "legacy unsafe cache was served without revalidation"
        assert "legacy-fixture-secret" not in json.dumps(result)
    finally:
        await service.close()


async def test_cursor_keeps_original_evidence_after_same_url_refresh(tmp_path):
    service = service_at(tmp_path)
    calls = 0

    async def fetch(url):
        nonlocal calls
        calls += 1
        return ProviderResult(
            "fixture",
            [
                EvidenceItem(
                    url=url,
                    retrieved_at="2026-09-03T00:00:00Z",
                    content=("ORIGINAL " if calls == 1 else "REPLACEMENT ") * 1200,
                )
            ],
        )

    service.http.fetch = fetch
    try:
        first = await service.web_fetch("https://example.org/research", max_chars=2000)
        cursor = first["page"]["next_cursor"]
        assert cursor
        refreshed = await service.web_fetch("https://example.org/research", max_chars=2000, max_age_seconds=0)
        assert refreshed["ok"] and calls == 2
        continued = await service.web_fetch(cursor=cursor)
        assert continued["ok"], continued
        assert "ORIGINAL" in continued["items"][0]["content"], "cursor silently switched to replacement evidence"
        assert "REPLACEMENT" not in json.dumps(continued)
    finally:
        await service.close()


async def test_cursor_snapshot_cannot_be_mutated_by_provider_after_return(tmp_path):
    service = service_at(tmp_path)
    source = ProviderResult(
        "fixture",
        [
            EvidenceItem(
                url="https://example.org/research", retrieved_at="2026-09-03T00:00:00Z", content="ORIGINAL " * 1200
            )
        ],
    )

    async def fetch(url):
        return source

    service.http.fetch = fetch
    try:
        first = await service.web_fetch(source.items[0].url, max_chars=2000)
        source.items[0].content = "MUTATED " * 1200
        continued = await service.web_fetch(cursor=first["page"]["next_cursor"])
        assert continued["ok"], continued
        assert "ORIGINAL" in continued["items"][0]["content"], "stored snapshot retained mutable provider objects"
    finally:
        await service.close()


@pytest.mark.parametrize("budget", [2000, 4000, 6000])
async def test_all_cursor_pages_retain_every_content_character(tmp_path, budget):
    service = service_at(tmp_path)
    expected = "Research evidence: alpha beta gamma.\n" * 250

    async def fetch(url):
        return ProviderResult("fixture", [EvidenceItem(url=url, retrieved_at="2026-09-03T00:00:00Z", content=expected)])

    service.http.fetch = fetch
    try:
        result = await service.web_fetch("https://example.org/research", max_chars=budget)
        text = ""
        pages = 0
        while True:
            assert result["ok"], result
            assert len(json.dumps(result, indent=2, ensure_ascii=False)) <= budget
            text += "".join(item.get("content", "") for item in result["items"])
            pages += 1
            cursor = result["page"]["next_cursor"]
            if not cursor:
                break
            assert pages < 300, "pagination did not make forward progress"
            result = await service.web_fetch(cursor=cursor)
        assert len(text) == len(expected), f"pagination lost {len(expected) - len(text)} evidence characters"
        assert text == expected
    finally:
        await service.close()


@pytest.mark.parametrize("replace_cache", [False, True])
async def test_restart_resumes_only_matching_cached_evidence(tmp_path, replace_cache):
    service = service_at(tmp_path)
    url = "https://example.org/research"

    async def fetch(url):
        return ProviderResult(
            "fixture", [EvidenceItem(url=url, retrieved_at="2026-09-03T00:00:00Z", content="ORIGINAL " * 1000)]
        )

    service.http.fetch = fetch
    first = await service.web_fetch(url, max_chars=2000)
    if replace_cache:
        changed = ProviderResult(
            "fixture", [EvidenceItem(url=url, retrieved_at="2026-09-03T01:00:00Z", content="REPLACED " * 1000)]
        )
        service.cache.put(first["cache"]["key"], service._encode_result(changed), 3600)
    await service.close()
    restarted = service_at(tmp_path)
    try:
        result = await restarted.web_fetch(cursor=first["page"]["next_cursor"])
        if replace_cache:
            assert not result["ok"] and result["error"]["code"] == "CURSOR_EVICTED", result
        else:
            assert result["ok"] and "ORIGINAL" in result["items"][0]["content"], result
    finally:
        await restarted.close()


async def test_noncacheable_cursor_cannot_recover_from_an_older_disk_entry(tmp_path):
    service = service_at(tmp_path)
    source = ProviderResult(
        "private-fixture",
        [
            EvidenceItem(
                url="https://example.org/research",
                retrieved_at="2026-09-03T00:00:00Z",
                content="private fixture evidence " * 400,
            )
        ],
    )
    service.cache.put("private-fixture-key", service._encode_result(source), 3600)

    async def operation():
        return source

    value = await service._cached_run("http", "fixture", "private-fixture-key", 3600, operation, cacheable=False)
    first = service._envelope("web_crawl", value, 2000)
    await service.close()
    restarted = service_at(tmp_path)
    try:
        result = restarted._resume("web_crawl", first["page"]["next_cursor"], None)
        assert not result["ok"], "non-cacheable cursor recovered an old disk entry"
        assert result["error"]["code"] == "CURSOR_EVICTED"
    finally:
        await restarted.close()


@pytest.mark.parametrize("kind", ["snippet", "both", "unicode"])
async def test_pagination_preserves_snippet_and_content_without_duplication(tmp_path, kind):
    service = service_at(tmp_path)
    snippet = "Brief source summary. " * 20
    content = "Complete research source text. " * 300
    if kind == "snippet":
        snippet, content = snippet * 20, ""
    elif kind == "unicode":
        snippet, content = '"\\\n é 研究 🔎 "' * 80, "Research\t\n📚" * 600

    async def fetch(url):
        return ProviderResult(
            "fixture", [EvidenceItem(url=url, retrieved_at="2026-09-03T00:00:00Z", snippet=snippet, content=content)]
        )

    service.http.fetch = fetch
    try:
        page = await service.web_fetch("https://example.org/", max_chars=2000)
        contents, snippets = [], []
        for _ in range(300):
            assert page["ok"], page
            wire = json.dumps(page, indent=2, ensure_ascii=False)
            assert len(wire) == page["page"]["serialized_chars"] <= 2000
            contents.extend(item.get("content") or "" for item in page["items"])
            snippets.extend(item.get("snippet") or "" for item in page["items"])
            if not page["page"]["next_cursor"]:
                break
            page = await service.web_fetch(cursor=page["page"]["next_cursor"])
        else:
            pytest.fail("pagination did not terminate")
        assert "".join(contents) == content
        assert len("".join(snippets)) == len(snippet), "snippet was repeated on content chunks"
        assert "".join(snippets) == snippet
    finally:
        await service.close()


@pytest.mark.parametrize("field", ["url", "metadata"])
async def test_oversized_non_prose_fields_fail_with_a_bounded_error(tmp_path, field):
    service = service_at(tmp_path)
    item = EvidenceItem(url="https://example.org/", retrieved_at="2026-09-03T00:00:00Z", content="evidence")
    if field == "url":
        item.url += "long-path-" * 1000
    else:
        item.metadata = {"large_field": "fixture" * 2000}

    async def fetch(url):
        return ProviderResult("fixture", [item])

    service.http.fetch = fetch
    try:
        result = await service.web_fetch("https://example.org/", max_chars=2000)
        assert not result["ok"] and result["error"]["code"] == "OUTPUT_ITEM_TOO_LARGE", result
        assert len(json.dumps(result, indent=2)) <= 2000
        assert "large_field" not in json.dumps(result)
    finally:
        await service.close()


async def test_snapshot_accounting_uses_utf8_bytes_and_deduplicates_payloads(tmp_path):
    service = service_at(tmp_path)
    source = ProviderResult(
        "fixture",
        [EvidenceItem(url="https://example.org/", retrieved_at="2026-09-03T00:00:00Z", content="研究📚" * 1000)],
    )
    size = len(service._encode_result(source))
    service.config.output.snapshot_max_bytes = size
    try:
        for _ in range(3):
            service._envelope("web_fetch", source, 6000)
        stats = service.stats()["snapshots"]
        assert stats["entries"] == 1 and stats["payload_bytes"] == size
    finally:
        await service.close()


async def test_legacy_document_cache_and_unbound_cursor_are_not_served(tmp_path):
    service = service_at(tmp_path)
    url = "https://example.org/research"
    key = "document:v2:" + hashlib.sha256(json.dumps([url, None, True, "auto"]).encode()).hexdigest()
    unsafe = ProviderResult(
        "legacy", [EvidenceItem(url=url + "?token=legacy-fixture", retrieved_at="2026-09-03T00:00:00Z", content="old")]
    )
    service.cache.put(key, service._encode_result(unsafe), 3600)

    async def extract(url, *args, **kwargs):
        return ProviderResult("fresh", [EvidenceItem(url=url, retrieved_at="2026-09-03T00:00:00Z", content="new")])

    service.documents.extract = extract
    try:
        result = await service.document_extract(url)
        assert result["ok"] and result["provider"] == "fresh"
        legacy = service.cursors.encode(
            {"tool": "document_extract", "schema": "1.5", "snapshot": key, "budget": 2000, "i": 0, "c": 0, "n": 2}
        )
        rejected = await service.document_extract(cursor=legacy)
        assert not rejected["ok"] and rejected["error"]["code"] == "CURSOR_EVICTED"
        assert service.cache.get(key) is not None, "historical cache was unexpectedly scrubbed"
    finally:
        await service.close()
