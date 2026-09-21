#!/usr/bin/env python3
"""Deterministic, read-only audits for raw wiki clippings."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

CURATED_DIRS = ("entities", "concepts", "comparisons", "queries", "hubs")
OFFICIAL_HOSTS = {
    "openai.com", "developers.openai.com", "help.openai.com",
    "hermes-agent.nousresearch.com", "openrouter.ai", "anthropic.com",
    "docs.anthropic.com", "qwen.ai", "qwencloud.com", "huggingface.co",
}
SOCIAL_HOSTS = {"x.com", "twitter.com", "reddit.com"}


def frontmatter_value(text: str, key: str) -> str:
    if not text.startswith("---\n"):
        return ""
    end = text.find("\n---", 4)
    if end < 0:
        return ""
    match = re.search(rf"(?m)^{re.escape(key)}:\s*[\"']?([^\"'\n]+)", text[4:end])
    return match.group(1).strip() if match else ""


def host_of(url: str) -> str:
    return (urlparse(url).hostname or "").lower().removeprefix("www.")


def is_official(url: str) -> bool:
    host = host_of(url)
    return any(host == item or host.endswith("." + item) for item in OFFICIAL_HOSTS)


def is_social(url: str) -> bool:
    return host_of(url) in SOCIAL_HOSTS


def clipping_files(root: Path) -> list[Path]:
    raw = root / "raw" / "clippings"
    return sorted(p for p in raw.glob("*.md") if p.is_file())


def duplicate_report(root: Path) -> dict[str, object]:
    rows = []
    by_url: dict[str, list[str]] = defaultdict(list)
    by_hash: dict[str, list[str]] = defaultdict(list)
    for path in clipping_files(root):
        relative = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        source = frontmatter_value(text, "source")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        rows.append({"path": relative, "source": source, "sha256": digest})
        if source:
            by_url[source].append(relative)
        by_hash[digest].append(relative)
    return {
        "files": len(rows),
        "duplicate_source_urls": {k: v for k, v in by_url.items() if len(v) > 1},
        "duplicate_sha256": {k: v for k, v in by_hash.items() if len(v) > 1},
    }


def clipping_report(root: Path) -> dict[str, object]:
    curated_text = "\n".join(
        p.read_text(encoding="utf-8", errors="replace")
        for directory in CURATED_DIRS
        for p in (root / directory).glob("*.md")
        if p.is_file()
    )
    rows = []
    counts: Counter[str] = Counter()
    for path in clipping_files(root):
        text = path.read_text(encoding="utf-8", errors="replace")
        source = frontmatter_value(text, "source")
        chars = len(text.strip())
        referenced = bool(source and source in curated_text)
        official = is_official(source)
        social = is_social(source)
        if official or referenced:
            category = "keep"
        elif social and chars < 700:
            category = "archive-candidate"
        elif social:
            category = "signal"
        elif chars >= 900:
            category = "reference"
        else:
            category = "signal"
        counts[category] += 1
        rows.append({
            "path": path.relative_to(root).as_posix(),
            "source": source,
            "chars": chars,
            "category": category,
        })
    return {"files": len(rows), "counts": dict(counts), "rows": rows}


def emit(report: dict[str, object], output: Path | None, as_json: bool) -> None:
    if as_json:
        rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    else:
        lines = [f"files={report['files']}"]
        if "counts" in report:
            lines.extend(f"{key}={value}" for key, value in sorted(report["counts"].items()))
        for key in ("duplicate_source_urls", "duplicate_sha256"):
            if key in report:
                groups = report[key]
                lines.append(f"{key}={len(groups)}")
                for group, paths in groups.items():
                    lines.append(f"  {group}: {', '.join(paths)}")
        rendered = "\n".join(lines) + "\n"
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vault", type=Path)
    parser.add_argument("mode", choices=("duplicates", "clippings"))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--write-report", type=Path)
    args = parser.parse_args(argv)
    root = args.vault.expanduser().resolve()
    if not root.is_dir():
        parser.error(f"vault directory does not exist: {root}")
    report = duplicate_report(root) if args.mode == "duplicates" else clipping_report(root)
    emit(report, args.write_report, args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
