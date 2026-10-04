#!/usr/bin/env python3
"""Validate capture frontmatter, exact body bytes, and capture disposition."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

import yaml

HASH_RE = re.compile(r"[0-9a-fA-F]{64}")
STATUSES = {"complete", "partial", "shell", "failed"}
ERROR_SHELL_RE = re.compile(
    rb"(?im)^#\s*(?:error|access denied|403 forbidden|404 not found|page not found|captcha|verify you are human)\s*$"
    rb"|^\s*(?:access denied|request blocked by security policy|verify you are human|enable javascript and cookies)\b"
)
REQUIRED = (
    "title", "supplied_url", "canonical_url", "source", "published_at", "clipped",
    "retrieved_at", "capture_status", "capture_method", "provider", "model",
    "content_sha256",
)


class UniqueKeySafeLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate keys instead of silently losing data."""


def _construct_unique_mapping(loader: UniqueKeySafeLoader, node: yaml.nodes.MappingNode, deep: bool = False):
    explicit_keys = set()
    for key_node, _ in node.value:
        if key_node.tag == "tag:yaml.org,2002:merge":
            continue
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in explicit_keys
            explicit_keys.add(key)
        except TypeError as exc:
            raise yaml.constructor.ConstructorError("while constructing a mapping", node.start_mark,
                                                     "found unhashable key", key_node.start_mark) from exc
        if duplicate:
            raise yaml.constructor.ConstructorError("while constructing a mapping", node.start_mark,
                                                     f"duplicate key {key!r}", key_node.start_mark)
    loader.flatten_mapping(node)
    mapping = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            mapping[key] = loader.construct_object(value_node, deep=deep)
        except TypeError as exc:
            raise yaml.constructor.ConstructorError("while constructing a mapping", node.start_mark,
                                                     "found unhashable key", key_node.start_mark) from exc
    return mapping


UniqueKeySafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_unique_mapping)


def split_capture(data: bytes) -> tuple[bytes, bytes] | None:
    if not data.startswith(b"---\n"):
        return None
    marker = data.find(b"\n---\n", 4)
    if marker < 0:
        return None
    return data[4:marker], data[marker + 5:]


def parse_frontmatter(raw: bytes) -> tuple[dict[str, object], list[str]]:
    try:
        source = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return {}, ["frontmatter is not valid UTF-8"]
    try:
        values = yaml.load(source, Loader=UniqueKeySafeLoader)
    except yaml.YAMLError as exc:
        detail = exc.problem or str(exc)
        return {}, [f"invalid YAML frontmatter: {detail}"]
    if not isinstance(values, dict) or any(not isinstance(key, str) for key in values):
        return {}, ["YAML frontmatter must be a mapping with string keys"]
    return values, []


def scalar_text(value: object) -> str:
    if isinstance(value, datetime):
        rendered = value.isoformat()
        return rendered[:-6] + "Z" if rendered.endswith("+00:00") else rendered
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        return value.strip()
    return ""


def validate(path: Path, root: Path | None = None) -> tuple[list[str], str]:
    errors: list[str] = []
    resolved = path.resolve()
    if root is not None:
        allowed = root.expanduser().resolve()
        try:
            resolved.relative_to(allowed)
        except ValueError:
            return [f"capture is outside expected root: {allowed}"], "corrupt"
    try:
        data = path.read_bytes()
    except OSError as exc:
        return [f"capture cannot be read: {exc}"], "corrupt"
    parts = split_capture(data)
    if parts is None:
        return ["missing or unterminated YAML frontmatter"], "corrupt"
    frontmatter, body = parts
    values, yaml_errors = parse_frontmatter(frontmatter)
    errors.extend(yaml_errors)
    for key in REQUIRED:
        if not scalar_text(values.get(key, "")):
            errors.append(f"frontmatter field is missing or empty: {key}")
    for key in ("supplied_url", "canonical_url"):
        value = scalar_text(values.get(key, ""))
        if value and not re.match(r"^https?://\S+$", value):
            errors.append(f"{key} must be an absolute HTTP(S) URL")
    if values.get("canonical_url") and scalar_text(values.get("source")) != scalar_text(values.get("canonical_url")):
        errors.append("source must equal canonical_url for legacy triage compatibility")
    published = scalar_text(values.get("published_at", ""))
    if published and published != "unknown":
        try:
            date.fromisoformat(published)
        except ValueError:
            errors.append("published_at must be an ISO date or unknown")
    clipped = scalar_text(values.get("clipped", ""))
    if clipped:
        try:
            date.fromisoformat(clipped)
        except ValueError:
            errors.append("clipped must be an ISO date")
    retrieved_at = scalar_text(values.get("retrieved_at", ""))
    if retrieved_at:
        try:
            timestamp = datetime.fromisoformat(retrieved_at.replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                raise ValueError
        except ValueError:
            errors.append("retrieved_at must be an ISO-8601 timestamp with timezone")
        if not retrieved_at.endswith("Z"):
            errors.append("retrieved_at must end in Z")
    status = scalar_text(values.get("capture_status", ""))
    if status and status not in STATUSES:
        errors.append("capture_status must be complete, partial, shell, or failed")
    capture_hash = scalar_text(values.get("content_sha256", ""))
    if capture_hash and not HASH_RE.fullmatch(capture_hash):
        errors.append("content_sha256 must be a 64-character hexadecimal SHA-256")
    if capture_hash and HASH_RE.fullmatch(capture_hash):
        actual_hash = hashlib.sha256(body).hexdigest()
        if capture_hash.lower() != actual_hash:
            errors.append("content_sha256 does not match the exact Markdown body bytes")
    if status == "complete":
        if not body.strip():
            errors.append("complete capture body is empty")
        if len(re.findall(rb"(?m)^```", body)) % 2:
            errors.append("code fences are unbalanced")
        if len(re.findall(rb"(?m)^#\s+\S", body)) != 1:
            errors.append("complete capture must contain exactly one H1")
        if ERROR_SHELL_RE.search(body[:8192]):
            errors.append("error/challenge page cannot be marked as a complete source")
        http_status = scalar_text(values.get("source_http_status", ""))
        if http_status and (not http_status.isdigit() or not 200 <= int(http_status) < 300):
            errors.append("complete capture requires a successful source HTTP status")
    if errors:
        return errors, "corrupt"
    outcome = {"complete": "complete", "partial": "deferred", "shell": "shell", "failed": "failed"}.get(status, "corrupt")
    return [], outcome


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    parser.add_argument("--root", type=Path, help="required artifact root for workspace checks")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.capture.is_file():
        parser.error(f"capture does not exist: {args.capture}")
    errors, outcome = validate(args.capture, args.root)
    if args.json:
        print(json.dumps({"path": str(args.capture), "ok": not errors, "outcome": outcome, "errors": errors}))
    else:
        print(f"capture={args.capture}")
        print(f"outcome={outcome}")
        print(f"problems={len(errors)}")
        for error in errors:
            print(f"ERROR {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
