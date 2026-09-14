#!/usr/bin/env python3
"""Fail closed when a declared Hermes toolset expands beyond reviewed tools."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from toolsets import resolve_toolset


PLATFORMS = ("cli", "telegram", "api_server", "cron")
FORBIDDEN = {
    "execute_code",
    "delegate_task",
    "browser_navigate",
    "computer_use",
    "send_message",
    "cronjob",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    bundle = args.bundle.resolve()
    reviewed = json.loads((bundle / "policy/tool-inventory.json").read_text(encoding="utf-8"))
    reviewed_workers = json.loads(
        (bundle / "policy/kanban-worker-inventory.json").read_text(encoding="utf-8")
    )
    failures: list[str] = []

    for profile, expected_names in reviewed.items():
        config = yaml.safe_load((bundle / "profiles" / profile / "config.yaml").read_text(encoding="utf-8"))
        platform_config = config.get("platform_toolsets") or {}
        expected = set(expected_names)
        for platform in PLATFORMS:
            declared = platform_config.get(platform)
            if not isinstance(declared, list) or not declared:
                failures.append(f"{profile}:{platform}: missing positive allowlist")
                continue
            resolved: set[str] = set()
            for toolset_name in declared:
                resolved.update(resolve_toolset(str(toolset_name)))
            if resolved != expected:
                missing = sorted(expected - resolved)
                extra = sorted(resolved - expected)
                failures.append(
                    f"{profile}:{platform}: inventory drift; missing={missing}, undeclared={extra}"
                )
            forbidden = sorted(resolved & FORBIDDEN)
            if forbidden:
                failures.append(f"{profile}:{platform}: forbidden tools={forbidden}")

    injected_kanban = set(resolve_toolset("kanban"))
    for profile, expected_names in reviewed_workers.items():
        actual = set(reviewed.get(profile, ())) | injected_kanban
        expected = set(expected_names)
        if actual != expected:
            failures.append(
                f"{profile}:kanban-worker: inventory drift; "
                f"missing={sorted(expected - actual)}, undeclared={sorted(actual - expected)}"
            )
        forbidden = sorted(actual & FORBIDDEN)
        if forbidden:
            failures.append(f"{profile}:kanban-worker: forbidden tools={forbidden}")

    if failures:
        print("\n".join(f"FAIL  {failure}" for failure in failures), file=sys.stderr)
        return 1
    print("PASS  resolved Hermes toolset expansions match policy/tool-inventory.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
