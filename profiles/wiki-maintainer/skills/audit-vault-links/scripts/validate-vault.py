#!/usr/bin/env python3
"""Validate Obsidian links and the machine-checkable canonical-page schema."""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path

import yaml

WIKILINK_RE = re.compile(r"(?P<embed>!)?\[\[(?P<body>[^\[\]]+)\]\]")
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$")
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
CANONICAL_DIRS = {"entities", "concepts", "comparisons", "queries"}
EVIDENCE_STATUSES = {"verified", "author-claim", "inference", "unverified", "conflict"}
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
INTERVAL_RE = re.compile(
    r"[1-9]\d*\s*(?:d|day|days|w|week|weeks|m|month|months|y|year|years)\Z", re.I
)
IGNORED_DIRS = {
    ".git", ".obsidian", ".trash", ".hermes-backups", ".hermes-maintenance",
    "evidence-only",
}


@dataclass
class Problem:
    source: str
    line: int
    link: str
    reason: str


class UniqueKeySafeLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate keys instead of silently losing data."""


def _construct_unique_mapping(
    loader: UniqueKeySafeLoader, node: yaml.nodes.MappingNode, deep: bool = False
):
    explicit_keys = set()
    for key_node, _ in node.value:
        if key_node.tag == "tag:yaml.org,2002:merge":
            continue
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in explicit_keys
            explicit_keys.add(key)
        except TypeError as exc:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping", node.start_mark,
                "found unhashable key", key_node.start_mark,
            ) from exc
        if duplicate:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping", node.start_mark,
                f"duplicate key {key!r}", key_node.start_mark,
            )
    loader.flatten_mapping(node)
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            mapping[key] = loader.construct_object(value_node, deep=deep)
        except TypeError as exc:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping", node.start_mark,
                "found unhashable key", key_node.start_mark,
            ) from exc
    return mapping


UniqueKeySafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_unique_mapping)


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


def read_note(path: Path) -> tuple[dict[str, object] | None, str, str | None]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None, "", "Markdown file is not valid UTF-8"
    match = FRONTMATTER_RE.match(text)
    if not match:
        if text.startswith("---"):
            return None, text, "unterminated YAML frontmatter"
        return None, text, None
    try:
        metadata = yaml.load(match.group(1), Loader=UniqueKeySafeLoader)
    except yaml.YAMLError as exc:
        return None, text[match.end():], f"invalid YAML frontmatter: {exc.problem or str(exc)}"
    if not isinstance(metadata, dict) or any(not isinstance(key, str) for key in metadata):
        return None, text[match.end():], "YAML frontmatter must be a mapping with string keys"
    return metadata, text[match.end():], None


def note_title(metadata: dict[str, object] | None) -> str | None:
    value = metadata.get("title") if metadata else None
    return value.strip() if isinstance(value, str) and value.strip() else None


def note_aliases(metadata: dict[str, object] | None) -> set[str]:
    if not metadata:
        return set()
    value = metadata.get("aliases", [])
    if isinstance(value, str):
        return {value.strip()} if value.strip() else set()
    if isinstance(value, list):
        return {item.strip() for item in value if isinstance(item, str) and item.strip()}
    return set()


def _as_iso_date(value: object) -> str | None:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        return value.strip()
    return None


def _valid_date(value: object) -> bool:
    rendered = _as_iso_date(value)
    if rendered == "unknown":
        return True
    if rendered is None or not DATE_RE.fullmatch(rendered):
        return False
    try:
        date.fromisoformat(rendered)
        return True
    except ValueError:
        return False


def validate_canonical(relative: str, metadata: dict[str, object] | None, body: str) -> list[str]:
    """Enforce structured freshness, source provenance, and evidence-ledger basics."""
    parts = Path(relative).parts
    if not any(part.casefold() in CANONICAL_DIRS for part in parts):
        return []
    failures: list[str] = []
    metadata = metadata or {}
    if not isinstance(metadata.get("title"), str) or not metadata["title"].strip():
        failures.append("canonical page is missing a non-empty YAML title")
    for key in ("last_reviewed", "review_after"):
        if key not in metadata:
            failures.append(f"canonical page is missing frontmatter field {key}")
    if "last_reviewed" in metadata and not _valid_date(metadata["last_reviewed"]):
        failures.append("last_reviewed must be an ISO date")
    review_after = metadata.get("review_after")
    if "review_after" in metadata and not (
        _valid_date(review_after)
        or (isinstance(review_after, str) and INTERVAL_RE.fullmatch(review_after.strip()))
    ):
        failures.append("review_after must be an ISO date or a positive interval such as 90 days")

    sources = metadata.get("sources")
    if not isinstance(sources, list) or not sources:
        failures.append("canonical page must have a non-empty sources list in frontmatter")
    else:
        for index, source in enumerate(sources, start=1):
            if not isinstance(source, dict):
                failures.append(f"sources[{index}] must be a mapping with url, published_at, and retrieved_at")
                continue
            url = source.get("url")
            if not isinstance(url, str) or not re.match(r"^https?://\S+$", url):
                failures.append(f"sources[{index}].url must be an absolute HTTP(S) URL")
            if "published_at" not in source or not _valid_date(source.get("published_at")):
                failures.append(f"sources[{index}].published_at must be an ISO date or unknown")
            if (
                "retrieved_at" not in source
                or not _valid_date(source.get("retrieved_at"))
                or _as_iso_date(source.get("retrieved_at")) == "unknown"
            ):
                failures.append(f"sources[{index}].retrieved_at must be an ISO date")

    ledger_body = strip_fenced_code(body)
    ledger = re.search(r"(?ims)^#{1,6}\s+evidence ledger\s*$\n(.*?)(?=^#{1,6}\s+|\Z)", ledger_body)
    if ledger is None:
        failures.append("canonical page is missing an Evidence ledger section")
    else:
        rows = [line for line in ledger.group(1).splitlines() if line.strip().startswith("|")]
        expected_headers = [
            "claim", "source / inspected passage", "published / updated", "retrieved",
            "scope / version", "status", "affected / updated page",
        ]
        headers = [cell.strip().casefold() for cell in rows[0].strip().strip("|").split("|")] if rows else []
        headers = [" ".join(header.split()) for header in headers]
        if headers != expected_headers:
            failures.append("Evidence ledger columns must match the SCHEMA.md order")
        separators = [cell.strip() for cell in rows[1].strip().strip("|").split("|")] if len(rows) > 1 else []
        if len(separators) != len(expected_headers) or any(
            not re.fullmatch(r":?-{3,}:?", cell) for cell in separators
        ):
            failures.append("Evidence ledger must have a valid Markdown table separator row")
        valid_rows = 0
        invalid_rows = 0
        for row in rows[2:]:
            cells = [cell.strip() for cell in row.strip().strip("|").split("|")]
            if len(cells) < 7:
                invalid_rows += 1
                continue
            claim, citation, publication, retrieval, scope, status, affected = cells[:7]
            status = status.strip("`*_ ").casefold()
            linked_source = bool(re.search(r"https?://\S+|\[\[[^]]+\]\]", citation))
            dates_valid = publication == "unknown" or _valid_date(publication)
            retrieved_valid = bool(DATE_RE.fullmatch(retrieval)) and _valid_date(retrieval)
            if claim and linked_source and dates_valid and retrieved_valid and scope and status in EVIDENCE_STATUSES and affected:
                valid_rows += 1
            else:
                invalid_rows += 1
        if not valid_rows:
            failures.append("Evidence ledger needs at least one complete row with source, dates, scope, status, and affected page")
        if invalid_rows:
            failures.append(f"Evidence ledger has {invalid_rows} incomplete row(s) or invalid citation/date/status values")
    return failures


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
    aliases: dict[Path, set[str]] = {}
    problems: list[Problem] = []
    for path in notes:
        relative = path.relative_to(root).as_posix()
        by_note[relative.casefold()] = path
        by_note[relative.removesuffix(".md").casefold()] = path
        metadata, body, frontmatter_error = read_note(path)
        titles[path] = note_title(metadata)
        aliases[path] = note_aliases(metadata)
        if frontmatter_error:
            problems.append(Problem(relative, 1, "", frontmatter_error))
        elif metadata is not None and not titles[path]:
            problems.append(Problem(relative, 1, "", "frontmatter title must be a non-empty string"))
        for error in validate_canonical(relative, metadata, body):
            problems.append(Problem(relative, 1, "", error))

    for source in notes:
        relative_source = source.relative_to(root).as_posix()
        normalized_source = relative_source.casefold()
        if "/raw/" in f"/{normalized_source}" or normalized_source.startswith(
            ("clippings/", "inbox/clippings/")
        ):
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
            elif alias != title and alias not in aliases[target_file]:
                problems.append(Problem(relative_source, line, raw, f"alias must equal target title {title!r} or a declared note alias"))
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
