#!/usr/bin/env python3
"""Discover in-scope documentation pages and write a crawl manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from collections import deque
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urldefrag, urljoin, urlsplit, urlunsplit
from urllib.request import Request, build_opener, urlopen

LANGUAGE_CODES = {
    "ar", "bg", "ca", "cs", "da", "de", "el", "es", "et", "fa", "fi",
    "fr", "he", "hi", "hr", "hu", "id", "it", "ja", "ko", "lt", "lv",
    "ms", "nb", "nl", "pl", "pt", "ro", "ru", "sk", "sl", "sr", "sv",
    "th", "tr", "uk", "vi", "zh",
}


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.title: list[str] = []
        self.text: list[str] = []
        self.html_lang: str | None = None
        self._in_title = False
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attributes = dict(attrs)
        if tag == "html":
            self.html_lang = attributes.get("lang")
        if tag in {"script", "style", "noscript", "template", "svg"}:
            self._skip += 1
        if tag == "title":
            self._in_title = True
        if tag == "a":
            href = attributes.get("href")
            if href:
                self.links.append(href)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title":
            self._in_title = False
        if tag in {"script", "style", "noscript", "template", "svg"} and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if self._skip:
            return
        value = re.sub(r"\s+", " ", data).strip()
        if not value:
            return
        if self._in_title:
            self.title.append(value)
        self.text.append(value)


def canonical(url: str) -> str:
    url, _ = urldefrag(url)
    parts = urlsplit(url)
    scheme = parts.scheme.lower()
    host = (parts.hostname or "").lower()
    port = parts.port
    authority = host
    if port and not ((scheme == "http" and port == 80) or (scheme == "https" and port == 443)):
        authority += f":{port}"
    path = re.sub(r"/{2,}", "/", parts.path or "/")
    if path != "/":
        path = path.rstrip("/")
    return urlunsplit((scheme, authority, path, "", ""))


def in_scope(url: str, root: str) -> bool:
    u, r = urlsplit(url), urlsplit(root)
    if u.scheme not in {"http", "https"} or (u.scheme, u.netloc.lower()) != (r.scheme, r.netloc.lower()):
        return False
    root_path = (r.path or "/").rstrip("/") or "/"
    target_path = u.path or "/"
    return target_path == root_path or target_path.startswith(root_path + "/")


def excluded(url: str, prefixes: list[str]) -> bool:
    return any(url == prefix or url.startswith(prefix + "/") for prefix in prefixes)


def url_language(url: str) -> str | None:
    """Return a language code only when it is an obvious path segment."""
    for segment in urlsplit(url).path.lower().split("/"):
        if segment in LANGUAGE_CODES or re.fullmatch(r"(?:[a-z]{2})-[a-z]{2}", segment):
            return segment.split("-", 1)[0]
    return None


def is_english_page(url: str, html_lang: str | None) -> bool:
    """Keep English pages and pages whose language cannot be determined."""
    language = (html_lang or "").lower().split("-", 1)[0].split("_", 1)[0]
    if language and language != "en":
        return False
    path_language = url_language(url)
    return path_language in (None, "en")


def safe_name(url: str, used: set[str]) -> str:
    path = urlsplit(url).path or "/"
    name = "index" if path == "/" or path.endswith("/") else Path(path).name
    name = re.sub(r"\.[A-Za-z0-9]{1,8}$", "", name) or "page"
    stem = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-._") or "page"
    parent = re.sub(r"[^A-Za-z0-9._-]+", "-", (path.rsplit("/", 1)[0] or "root")).strip("-._")
    candidate = f"{parent}--{stem}.md"
    if candidate in used:
        candidate = f"{parent}--{stem}-{hashlib.sha256(url.encode()).hexdigest()[:10]}.md"
    used.add(candidate)
    return candidate


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", required=True)
    ap.add_argument("--wiki-root", required=True)
    ap.add_argument("--delay", type=float, default=0.2)
    ap.add_argument("--max-pages", type=int, default=10000)
    ap.add_argument("--timeout", type=float, default=30)
    ap.add_argument("--user-agent", default="Hermes-docsite-clipper/0.1")
    ap.add_argument("--exclude-prefix", action="append", default=[], help="canonical URL path prefix to skip; may be repeated")
    args = ap.parse_args()

    root = canonical(args.root)
    exclude_prefixes = [canonical(prefix) for prefix in args.exclude_prefix]
    if urlsplit(root).scheme not in {"http", "https"}:
        print("error: --root must use http or https", file=sys.stderr)
        return 2
    site_root = Path(args.wiki_root).expanduser().resolve() / "raw" / "site"
    host_dir = urlsplit(root).hostname or "unknown-host"
    out = site_root / host_dir
    out.mkdir(parents=True, exist_ok=True)
    opener = build_opener()
    queue: deque[str] = deque([root])
    queued = {root}
    visited: list[str] = []
    pages: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []
    used: set[str] = set()

    while queue and len(visited) < args.max_pages:
        url = queue.popleft()
        if excluded(url, exclude_prefixes):
            skipped.append({"url": url, "reason": "excluded-prefix"})
            continue
        if url in visited:
            continue
        visited.append(url)
        try:
            request = Request(url, headers={"User-Agent": args.user_agent, "Accept": "text/html,application/xhtml+xml"})
            with opener.open(request, timeout=args.timeout) as response:
                final = canonical(response.geturl())
                ctype = response.headers.get_content_type()
                if not in_scope(final, root):
                    skipped.append({"url": url, "reason": "redirect-out-of-scope", "final_url": final})
                    continue
                if ctype not in {"text/html", "application/xhtml+xml"}:
                    skipped.append({"url": url, "reason": f"content-type:{ctype}"})
                    continue
                raw = response.read()
            html = raw.decode("utf-8", errors="replace")
            parser = PageParser()
            parser.feed(html)
            if not is_english_page(final, parser.html_lang):
                skipped.append({"url": final, "reason": "non-english-page"})
                continue
            text = "\n\n".join(parser.text)
            title = " ".join(parser.title).strip() or urlsplit(final).path.rsplit("/", 1)[-1] or "Documentation"
            filename = safe_name(final, used)
            pages.append({"url": final, "title": title, "file": filename})
            base_url = response.geturl()
            for href in parser.links:
                nxt = canonical(urljoin(base_url, href))
                if nxt not in queued and excluded(nxt, exclude_prefixes):
                    skipped.append({"url": nxt, "reason": "excluded-prefix", "found_on": final})
                elif nxt not in queued and in_scope(nxt, root):
                    queued.add(nxt)
                    queue.append(nxt)
                elif nxt not in queued and urlsplit(nxt).scheme in {"http", "https"}:
                    skipped.append({"url": nxt, "reason": "out-of-scope-link", "found_on": final})
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            errors.append({"url": url, "error": f"{type(exc).__name__}: {exc}"})
        except Exception as exc:  # keep crawl report useful for malformed pages
            errors.append({"url": url, "error": f"{type(exc).__name__}: {exc}"})
        if queue and args.delay > 0:
            time.sleep(args.delay)

    report = {
        "root": root,
        "output_dir": str(out),
        "visited": len(visited),
        "discovered": len(pages),
        "skipped": len(skipped),
        "errors": len(errors),
        "max_pages_reached": bool(queue),
        "pages": pages,
        "skipped_urls": skipped,
        "errors_detail": errors,
    }
    (out / "_crawl-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("root", "output_dir", "visited", "discovered", "skipped", "errors", "max_pages_reached")}, ensure_ascii=False))
    return 0 if not report["errors"] and not report["max_pages_reached"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
