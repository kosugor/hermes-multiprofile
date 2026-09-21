#!/usr/bin/env python3
"""Validate the small Markdown contract produced by web-clipper."""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
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
    for key in ("title", "source", "clipped"):
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
    body = text[end + 5 :]
    if not body.strip():
        errors.append("body is empty")
    if len(re.findall(r"(?m)^```", body)) % 2:
        errors.append("code fences are unbalanced")
    if len(re.findall(r"(?m)^#\s+\S", body)) > 1:
        errors.append("body contains more than one H1")
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
