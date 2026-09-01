"""Bounded public caption retrieval without downloading media payloads."""

from __future__ import annotations

import html
import json
import re
import urllib.parse
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any

from ..clock import rfc3339
from ..models import EvidenceItem, ProviderResult
from ..security import validate_url

MAX_SEGMENTS = 5_000
MAX_METADATA_SEGMENTS = 200
CAPTION_CONTENT_TYPES = {
    "application/ttml+xml",
    "application/x-subrip",
    "application/xml",
    "text/plain",
    "text/vtt",
    "text/xml",
}
MEDIA_EXTENSIONS = {
    ".aac",
    ".avi",
    ".flac",
    ".m3u8",
    ".m4a",
    ".m4v",
    ".mkv",
    ".mov",
    ".mp3",
    ".mp4",
    ".mpeg",
    ".mpg",
    ".oga",
    ".ogg",
    ".ogv",
    ".opus",
    ".ts",
    ".wav",
    ".webm",
    ".wma",
    ".wmv",
}


@dataclass(slots=True)
class CaptionTrack:
    url: str
    language: str | None = None
    name: str | None = None
    auto_generated: bool = False


class _PageMetadata(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title: str | None = None
        self.publisher: str | None = None
        self.date: str | None = None
        self.canonical: str | None = None
        self.tracks: list[CaptionTrack] = []
        self._inside_title = False
        self._title_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.casefold(): value for key, value in attrs if value is not None}
        if tag.casefold() == "title":
            self._inside_title = True
        elif tag.casefold() == "link" and values.get("rel", "").casefold() == "canonical":
            self.canonical = values.get("href")
        elif tag.casefold() == "meta":
            key = (values.get("property") or values.get("name") or "").casefold()
            value = values.get("content")
            if key in {"og:title", "twitter:title"} and value:
                self.title = value
            elif key in {"og:site_name", "author", "publisher"} and value:
                self.publisher = value
            elif key in {"article:published_time", "date", "upload_date"} and value:
                self.date = value
        elif tag.casefold() == "track" and values.get("src"):
            kind = values.get("kind", "subtitles").casefold()
            if kind in {"captions", "subtitles"}:
                self.tracks.append(
                    CaptionTrack(
                        values["src"],
                        values.get("srclang"),
                        values.get("label"),
                        "auto" in values.get("label", "").casefold(),
                    )
                )

    def handle_endtag(self, tag: str) -> None:
        if tag.casefold() == "title":
            self._inside_title = False
            if self.title is None:
                value = "".join(self._title_parts).strip()
                self.title = value or None

    def handle_data(self, data: str) -> None:
        if self._inside_title:
            self._title_parts.append(data)


def _decode(headers: dict[str, str], body: bytes) -> str:
    content_type = headers.get("content-type", "")
    match = re.search(r"charset=([^;\s]+)", content_type, flags=re.IGNORECASE)
    return body.decode(match.group(1).strip("\"'") if match else "utf-8", errors="replace")


def _json_object_after(text: str, marker: str) -> dict[str, Any] | None:
    position = text.find(marker)
    while position >= 0:
        start = text.find("{", position + len(marker))
        if start < 0:
            return None
        try:
            value, _ = json.JSONDecoder().raw_decode(text[start:])
            return value if isinstance(value, dict) else None
        except json.JSONDecodeError:
            position = text.find(marker, position + len(marker))
    return None


def _youtube_tracks(player: dict[str, Any]) -> list[CaptionTrack]:
    raw_tracks = player.get("captions", {}).get("playerCaptionsTracklistRenderer", {}).get("captionTracks", [])
    tracks: list[CaptionTrack] = []
    for raw in raw_tracks:
        if not isinstance(raw, dict) or not raw.get("baseUrl"):
            continue
        name = raw.get("name") or {}
        label = name.get("simpleText") if isinstance(name, dict) else None
        if label is None and isinstance(name, dict):
            label = "".join(str(run.get("text", "")) for run in name.get("runs", []) if isinstance(run, dict))
        tracks.append(
            CaptionTrack(
                str(raw["baseUrl"]),
                str(raw["languageCode"]) if raw.get("languageCode") else None,
                str(label) if label else None,
                raw.get("kind") == "asr" or "auto-generated" in str(label).casefold(),
            )
        )
    return tracks


def _language_matches(track: CaptionTrack, requested: str) -> bool:
    actual = (track.language or "").replace("_", "-").casefold()
    wanted = requested.replace("_", "-").casefold()
    return actual == wanted or actual.split("-", 1)[0] == wanted.split("-", 1)[0]


def _select_track(tracks: list[CaptionTrack], language: str | None, prefer_human: bool) -> CaptionTrack | None:
    candidates = [track for track in tracks if _language_matches(track, language)] if language else list(tracks)
    if not candidates:
        return None
    candidates.sort(key=lambda track: (track.auto_generated == prefer_human, tracks.index(track)))
    return candidates[0]


def _is_media_url(url: str) -> bool:
    path = urllib.parse.urlsplit(url).path.casefold()
    return any(path.endswith(extension) for extension in MEDIA_EXTENSIONS)


def _timestamp(seconds: float) -> str:
    milliseconds = max(0, round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    whole_seconds, fraction = divmod(remainder, 1_000)
    prefix = f"{hours:02d}:" if hours else ""
    return f"{prefix}{minutes:02d}:{whole_seconds:02d}.{fraction:03d}"


def _clean_caption_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value))).strip()


def _parse_time(value: str | None) -> float:
    if value is None:
        raise ValueError("timestamp missing")
    if value.endswith("ms"):
        return float(value[:-2]) / 1000
    if value.endswith("s"):
        return float(value[:-1])
    if ":" not in value:
        return float(value)
    total = 0.0
    for part in value.replace(",", ".").split(":"):
        total = total * 60 + float(part)
    return total


def _parse_xml(text: str) -> list[dict[str, Any]]:
    try:
        root = ET.fromstring(text)
    except ET.ParseError:
        return []
    segments: list[dict[str, Any]] = []
    for node in root.iter():
        if node.tag.rsplit("}", 1)[-1] not in {"text", "p"}:
            continue
        raw_start = node.attrib.get("start") or node.attrib.get("begin")
        raw_duration = node.attrib.get("dur")
        raw_end = node.attrib.get("end")
        try:
            start = _parse_time(raw_start)
            end = _parse_time(raw_end) if raw_end else start + float(raw_duration or 0)
        except (TypeError, ValueError):
            continue
        value = _clean_caption_text("".join(node.itertext()))
        if value:
            segments.append({"start_seconds": start, "end_seconds": max(start, end), "text": value})
        if len(segments) >= MAX_SEGMENTS:
            break
    return segments


def _parse_vtt(text: str) -> list[dict[str, Any]]:
    pattern = re.compile(
        r"(?m)^(\d{1,2}:)?\d{2}:\d{2}[.,]\d{3}\s+-->\s+((?:\d{1,2}:)?\d{2}:\d{2}[.,]\d{3})[^\r\n]*\r?\n"
        r"(.*?)(?=\r?\n\r?\n|\Z)",
        flags=re.DOTALL,
    )
    segments: list[dict[str, Any]] = []
    for match in pattern.finditer(text):
        timing = match.group(0).splitlines()[0]
        start_raw, end_raw = [part.strip().split()[0] for part in timing.split("-->", 1)]
        value = _clean_caption_text(" ".join(match.group(3).splitlines()))
        if value:
            segments.append(
                {"start_seconds": _parse_time(start_raw), "end_seconds": _parse_time(end_raw), "text": value}
            )
        if len(segments) >= MAX_SEGMENTS:
            break
    return segments


def _parse_json3(text: str) -> list[dict[str, Any]]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return []
    segments = []
    for event in value.get("events", []) if isinstance(value, dict) else []:
        pieces = event.get("segs") or []
        caption = _clean_caption_text(
            "".join(str(piece.get("utf8", "")) for piece in pieces if isinstance(piece, dict))
        )
        if not caption:
            continue
        start = float(event.get("tStartMs", 0)) / 1000
        end = start + float(event.get("dDurationMs", 0)) / 1000
        segments.append({"start_seconds": start, "end_seconds": end, "text": caption})
        if len(segments) >= MAX_SEGMENTS:
            break
    return segments


def _parse_segments(text: str, content_type: str) -> list[dict[str, Any]]:
    stripped = text.lstrip()
    if "json" in content_type or stripped.startswith("{"):
        return _parse_json3(text)
    if "vtt" in content_type or stripped.startswith("WEBVTT") or "-->" in text:
        return _parse_vtt(text)
    return _parse_xml(text)


class TranscriptProvider:
    def __init__(self, http, clock) -> None:
        self.http = http
        self.clock = clock

    async def fetch(self, url: str, language: str | None, prefer_human: bool) -> ProviderResult:
        validate_url(url)
        if _is_media_url(url):
            return ProviderResult("public-transcript", [], ["TRANSCRIPT_UNAVAILABLE"], 0)
        current_url, target, headers, body = await self.http.download(url)
        content_type = headers.get("content-type", "").split(";", 1)[0].casefold()
        if content_type.startswith(("audio/", "video/")):
            return ProviderResult("public-transcript", [], ["TRANSCRIPT_UNAVAILABLE"], 0)
        text = _decode(headers, body)
        canonical = urllib.parse.urldefrag(current_url)[0]
        page = _PageMetadata()
        title = publisher = published_at = None
        tracks: list[CaptionTrack] = []

        direct_caption = content_type in (CAPTION_CONTENT_TYPES - {"text/plain"}) or (
            content_type == "text/plain" and ("-->" in text or text.lstrip().startswith(("<transcript", "<?xml", "{")))
        )
        if direct_caption:
            tracks = [CaptionTrack(current_url, language)]
        else:
            page.feed(text)
            player = _json_object_after(text, "ytInitialPlayerResponse") or {}
            details = player.get("videoDetails") or {}
            microformat = (player.get("microformat") or {}).get("playerMicroformatRenderer") or {}
            title = details.get("title") or page.title
            publisher = details.get("author") or microformat.get("ownerChannelName") or page.publisher
            published_at = microformat.get("publishDate") or microformat.get("uploadDate") or page.date
            tracks = _youtube_tracks(player)
            tracks.extend(page.tracks)
            if page.canonical:
                candidate = urllib.parse.urljoin(current_url, page.canonical)
                try:
                    validate_url(candidate)
                    canonical = urllib.parse.urldefrag(candidate)[0]
                except ValueError:
                    pass

        track = _select_track(tracks, language, prefer_human)
        if track is None:
            warnings = ["TRANSCRIPT_UNAVAILABLE"]
            if language and tracks:
                warnings.append("TRANSCRIPT_LANGUAGE_UNAVAILABLE")
            return ProviderResult("public-transcript", [], warnings, 0)

        caption_url = urllib.parse.urljoin(current_url, track.url)
        if _is_media_url(caption_url):
            return ProviderResult("public-transcript", [], ["TRANSCRIPT_UNAVAILABLE"], 0)
        if caption_url == current_url:
            caption_headers, caption_text = headers, text
        else:
            _, _, caption_headers, caption_body = await self.http.download(
                caption_url, accept="text/vtt,application/ttml+xml,text/xml,application/json,text/plain"
            )
            caption_text = _decode(caption_headers, caption_body)
        caption_type = caption_headers.get("content-type", "").split(";", 1)[0].casefold()
        if caption_type.startswith(("audio/", "video/")):
            return ProviderResult("public-transcript", [], ["TRANSCRIPT_UNAVAILABLE"], 0)
        segments = _parse_segments(caption_text, caption_type)
        if not segments:
            return ProviderResult("public-transcript", [], ["TRANSCRIPT_UNAVAILABLE"], 0)

        content = "\n".join(
            f"[{_timestamp(segment['start_seconds'])} --> {_timestamp(segment['end_seconds'])}] {segment['text']}"
            for segment in segments
        )
        metadata = {
            "publisher": publisher,
            "language": track.language,
            "language_name": track.name,
            "auto_generated": track.auto_generated,
            "segment_count": len(segments),
            "segments": segments[:MAX_METADATA_SEGMENTS],
        }
        item = EvidenceItem(
            title=str(title) if title else None,
            url=canonical,
            published_at=str(published_at) if published_at else None,
            retrieved_at=rfc3339(self.clock.utcnow()),
            source=target.host.removeprefix("www."),
            content=content,
            metadata={key: value for key, value in metadata.items() if value is not None},
        )
        warnings = []
        if len(segments) >= MAX_SEGMENTS:
            warnings.append("TRANSCRIPT_SEGMENT_LIMIT_REACHED")
        if len(segments) > MAX_METADATA_SEGMENTS:
            warnings.append("TRANSCRIPT_SEGMENT_METADATA_TRUNCATED")
        return ProviderResult("public-transcript", [item], warnings, len(segments))
