import json
import urllib.parse
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from mcp.server.mcpserver import Context

from halo_research_gateway.app import create_application
from halo_research_gateway.config import GatewayConfig, OutputProfile
from halo_research_gateway.models import EvidenceItem, ProviderResult
from halo_research_gateway.providers.community import CommunityProvider
from halo_research_gateway.providers.transcripts import TranscriptProvider
from halo_research_gateway.security import validate_url
from halo_research_gateway.service import HaloService


class FixedClock:
    def utcnow(self):
        return datetime(2026, 9, 1, 12, 0, tzinfo=UTC)


class FakeHttp:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    async def download(self, url, accept=None):
        self.calls.append((url, accept))
        for fragment, content_type, value in self.responses:
            if fragment in url:
                body = value if isinstance(value, bytes) else value.encode()
                return url, validate_url(url), {"content-type": content_type}, body
        raise AssertionError(f"unexpected public request: {url}")


class FakeGitHub:
    def __init__(self, result=None):
        self.result = result or ProviderResult("github-public", [], ["GITHUB_AUTH_NOT_CONFIGURED"], 0)
        self.calls = []

    async def research(self, query, repository, kinds, ref, max_results):
        self.calls.append((query, repository, kinds, ref, max_results))
        return self.result


class FakeSearch:
    def __init__(self, result=None):
        self.result = result or ProviderResult("fixture-search", [], [], 0)
        self.calls = []

    async def search(self, query, **values):
        self.calls.append((query, values))
        return self.result


def youtube_page(player):
    return "<html><script>ytInitialPlayerResponse = " + json.dumps(player) + ";</script></html>"


@pytest.mark.asyncio
async def test_transcript_selects_human_track_and_normalizes_caption_metadata():
    player = {
        "videoDetails": {"videoId": "abc123", "title": "Fixture talk", "author": "Fixture channel"},
        "microformat": {"playerMicroformatRenderer": {"publishDate": "2026-08-30"}},
        "captions": {
            "playerCaptionsTracklistRenderer": {
                "captionTracks": [
                    {
                        "baseUrl": "https://www.youtube.com/api/timedtext?v=abc123&lang=en&kind=asr",
                        "languageCode": "en",
                        "kind": "asr",
                        "name": {"simpleText": "English (auto-generated)"},
                    },
                    {
                        "baseUrl": "https://www.youtube.com/api/timedtext?v=abc123&lang=fr",
                        "languageCode": "fr",
                        "name": {"simpleText": "French"},
                    },
                ]
            }
        },
    }
    captions = """<transcript>
      <text start="1.5" dur="2.25">Bonjour &amp; bienvenue</text>
      <text start="4" dur="1">Deuxième ligne</text>
    </transcript>"""
    http = FakeHttp(
        [
            ("watch?v=abc123", "text/html; charset=utf-8", youtube_page(player)),
            ("lang=fr", "text/xml; charset=utf-8", captions),
        ]
    )

    result = await TranscriptProvider(http, FixedClock()).fetch(
        "https://www.youtube.com/watch?v=abc123#chapter", None, True
    )

    assert result.warnings == []
    assert result.available == 2
    assert len(result.items) == 1
    item = result.items[0]
    assert item.url == "https://www.youtube.com/watch?v=abc123"
    assert item.title == "Fixture talk"
    assert item.published_at == "2026-08-30"
    assert item.source == "youtube.com"
    assert item.content == "[00:01.500 --> 00:03.750] Bonjour & bienvenue\n[00:04.000 --> 00:05.000] Deuxième ligne"
    assert item.metadata == {
        "publisher": "Fixture channel",
        "language": "fr",
        "language_name": "French",
        "auto_generated": False,
        "segment_count": 2,
        "segments": [
            {"start_seconds": 1.5, "end_seconds": 3.75, "text": "Bonjour & bienvenue"},
            {"start_seconds": 4.0, "end_seconds": 5.0, "text": "Deuxième ligne"},
        ],
    }
    assert all("audio" not in url and "video" not in url for url, _ in http.calls[1:])


@pytest.mark.asyncio
async def test_transcript_honors_language_then_reports_unavailable_honestly():
    player = {
        "videoDetails": {"videoId": "missing", "title": "No captions", "author": "Publisher"},
    }
    http = FakeHttp([("watch?v=missing", "text/html", youtube_page(player))])

    result = await TranscriptProvider(http, FixedClock()).fetch(
        "https://www.youtube.com/watch?v=missing", "es-MX", True
    )

    assert result.items == []
    assert result.available == 0
    assert result.warnings == ["TRANSCRIPT_UNAVAILABLE"]
    assert len(http.calls) == 1


@pytest.mark.asyncio
async def test_transcript_never_downloads_direct_media_and_rejects_media_content_type():
    direct = FakeHttp([("clip.mp4", "video/mp4", b"not really a media payload")])
    content_typed = FakeHttp([("watch?id=media", "audio/mpeg", b"not really an audio payload")])
    track_page = youtube_page(
        {
            "captions": {
                "playerCaptionsTracklistRenderer": {
                    "captionTracks": [
                        {
                            "baseUrl": "https://media.example/captions.mp4",
                            "languageCode": "en",
                            "name": {"simpleText": "malformed media track"},
                        }
                    ]
                }
            }
        }
    )
    media_track = FakeHttp(
        [
            ("watch?id=track", "text/html", track_page),
            ("captions.mp4", "video/mp4", b"must not be requested"),
        ]
    )

    direct_result = await TranscriptProvider(direct, FixedClock()).fetch(
        "https://media.example/clip.mp4?download=1", None, True
    )
    typed_result = await TranscriptProvider(content_typed, FixedClock()).fetch(
        "https://media.example/watch?id=media", None, True
    )
    track_result = await TranscriptProvider(media_track, FixedClock()).fetch(
        "https://media.example/watch?id=track", None, True
    )

    assert direct_result.warnings == ["TRANSCRIPT_UNAVAILABLE"]
    assert direct.calls == []
    assert typed_result.warnings == ["TRANSCRIPT_UNAVAILABLE"]
    assert len(content_typed.calls) == 1
    assert track_result.warnings == ["TRANSCRIPT_UNAVAILABLE"]
    assert len(media_track.calls) == 1


@pytest.mark.asyncio
async def test_community_search_uses_structured_apis_freshness_and_preserves_signals():
    stack_payload = {
        "items": [
            {
                "question_id": 123,
                "title": "Bounded queues",
                "link": "https://stackoverflow.com/questions/123/bounded-queues",
                "body": "<p>How should queues be bounded?</p>",
                "score": 17,
                "answer_count": 3,
                "is_answered": True,
                "accepted_answer_id": 456,
                "owner": {"display_name": "Ada"},
                "creation_date": 1788170400,
                "last_activity_date": 1788174000,
            }
        ],
        "has_more": False,
        "quota_remaining": 299,
    }
    hn_payload = {
        "hits": [
            {
                "objectID": "99",
                "title": "Fair schedulers",
                "url": "https://example.org/fair",
                "story_text": "A discussion of fair schedulers",
                "points": 42,
                "num_comments": 8,
                "author": "grace",
                "created_at": "2026-08-31T08:00:00Z",
                "created_at_i": 1788163200,
            }
        ],
        "nbHits": 1,
    }
    http = FakeHttp(
        [
            ("api.stackexchange.com/2.3/search/advanced", "application/json", json.dumps(stack_payload)),
            ("hn.algolia.com/api/v1/search", "application/json", json.dumps(hn_payload)),
        ]
    )
    provider = CommunityProvider(http, FakeGitHub(), FakeSearch(), FixedClock())

    result = await provider.search("fair bounded queues", ["stackoverflow", "hackernews"], 2, 7)

    assert len(result.items) == 2
    assert {item.source for item in result.items} == {"stackoverflow.com", "news.ycombinator.com"}
    stack = next(item for item in result.items if item.source == "stackoverflow.com")
    assert stack.content == "How should queues be bounded?"
    assert stack.metadata == {
        "community_source": "stackoverflow",
        "question_id": 123,
        "author": "Ada",
        "score": 17,
        "answer_count": 3,
        "is_answered": True,
        "accepted_answer_id": 456,
        "last_activity_at": "2026-08-31T11:00:00Z",
    }
    hn = next(item for item in result.items if item.source == "news.ycombinator.com")
    assert hn.url == "https://news.ycombinator.com/item?id=99"
    assert hn.metadata["score"] == 42
    assert hn.metadata["reply_count"] == 8
    stack_query = urllib.parse.parse_qs(urllib.parse.urlsplit(http.calls[0][0]).query)
    hn_query = urllib.parse.parse_qs(urllib.parse.urlsplit(http.calls[1][0]).query)
    assert stack_query["pagesize"] == ["2"]
    assert "fromdate" in stack_query
    assert hn_query["hitsPerPage"] == ["2"]
    assert hn_query["numericFilters"][0].startswith("created_at_i>")


@pytest.mark.asyncio
async def test_community_threads_preserve_stack_answers_and_hacker_news_nesting():
    stack_question = {
        "items": [
            {
                "question_id": 123,
                "title": "Question root",
                "link": "https://stackoverflow.com/questions/123/question-root",
                "body": "<p>Question body</p>",
                "score": 5,
                "answer_count": 1,
                "owner": {"display_name": "questioner"},
                "creation_date": 1788160000,
            }
        ]
    }
    stack_answers = {
        "items": [
            {
                "answer_id": 456,
                "question_id": 123,
                "body": "<p>Accepted answer</p>",
                "score": 12,
                "is_accepted": True,
                "owner": {"display_name": "answerer"},
                "creation_date": 1788161000,
            }
        ],
        "has_more": False,
    }
    hn_item = {
        "id": 99,
        "title": "HN root",
        "text": "Root text",
        "points": 20,
        "author": "root",
        "created_at": "2026-08-31T08:00:00Z",
        "children": [
            {
                "id": 100,
                "text": "First reply",
                "points": 7,
                "author": "child",
                "created_at": "2026-08-31T08:01:00Z",
                "children": [
                    {
                        "id": 101,
                        "text": "Nested reply",
                        "points": 1,
                        "author": "nested",
                        "created_at": "2026-08-31T08:02:00Z",
                        "children": [],
                    }
                ],
            }
        ],
    }
    http = FakeHttp(
        [
            ("/questions/123/answers", "application/json", json.dumps(stack_answers)),
            ("/questions/123?", "application/json", json.dumps(stack_question)),
            ("hn.algolia.com/api/v1/items/99", "application/json", json.dumps(hn_item)),
        ]
    )
    provider = CommunityProvider(http, FakeGitHub(), FakeSearch(), FixedClock())

    stack = await provider.thread("https://stackoverflow.com/questions/123/question-root", 1, "top")
    hacker_news = await provider.thread("https://news.ycombinator.com/item?id=99", 2, "source_default")

    assert [item.url for item in stack.items] == [
        "https://stackoverflow.com/questions/123/question-root",
        "https://stackoverflow.com/a/456",
    ]
    assert stack.items[1].metadata["is_accepted"] is True
    assert stack.items[1].metadata["parent_id"] == 123
    assert [item.metadata["depth"] for item in hacker_news.items] == [0, 1, 2]
    assert [item.metadata["parent_id"] for item in hacker_news.items[1:]] == [99, 100]
    assert hacker_news.items[2].url == "https://news.ycombinator.com/item?id=101"


@pytest.mark.asyncio
async def test_github_discussions_hands_off_or_returns_an_honest_partial_warning():
    github = FakeGitHub()
    provider = CommunityProvider(FakeHttp([]), github, FakeSearch(), FixedClock())

    result = await provider.thread("https://github.com/acme/widgets/discussions/77", 10, "source_default")

    assert github.calls == [("77", "acme/widgets", ["discussions"], None, 11)]
    assert result.items == []
    assert set(result.warnings) == {
        "GITHUB_AUTH_NOT_CONFIGURED",
        "GITHUB_DISCUSSIONS_UNAVAILABLE",
    }


@pytest.mark.asyncio
async def test_mcp_tools_forward_structured_arguments_and_client_identity(tmp_path):
    config = GatewayConfig()
    config.storage.database = str(tmp_path / "gateway.db")
    config.storage.backup_directory = str(tmp_path / "backups")
    config.storage.content_directory = str(tmp_path / "content")
    config.output.profiles["known-planner"] = OutputProfile()
    app = create_application(config)
    service = app.state.halo_service
    calls = []

    async def transcript_fetch(url, language, prefer_human, max_chars, cursor, client):
        calls.append(("transcript", url, language, prefer_human, max_chars, cursor, client))
        return {"path": "transcript"}

    async def community_search(query, sources, max_results, freshness_days, max_chars, cursor, client):
        calls.append(("search", query, sources, max_results, freshness_days, max_chars, cursor, client))
        return {"path": "search"}

    async def community_thread(url, max_replies, sort, max_chars, cursor, client):
        calls.append(("thread", url, max_replies, sort, max_chars, cursor, client))
        return {"path": "thread"}

    async def legacy(*args, **kwargs):
        del args, kwargs
        return {"path": "legacy", "ok": True, "warnings": []}

    service.transcript_fetch = transcript_fetch
    service.community_search = community_search
    service.community_thread = community_thread
    service.web_fetch = legacy
    service.web_search = legacy
    service.reddit_thread = legacy
    context = Context(
        request_context=SimpleNamespace(request=SimpleNamespace(headers={"X-Halo-Client": "known-planner"})),
        mcp_server=app.state.mcp_server,
    )
    try:
        transcript = await app.state.mcp_server._tool_manager.call_tool(
            "transcript_fetch",
            {
                "url": "https://www.youtube.com/watch?v=abc",
                "language": "en-US",
                "prefer_human": False,
                "max_chars": 4000,
            },
            context,
        )
        search = await app.state.mcp_server._tool_manager.call_tool(
            "community_search",
            {
                "query": "bounded queues",
                "sources": ["stackoverflow", "hackernews"],
                "max_results": 7,
                "freshness_days": 30,
                "max_chars": 4000,
            },
            context,
        )
        thread = await app.state.mcp_server._tool_manager.call_tool(
            "community_thread",
            {
                "url": "https://news.ycombinator.com/item?id=99",
                "max_replies": 12,
                "sort": "oldest",
                "max_chars": 4000,
            },
            context,
        )
    finally:
        await service.close()

    assert transcript == {"path": "transcript"}
    assert search == {"path": "search"}
    assert thread == {"path": "thread"}
    assert calls == [
        ("transcript", "https://www.youtube.com/watch?v=abc", "en-US", False, 4000, None, "known-planner"),
        ("search", "bounded queues", ["stackoverflow", "hackernews"], 7, 30, 4000, None, "known-planner"),
        ("thread", "https://news.ycombinator.com/item?id=99", 12, "oldest", 4000, None, "known-planner"),
    ]


def make_service(tmp_path):
    config = GatewayConfig()
    config.storage.database = str(tmp_path / "gateway.db")
    config.storage.backup_directory = str(tmp_path / "backups")
    config.storage.content_directory = str(tmp_path / "content")
    return HaloService(config)


@pytest.mark.asyncio
async def test_service_caches_public_transcript_packet_and_rejects_sensitive_url(tmp_path):
    service = make_service(tmp_path)

    class FakeTranscripts:
        def __init__(self):
            self.calls = []

        async def fetch(self, url, language, prefer_human):
            self.calls.append((url, language, prefer_human))
            return ProviderResult(
                "fixture-transcript",
                [
                    EvidenceItem(
                        url=url,
                        retrieved_at="2026-09-01T12:00:00Z",
                        source="media.example",
                        content="[00:00.000 --> 00:01.000] fixture",
                    )
                ],
                [],
                1,
            )

    fake = FakeTranscripts()
    service.transcripts = fake
    try:
        first = await service.transcript_fetch("https://media.example/talk", "en", True, 6000, None, "known-planner")
        second = await service.transcript_fetch("https://media.example/talk", "en", True, 6000, None, "known-planner")
        sensitive = await service.transcript_fetch(
            "https://media.example/talk?token=do-not-expose", "en", True, 6000, None, "known-planner"
        )
    finally:
        await service.close()

    assert first["tool"] == "transcript_fetch"
    assert first["provider"] == "fixture-transcript"
    assert second["cache"]["hit"] is True
    assert fake.calls == [("https://media.example/talk", "en", True)]
    assert sensitive["ok"] is False
    assert sensitive["error"]["code"] == "SENSITIVE_URL_NOT_ALLOWED"
    assert "do-not-expose" not in json.dumps(sensitive)


@pytest.mark.asyncio
async def test_service_never_caches_github_discussion_and_rejects_unsafe_thread(tmp_path):
    service = make_service(tmp_path)

    class FakeCommunity:
        def __init__(self):
            self.calls = []

        async def thread(self, url, max_replies, sort):
            self.calls.append((url, max_replies, sort))
            return ProviderResult(
                "fixture-github",
                [
                    EvidenceItem(
                        url=url,
                        retrieved_at="2026-09-01T12:00:00Z",
                        source="github.com",
                        content="private-policy-safe fixture",
                        metadata={"authenticated_source": True},
                    )
                ],
                [],
                1,
            )

    fake = FakeCommunity()
    service.community = fake
    url = "https://github.com/acme/widgets/discussions/77"
    try:
        first = await service.community_thread(url, 10, "source_default", 6000, None, "known-planner")
        second = await service.community_thread(url, 10, "source_default", 6000, None, "known-planner")
        unsafe = await service.community_thread(
            "http://127.0.0.1/thread", 10, "source_default", 6000, None, "known-planner"
        )
    finally:
        await service.close()

    assert first["ok"] is True
    assert second["cache"]["hit"] is False
    assert fake.calls == [(url, 10, "source_default"), (url, 10, "source_default")]
    assert unsafe["ok"] is False
    assert unsafe["error"]["code"] == "UNSAFE_URL"
