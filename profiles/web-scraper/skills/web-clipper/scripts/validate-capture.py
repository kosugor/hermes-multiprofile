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

KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(?:[ \t]+(.*))?$", re.ASCII)
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


def split_capture(data: bytes) -> tuple[bytes, bytes] | None:
    if not data.startswith(b"---\n"):
        return None
    marker = data.find(b"\n---\n", 4)
    if marker < 0:
        return None
    return data[4:marker], data[marker + 5:]


def parse_frontmatter(raw: bytes) -> tuple[dict[str, str], list[str]]:
    errors: list[str] = []
    try:
        source = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return {}, ["frontmatter is not valid UTF-8"]
    values: dict[str, str] = {}
    for number, line in enumerate(source.splitlines(), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = KEY_RE.fullmatch(line)
        if not match:
            errors.append(f"invalid YAML frontmatter at line {number}")
            continue
        key, value = match.groups()
        if key in values:
            errors.append(f"duplicate YAML frontmatter key: {key}")
            continue
        value = (value or "").strip()
        if value.count('"') % 2 or value.count("'") % 2:
            errors.append(f"unbalanced quote in YAML field: {key}")
        if value.startswith(("[", "{")) and not (
            (value.startswith("[") and value.endswith("]"))
            or (value.startswith("{") and value.endswith("}"))
        ):
            errors.append(f"unbalanced flow value in YAML field: {key}")
        values[key] = value.strip("\"'")
    return values, errors


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
        if not values.get(key):
            errors.append(f"frontmatter field is missing or empty: {key}")
    for key in ("supplied_url", "canonical_url"):
        value = values.get(key, "")
        if value and not re.match(r"^https?://\S+$", value):
            errors.append(f"{key} must be an absolute HTTP(S) URL")
    if values.get("canonical_url") and values.get("source") != values.get("canonical_url"):
        errors.append("source must equal canonical_url for legacy triage compatibility")
    published = values.get("published_at", "")
    if published and published != "unknown":
        try:
            date.fromisoformat(published)
        except ValueError:
            errors.append("published_at must be an ISO date or unknown")
    clipped = values.get("clipped", "")
    if clipped:
        try:
            date.fromisoformat(clipped)
        except ValueError:
            errors.append("clipped must be an ISO date")
    retrieved_at = values.get("retrieved_at", "")
    if retrieved_at:
        try:
            timestamp = datetime.fromisoformat(retrieved_at.replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                raise ValueError
        except ValueError:
            errors.append("retrieved_at must be an ISO-8601 timestamp with timezone")
        if not retrieved_at.endswith("Z"):
            errors.append("retrieved_at must end in Z")
    status = values.get("capture_status", "")
    if status and status not in STATUSES:
        errors.append("capture_status must be complete, partial, shell, or failed")
    capture_hash = values.get("content_sha256", "")
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
        http_status = values.get("source_http_status", "")
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
