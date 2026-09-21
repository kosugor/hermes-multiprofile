#!/usr/bin/env python3
"""Validate the small Markdown contract produced by web-clipper."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---\n"):
        return ["missing YAML frontmatter"]
    end = text.find("\n---\n", 4)
    if end < 0:
        return ["unterminated YAML frontmatter"]
    frontmatter = text[4:end].splitlines()
    values: dict[str, str] = {}
    for line in frontmatter:
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*)$", line)
        if match:
            values[match.group(1)] = match.group(2).strip().strip('"\'')
    for key in (
        "title",
        "source",
        "clipped",
        "retrieved_at",
        "capture_status",
        "capture_method",
        "provider",
        "model",
        "content_sha256",
    ):
        if not values.get(key):
            errors.append(f"frontmatter field is missing or empty: {key}")
    source = values.get("source", "")
    if source and not re.match(r"^https?://\S+$", source):
        errors.append("source must be an absolute HTTP(S) URL")
    clipped = values.get("clipped", "")
    if clipped:
        try:
            date.fromisoformat(clipped)
        except ValueError:
            errors.append("clipped must be an ISO date")
    retrieved_at = values.get("retrieved_at", "")
    if retrieved_at:
        try:
            datetime.fromisoformat(retrieved_at.replace("Z", "+00:00"))
        except ValueError:
            errors.append("retrieved_at must be an ISO-8601 timestamp")
        if not retrieved_at.endswith("Z"):
            errors.append("retrieved_at must end in Z")
    status = values.get("capture_status", "")
    if status and status not in {"complete", "partial"}:
        errors.append("capture_status must be complete or partial")
    capture_hash = values.get("content_sha256", "")
    if capture_hash and not re.fullmatch(r"[0-9a-fA-F]{64}", capture_hash):
        errors.append("content_sha256 must be a 64-character hexadecimal SHA-256")
    body = text[end + 5 :]
    if not body.strip():
        errors.append("body is empty")
    if capture_hash and re.fullmatch(r"[0-9a-fA-F]{64}", capture_hash):
        actual_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
        if capture_hash.lower() != actual_hash:
            errors.append("content_sha256 does not match the Markdown body")
    if len(re.findall(r"(?m)^```", body)) % 2:
        errors.append("code fences are unbalanced")
    h1_count = len(re.findall(r"(?m)^#\s+\S", body))
    if h1_count != 1:
        errors.append("body must contain exactly one H1")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if not args.capture.is_file():
        parser.error(f"capture does not exist: {args.capture}")
    errors = validate(args.capture)
    if args.json:
        print(json.dumps({"path": str(args.capture), "ok": not errors, "errors": errors}))
    else:
        print(f"capture={args.capture}")
        print(f"problems={len(errors)}")
        for error in errors:
            print(f"ERROR {error}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
