"""Model-copyable cursors must retain the existing evidence and policy checks."""

import hashlib
import json

import pytest

from halo_research_gateway.config import GatewayConfig
from halo_research_gateway.models import EvidenceItem, ProviderResult
from halo_research_gateway.service import HaloService


def service_at(tmp_path):
    config = GatewayConfig()
    config.storage.database = str(tmp_path / "state" / "gateway.db")
    config.storage.backup_directory = str(tmp_path / "backups")
    config.storage.content_directory = str(tmp_path / "content")
    return HaloService(config)


def source(number=0):
    return ProviderResult(
        "fixture",
        [
            EvidenceItem(
                url=f"https://example.org/{number}",
                retrieved_at="2026-09-03T00:00:00Z",
                content=f"source {number} evidence " * 500,
            )
        ],
    )


@pytest.mark.parametrize("cached", [False, True])
async def test_model_cursor_is_short_and_continuation_keeps_all_evidence(tmp_path, cached):
    service = service_at(tmp_path)
    value = source()
    if cached:
        service._cache_result(value, "fixture-public", 3600)
    try:
        first = service._envelope("web_fetch", value, 2000)
        cursor = first["page"]["next_cursor"]
        assert len(cursor) <= 64, "Local model should not have to copy a 300-character state document"
        collected = "".join(item.get("content", "") for item in first["items"])
        pages = 1
        while cursor:
            page = await service.web_fetch(cursor=cursor)
            assert page["ok"], page
            assert len(json.dumps(page, indent=2, ensure_ascii=False)) <= 2000
            assert page["page"]["number"] == pages + 1
            collected += "".join(item.get("content", "") for item in page["items"])
            cursor = page["page"]["next_cursor"]
            assert cursor is None or len(cursor) <= 64
            pages += 1
            assert pages < 200
        assert collected == value.items[0].content
        if not cached:
            assert service.cache.stats()["entries"] == 0, "Private cursor metadata was persisted"
    finally:
        await service.close()


async def test_compact_cursor_metadata_is_bounded_and_visible(tmp_path):
    service = service_at(tmp_path)
    service.config.output.snapshot_max_entries = 2
    try:
        cursors = [service._envelope("web_fetch", source(i), 2000)["page"]["next_cursor"] for i in range(3)]
        stats = service.stats().get("cursor_handles")
        assert stats is not None, "Cursor lookup metadata needs visible bounds"
        assert stats["entries"] == 2
        assert stats["payload_bytes"] <= stats["max_payload_bytes"]
        assert stats["max_entries"] == 2
        assert (await service.web_fetch(cursor=cursors[0]))["error"]["code"] == "CURSOR_EVICTED"
        assert (await service.web_fetch(cursor=cursors[-1]))["ok"]
        await service.close()
        assert service.stats()["cursor_handles"]["entries"] == 0
        assert service.stats()["cursor_handles"]["payload_bytes"] == 0
    finally:
        await service.close()


@pytest.mark.parametrize("cached", [False, True])
async def test_compact_cursor_restart_respects_original_cache_policy(tmp_path, cached):
    service = service_at(tmp_path)
    value = source()
    if cached:
        service._cache_result(value, "fixture-public", 3600)
    first = service._envelope("web_fetch", value, 2000)
    cursor = first["page"]["next_cursor"]
    await service.close()
    assert len(cursor) <= 64
    restarted = service_at(tmp_path)
    try:
        continued = await restarted.web_fetch(cursor=cursor)
        assert continued["ok"] is cached, continued
        if cached:
            assert continued["page"]["number"] == 2
        else:
            assert continued["error"]["code"] == "CURSOR_EVICTED"
    finally:
        await restarted.close()


async def test_compact_cursor_keeps_tamper_expiry_tool_and_budget_validation(tmp_path):
    service = service_at(tmp_path)
    now = [100]
    service.cursors.clock = lambda: now[0]
    try:
        cursor = service._envelope("web_fetch", source(), 2000)["page"]["next_cursor"]
        assert len(cursor) <= 64
        bad = cursor[:-1] + ("A" if cursor[-1] != "A" else "B")
        assert (await service.web_fetch(cursor=bad))["error"]["code"] == "CURSOR_INVALID"
        assert (await service.web_search(cursor=cursor))["error"]["code"] == "CURSOR_INVALID"
        assert (await service.web_fetch(cursor=cursor, max_chars=3000))["error"]["code"] == "CURSOR_INVALID"
        now[0] += service.cursors.ttl_seconds + 1
        assert (await service.web_fetch(cursor=cursor))["error"]["code"] == "CURSOR_EXPIRED"
    finally:
        await service.close()


@pytest.mark.parametrize("pressure", ["total", "entry"])
async def test_tight_cache_uses_legacy_token_without_losing_cached_evidence(tmp_path, pressure):
    service = service_at(tmp_path)
    value = source()
    service._cache_result(value, "fixture-public", 3600)
    before = service.cache.stats()
    if pressure == "total":
        service.cache.max_bytes = before["total_compressed_bytes"]
    else:
        service.cache.entry_max_bytes = 1
    try:
        page = service._envelope("web_fetch", value, 2000)
        token = page["page"]["next_cursor"]
        assert not token.startswith("h1_"), "Inadmissible metadata must use the existing self-contained cursor"
        assert len(json.dumps(page, indent=2, ensure_ascii=False)) <= 2000
        assert service.cache.stats()["entries"] == before["entries"] == 1
        service.cache.entry_max_bytes = before["entry_max_bytes"]
        assert service.cache.get("fixture-public") is not None
        await service.close()
        restarted = service_at(tmp_path)
        try:
            result = await restarted.web_fetch(cursor=token)
            assert result["ok"] and result["page"]["number"] == 2
        finally:
            await restarted.close()
    finally:
        await service.close()


async def test_fitting_persists_only_the_one_returned_handle(tmp_path):
    service = service_at(tmp_path)
    value = source()
    value.items[0].snippet = "large summary " * 300
    service._cache_result(value, "fixture-public", 3600)
    try:
        first = service._envelope("web_fetch", value, 2000)
        assert first["page"]["next_cursor"].startswith("h1_")
        assert first["items"][0]["metadata"]["text_offset"] == 0
        assert service.cache.stats()["entries"] == 2, "Fitting candidates were persisted"
        assert service.stats()["cursor_handles"]["entries"] == 1
    finally:
        await service.close()


@pytest.mark.parametrize("corrupt", ["other_signed_state", "non_ascii", "missing"])
async def test_disk_handle_mapping_cannot_substitute_or_invent_evidence(tmp_path, corrupt):
    service = service_at(tmp_path)
    value = source()
    service._cache_result(value, "fixture-public", 3600)
    token = service._envelope("web_fetch", value, 2000)["page"]["next_cursor"]
    key = "cursor-handle:" + token
    if corrupt == "missing":
        service.cache.delete(key)
    else:
        wrong = service.cursors.encode({"v": 3, "t": "web_fetch", "b": 2000, "s": "wrong"}).encode()
        service.cache.put(key, wrong if corrupt == "other_signed_state" else b"\xff", 3600)
    await service.close()
    restarted = service_at(tmp_path)
    try:
        result = await restarted.web_fetch(cursor=token)
        assert not result["ok"]
        assert result["error"]["code"] == ("CURSOR_EVICTED" if corrupt == "missing" else "CURSOR_INVALID")
        assert not result["items"]
    finally:
        await restarted.close()


async def test_legacy_layout_three_cursor_remains_usable(tmp_path):
    service = service_at(tmp_path)
    value = source()
    try:
        service._envelope("web_fetch", value, 2000)
        legacy = service.cursors.encode(
            {
                "v": 3,
                "t": "web_fetch",
                "b": 2000,
                "k": "",
                "s": hashlib.sha256(service._encode_result(value)).hexdigest(),
                "i": 1,
                "c": 1,
                "n": 2,
            }
        )
        result = await service.web_fetch(cursor=legacy)
        assert result["ok"] and result["page"]["number"] == 2
        assert result["items"][0]["content"] == value.items[0].content[250:500]
    finally:
        await service.close()


async def test_invalid_and_expired_handles_are_rejected_before_disk_lookup(tmp_path):
    service = service_at(tmp_path)
    now = [100]
    service.cursors.clock = lambda: now[0]
    try:
        token = service._envelope("web_fetch", source(), 2000)["page"]["next_cursor"]
        await service.close()

        def no_lookup(*args, **kwargs):
            pytest.fail("Unauthenticated or expired cursor reached storage")

        service.cache.get = no_lookup
        for bad in [
            token + "=",
            token[:-1],
            "h1_" + "!" * 48,
            "h1_" + "é" * 48,
            token[:-1] + ("A" if token[-1] != "A" else "B"),
        ]:
            assert (await service.web_fetch(cursor=bad))["error"]["code"] == "CURSOR_INVALID"
        now[0] += service.cursors.ttl_seconds + 1
        assert (await service.web_fetch(cursor=token))["error"]["code"] == "CURSOR_EXPIRED"
    finally:
        await service.close()


async def test_metadata_byte_bound_and_idle_pruning(tmp_path):
    service = service_at(tmp_path)
    now = [10.0]
    service.clock.monotonic = lambda: now[0]
    service.config.output.snapshot_max_bytes = 600
    service.config.output.cursor_ttl_seconds = 5
    try:
        for i in range(5):
            signed = service.cursors.encode({"i": i, "fixture": "x" * 100})
            assert service._remember_cursor(service.cursors.compact(signed), signed, persist=False)
            assert service.stats()["cursor_handles"]["payload_bytes"] <= 600
        assert service.stats()["cursor_handles"]["entries"] < 5
        now[0] = 16.0
        assert service.stats()["cursor_handles"]["entries"] == 0
        assert service.stats()["cursor_handles"]["payload_bytes"] == 0
        assert service.cache.stats()["entries"] == 0
    finally:
        await service.close()
