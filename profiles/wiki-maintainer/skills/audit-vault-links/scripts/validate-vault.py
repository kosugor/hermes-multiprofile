#!/usr/bin/env python3
"""Validate canonical Obsidian links and embeds without external packages."""
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
IGNORED_DIRS = {".git", ".obsidian", ".trash", ".hermes-backups", ".hermes-maintenance"}


@dataclass
class Problem:
    source: str
    line: int
    link: str
    reason: str


def markdown_files(root: Path) -> list[Path]:
    return sorted(
        p for p in root.rglob("*.md")
        if p.is_file() and not any(part in IGNORED_DIRS for part in p.relative_to(root).parts)
    )


def all_files(root: Path) -> dict[str, Path]:
    return {
        p.relative_to(root).as_posix().casefold(): p
        for p in root.rglob("*")
        if p.is_file() and not any(part in IGNORED_DIRS for part in p.relative_to(root).parts)
    }


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
    notes = markdown_files(root)
    paths = all_files(root)
    by_note: dict[str, Path] = {}
    titles: dict[Path, str | None] = {}
    for path in notes:
        relative = path.relative_to(root).as_posix()
        by_note[relative.casefold()] = path
        by_note[relative.removesuffix(".md").casefold()] = path
        titles[path] = note_title(path)

    problems: list[Problem] = []
    for source in notes:
        relative_source = source.relative_to(root).as_posix()
        if "/raw/" in f"/{relative_source}" or relative_source.startswith("Clippings/"):
            continue
        text = strip_fenced_code(source.read_text(encoding="utf-8", errors="replace"))
        for match in WIKILINK_RE.finditer(text):
            raw = match.group("body").strip()
            line = text.count("\n", 0, match.start()) + 1
            target, separator, alias = raw.partition("|")
            target = target.strip()
            alias = alias.strip()
            target_path, _, fragment = target.partition("#")
            if target_path.startswith("/") or ".." in Path(target_path).parts:
                problems.append(Problem(relative_source, line, raw, "unsafe or non-vault-relative target"))
                continue

            if match.group("embed"):
                candidates = (target_path, f"{target_path}.md") if not Path(target_path).suffix else (target_path,)
                if not any(candidate.casefold() in paths for candidate in candidates):
                    problems.append(Problem(relative_source, line, raw, "embedded target does not exist"))
                continue

            if not separator or not alias:
                problems.append(Problem(relative_source, line, raw, "link requires [[full/vault/path|Note Title]]"))
                continue
            target_file = by_note.get(target_path.casefold())
            if target_file is None:
                problems.append(Problem(relative_source, line, raw, "target must be an existing vault-relative Markdown path"))
                continue
            expected = target_file.relative_to(root).as_posix()
            if target_path.casefold() not in {expected.casefold(), expected.removesuffix(".md").casefold()}:
                problems.append(Problem(relative_source, line, raw, "target is not the canonical vault-relative path"))
            title = titles[target_file]
            if title is None:
                problems.append(Problem(relative_source, line, raw, "target note has no YAML title"))
            elif alias != title:
                problems.append(Problem(relative_source, line, raw, f"alias must equal target title {title!r}"))
            if fragment and not fragment.startswith("^") and fragment.casefold() not in heading_names(target_file):
                problems.append(Problem(relative_source, line, raw, f"heading not found: #{fragment}"))
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("vault", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
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
