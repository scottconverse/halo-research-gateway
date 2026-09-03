"""Job request admission and the complete MCP status response must be finite."""

import json
import sqlite3

import pytest
from test_job_errors import app as app
from test_job_errors import call

from halo_research_gateway.models import EvidenceItem


@pytest.mark.parametrize("case", ["question", "profile", "extra", "nested", "override", "cursor", "job_id"])
async def test_unbounded_or_ignored_job_fields_are_rejected_before_creation(app, case):
    service = app.state.halo_service
    scheduled = []
    service._schedule_job = lambda *args: scheduled.append(args)
    args = {"operation": "create", "question": "bounded public research"}
    if case == "question":
        args["question"] = "x" * 8193
    elif case == "profile":
        args["profile"] = "x" * 65
    elif case in {"extra", "nested", "override"}:
        args["limits"] = {
            "extra": {"unrecognized": "x" * 10000},
            "nested": {"max_pages": {"unrecognized": "x" * 10000}},
            "override": {"profile": "different"},
        }[case]
    elif case == "cursor":
        args["cursor"] = "ignored-cursor"
    else:
        args["job_id"] = "x" * 129
    reply = await call(app, args)
    assert reply.get("ok") is False, "Invalid job request was accepted"
    assert reply["error"]["code"] in {"INVALID_ARGUMENT", "INVALID_JOB_LIMITS"}
    assert service.jobs.list() == [] and scheduled == []
    assert len(json.dumps(reply, indent=2, ensure_ascii=False)) <= 2000


@pytest.mark.parametrize("budget", [2000, 4000, 6000])
async def test_complete_job_status_obeys_requested_budget_and_keeps_all_evidence(app, budget):
    service = app.state.halo_service
    question = "Research question with Unicode: \u03bb " * 200
    source = "https://example.org/bounded-job"
    content = "Every piece of this research evidence must be retained. \u03bb\n" * 200
    job = service.jobs.create("unidentified", question, {"max_sources": 2, "max_pages": 3, "timeout_seconds": 30})
    service.jobs.start(job["job_id"], "unidentified", 30)
    service.jobs.checkpoint(
        job["job_id"],
        "unidentified",
        {
            "items": [EvidenceItem(url=source, retrieved_at="2026-09-03T00:00:00Z", content=content).as_dict()],
            "frontier": [],
            "position": 0,
            "attempted": 1,
            "elapsed_seconds": 0.5,
            "search_complete": True,
            "warnings": ["PARTIAL_FIXTURE"],
        },
        service.config.storage.entry_max_bytes,
    )
    service.jobs.transition(job["job_id"], "unidentified", "pause")
    reply = await call(app, {"operation": "status", "job_id": job["job_id"], "max_chars": budget})
    assert len(json.dumps(reply, indent=2, ensure_ascii=False)) <= budget, "Whole status exceeded MCP budget"
    assert reply["state"] == "paused" and reply["job_id"] == job["job_id"]
    assert reply["request"]["question_truncated"] is True
    assert service.jobs.status(job["job_id"], "unidentified")["request"]["question"] == question
    page = reply["progress"]["result"]
    collected, count = "", 0
    while True:
        assert page["ok"]
        if not page["items"]:
            assert count == 0 and page["page"]["next_cursor"]
            assert page["coverage"]["returned_this_page"] == 0 and not page["coverage"]["complete"]
        assert "PARTIAL_FIXTURE" in page["warnings"]
        collected += "".join(item.get("content") or "" for item in page["items"])
        cursor = page["page"]["next_cursor"]
        if not cursor:
            break
        # Continuations may omit the size or use the caller's supported budget.
        page = await service.deep_research(cursor=cursor, max_chars=budget if count % 2 == 0 else None)
        count += 1
        assert count < 100
    assert collected == content


async def test_largest_accepted_question_is_preserved_but_creation_reply_is_bounded(app):
    service = app.state.halo_service
    service._schedule_job = lambda *args: None
    question = "\u03bb" * 8192
    reply = await call(app, {"operation": "create", "question": question, "max_chars": 2000})
    assert len(json.dumps(reply, indent=2, ensure_ascii=False)) <= 2000
    assert reply["state"] == "queued"
    assert service.jobs.status(reply["job_id"], "unidentified")["request"]["question"] == question


@pytest.mark.parametrize("case", ["metadata", "retention", "legacy"])
async def test_format_failure_preserves_successful_control_identity_and_state(app, case):
    service = app.state.halo_service
    job = service.jobs.create("unidentified", "fixture", {"timeout_seconds": 30})
    service.jobs.start(job["job_id"], "unidentified", 30)
    if case == "legacy":
        with sqlite3.connect(service.config.storage.database) as db:
            db.execute(
                "UPDATE jobs SET progress_json=? WHERE job_id=?",
                (json.dumps({"result": {"legacy": "x" * 10000}}), job["job_id"]),
            )
        operation, expected_state = "cancel", "cancelled"
    else:
        item = EvidenceItem(
            url="https://example.org/fixture", retrieved_at="2026-09-03T00:00:00Z", content="source " * 100
        )
        if case == "metadata":
            item.title = "oversized title " * 1000
        else:
            service.config.output.snapshot_max_bytes = 1
        service.jobs.checkpoint(
            job["job_id"], "unidentified", {"items": [item.as_dict()]}, service.config.storage.entry_max_bytes
        )
        operation, expected_state = "pause", "paused"
    try:
        reply = await call(app, {"operation": operation, "job_id": job["job_id"], "max_chars": 2000})
    except Exception:
        reply = {}
    assert reply.get("job_id") == job["job_id"], "Formatting hid the successful job-control operation"
    assert reply["state"] == expected_state
    assert len(json.dumps(reply, indent=2, ensure_ascii=False)) <= 2000
    assert reply["progress"]["partial"] is True
    assert reply["progress"]["result"]["ok"] is False
