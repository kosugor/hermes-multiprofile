#!/usr/bin/env python3
"""Validate canonical wikilinks across an Obsidian vault."""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

WIKILINK_RE = re.compile(r"(?P<embed>!)?\[\[(?P<body>[^\[\]]+)\]\]")
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$")
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
IGNORED_DIRS = {".git", ".obsidian", ".trash"}


@dataclass
class Problem:
    source: str
    line: int
    link: str
    reason: str


def markdown_files(root: Path) -> list[Path]:
    return sorted(
        p for p in root.rglob("*.md")
        if p.is_file() and not any(part in IGNORED_DIRS for part in p.parts)
    )


def note_title(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8", errors="replace")
    match = FRONTMATTER_RE.match(text)
    if not match:
        return None
    for line in match.group(1).splitlines():
        if line.startswith("title:"):
            value = line.split(":", 1)[1].strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            return value
    return None


def heading_names(path: Path) -> set[str]:
    return {
        match.group(1).strip().casefold()
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
        if (match := HEADING_RE.match(line))
    }


def strip_fenced_code(text: str) -> str:
    inside = False
    output: list[str] = []
    for line in text.splitlines(keepends=True):
        if re.match(r"^\s*(```|~~~)", line):
            inside = not inside
            output.append("\n" if line.endswith("\n") else "")
        elif inside:
            output.append("\n" if line.endswith("\n") else "")
        else:
            output.append(line)
    return "".join(output)


def validate(root: Path) -> list[Problem]:
    root = root.expanduser().resolve()
    files = markdown_files(root)
    by_relative: dict[str, Path] = {}
    titles: dict[Path, str | None] = {}
    for path in files:
        relative = path.relative_to(root).as_posix()
        by_relative[relative.casefold()] = path
        by_relative[relative.removesuffix(".md").casefold()] = path
        titles[path] = note_title(path)

    problems: list[Problem] = []
    for source in files:
        # Raw captures and legacy Clippings preserve upstream prose/examples;
        # validate links targeting them from curated notes, but do not treat
        # source-body embeds, author mentions, or code artifacts as navigation.
        relative_source = source.relative_to(root).as_posix()
        if "raw/" in relative_source or relative_source.startswith("Clippings/"):
            continue
        text = strip_fenced_code(source.read_text(encoding="utf-8", errors="replace"))
        for match in WIKILINK_RE.finditer(text):
            if match.group("embed"):
                continue
            raw = match.group("body").strip()
            line = text.count("\n", 0, match.start()) + 1
            target, separator, alias = raw.partition("|")
            target = target.strip()
            alias = alias.strip()
            location = source.relative_to(root).as_posix()

            if not separator or not alias:
                problems.append(Problem(location, line, raw, "link requires [[full/vault/path|Note Title]]"))
                continue
            if target.startswith("/") or ".." in Path(target).parts:
                problems.append(Problem(location, line, raw, "unsafe or non-vault-relative target path"))
                continue
            if "#" in target:
                target_path, fragment = target.split("#", 1)
            else:
                target_path, fragment = target, ""
            target_key = target_path.casefold()
            target_file = by_relative.get(target_key)
            if target_file is None:
                problems.append(Problem(location, line, raw, "target must be an existing full vault-relative Markdown path"))
                continue
            expected_path = target_file.relative_to(root).as_posix()
            if target_path.casefold() not in {expected_path.casefold(), expected_path.removesuffix(".md").casefold()}:
                problems.append(Problem(location, line, raw, "target is not the canonical vault-relative path"))
            title = titles[target_file]
            if title is None:
                problems.append(Problem(location, line, raw, "target note has no YAML title"))
            elif alias != title:
                problems.append(Problem(location, line, raw, f"alias must equal target title {title!r}"))
            if fragment and not fragment.startswith("^") and fragment.casefold() not in heading_names(target_file):
                problems.append(Problem(location, line, raw, f"heading not found: #{fragment}"))
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vault", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    root = args.vault.expanduser().resolve()
    if not root.is_dir():
        parser.error(f"vault directory does not exist: {root}")
    problems = validate(root)
    if args.as_json:
        print(json.dumps([asdict(problem) for problem in problems], ensure_ascii=False, indent=2))
    else:
        print(f"vault={root}")
        print(f"notes={len(markdown_files(root))}")
        print(f"problems={len(problems)}")
        for problem in problems:
            print(f"ERROR {problem.source}:{problem.line}: [[{problem.link}]] — {problem.reason}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
