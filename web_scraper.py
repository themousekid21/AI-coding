#!/usr/bin/env python3
"""Simple configurable web scraper with no third-party dependencies."""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import asdict, dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.request import Request, urlopen


@dataclass
class ScrapedItem:
    text: str
    value: str


class _ElementCollector(HTMLParser):
    def __init__(self, selector: str) -> None:
        super().__init__()
        self.selector = selector.strip()
        self.items: list[tuple[dict[str, str], str]] = []
        self._stack: list[tuple[bool, dict[str, str], list[str]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {k: (v or "") for k, v in attrs}
        is_match = _matches_selector(tag, attr_map, self.selector)
        self._stack.append((is_match, attr_map, []))

    def handle_data(self, data: str) -> None:
        if self._stack:
            is_match, attrs, text_parts = self._stack[-1]
            if is_match and data.strip():
                text_parts.append(data.strip())
                self._stack[-1] = (is_match, attrs, text_parts)

    def handle_endtag(self, tag: str) -> None:
        if not self._stack:
            return
        is_match, attrs, text_parts = self._stack.pop()
        if is_match:
            self.items.append((attrs, " ".join(text_parts).strip()))


def _matches_selector(tag: str, attrs: dict[str, str], selector: str) -> bool:
    # Supported selectors: tag, .class, #id, tag.class, tag#id
    pattern = r"^(?:(?P<tag>[a-zA-Z][\w-]*)|)(?:(?P<id>#[\w-]+)|)(?:(?P<class>\.[\w-]+)|)$"
    match = re.match(pattern, selector)
    if not match:
        raise ValueError(
            "Unsupported selector. Use one of: tag, .class, #id, tag.class, tag#id"
        )

    sel_tag = (match.group("tag") or "").lower()
    sel_id = (match.group("id") or "").removeprefix("#")
    sel_class = (match.group("class") or "").removeprefix(".")

    if sel_tag and tag.lower() != sel_tag:
        return False
    if sel_id and attrs.get("id", "") != sel_id:
        return False
    if sel_class:
        classes = attrs.get("class", "").split()
        if sel_class not in classes:
            return False
    return True


def fetch_html(url: str, timeout: int = 15) -> str:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; simple-scraper/1.0)"})
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def scrape(
    html: str,
    selector: str,
    attr: str | None = None,
    contains: str | None = None,
    limit: int | None = None,
) -> list[ScrapedItem]:
    parser = _ElementCollector(selector)
    parser.feed(html)

    items: list[ScrapedItem] = []
    for attrs, text in parser.items:
        value = attrs.get(attr, "") if attr else text

        if contains:
            haystack = f"{text}\n{value}".lower()
            if contains.lower() not in haystack:
                continue

        items.append(ScrapedItem(text=text, value=value))
        if limit and len(items) >= limit:
            break

    return items


def to_json(items: Iterable[ScrapedItem]) -> str:
    return json.dumps([asdict(item) for item in items], indent=2, ensure_ascii=False)


def write_csv(items: Iterable[ScrapedItem], output_path: Path) -> None:
    with output_path.open("w", encoding="utf-8", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["text", "value"])
        writer.writeheader()
        for item in items:
            writer.writerow(asdict(item))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape a webpage by simple selector")
    parser.add_argument("--url", help="Target URL to scrape (if omitted, you'll be prompted)")
    parser.add_argument("--selector", required=True, help="Selector: tag, .class, #id, tag.class, or tag#id")
    parser.add_argument("--attr", help="Optional attribute to extract instead of text, e.g. href")
    parser.add_argument("--contains", help="Optional case-insensitive text filter")
    parser.add_argument("--limit", type=int, help="Maximum number of matches to return")
    parser.add_argument("--format", choices=["json", "csv"], default="json", help="Output format")
    parser.add_argument("--out", help="Optional output file path. If omitted, prints to stdout")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    url = args.url or input("Enter the page URL to scrape: ").strip()
    if not url:
        raise SystemExit("URL is required. Pass --url or provide one when prompted.")

    html = fetch_html(url)
    items = scrape(html=html, selector=args.selector, attr=args.attr, contains=args.contains, limit=args.limit)

    if args.format == "json":
        output = to_json(items)
        if args.out:
            Path(args.out).write_text(output, encoding="utf-8")
        else:
            print(output)
    else:
        output_path = Path(args.out or "scraped_results.csv")
        write_csv(items, output_path)
        print(f"Saved {len(items)} rows to {output_path}")


if __name__ == "__main__":
    main()
