"""Small deterministic HTML-to-text extractor with no script execution."""

from __future__ import annotations

import re
from html.parser import HTMLParser


class _Extractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.links: list[tuple[str, str]] = []
        self.title: list[str] = []
        self._ignored = 0
        self._in_title = False
        self._href: str | None = None
        self._anchor: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        attrs = dict(attrs)
        if tag in {"script", "style", "noscript", "svg"}:
            self._ignored += 1
        if tag == "title":
            self._in_title = True
        if tag == "a" and not self._ignored:
            self._href = attrs.get("href")
            self._anchor = []
        if tag in {"p", "br", "li", "h1", "h2", "h3", "h4", "tr", "blockquote", "article", "section"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self._ignored:
            self._ignored -= 1
        if tag == "title":
            self._in_title = False
        if tag == "a" and self._href:
            text = " ".join(self._anchor).strip()
            self.links.append((text, self._href))
            self._href = None
            self._anchor = []

    def handle_data(self, data: str) -> None:
        if self._ignored:
            return
        if self._in_title:
            self.title.append(data)
        self.parts.append(data)
        if self._href:
            self._anchor.append(data)


def extract_html(source: str) -> tuple[str | None, str, list[tuple[str, str]]]:
    parser = _Extractor()
    parser.feed(source)
    text = re.sub(r"[ \t]+", " ", "".join(parser.parts))
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
    title = " ".join("".join(parser.title).split()) or None
    return title, text, parser.links
