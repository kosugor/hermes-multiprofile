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
BROWSER_PROFILE = "researcher"
BROWSER_POLICY = {
    "backend": "off",
    "cloud_provider": "local",
    "engine": "chrome",
    "headed": False,
    "inactivity_timeout": 60,
    "command_timeout": 30,
    "record_sessions": False,
    "allow_private_urls": False,
    "auto_local_for_private_urls": False,
    "cdp_url": "",
    "restrict_evaluate": True,
    "allow_unsafe_evaluate": False,
    "use_real_profile": False,
    "dialog_policy": "auto_dismiss",
    "dialog_timeout_s": 30,
}
FORBIDDEN = {
    "execute_code",
    "delegate_task",
    "browser_exec",
    "computer_use",
    "send_message",
    "cronjob",
}
PLUGIN_TOOLS = {
    "hermes-lcm": {
        "lcm_compile_evidence",
        "lcm_compute",
        "lcm_describe",
        "lcm_doctor",
        "lcm_evidence_pack",
        "lcm_expand",
        "lcm_expand_query",
        "lcm_grep",
        "lcm_inspect",
        "lcm_load_session",
        "lcm_query_state",
        "lcm_recall",
        "lcm_recent",
        "lcm_retrieve",
        "lcm_status",
    },
}
QMD_PROFILE = "wiki-maintainer"
QMD_TOOLS = {"query", "get", "multi_get", "status"}
QMD_SERVER_POLICY = {
    "command": "${userHome}/.hermes/qmd-runtime/node_modules/.bin/qmd",
    "args": ["mcp"],
    "env": {
        "PATH": "${userHome}/.hermes/node/bin:/usr/local/bin:/usr/bin:/bin",
        "QMD_CONFIG_DIR": "${userHome}/.hermes/profiles/wiki-maintainer/qmd",
        "QMD_FORCE_CPU": "1",
    },
    "timeout": 120,
    "connect_timeout": 45,
    "supports_parallel_tool_calls": False,
    "idle_timeout_seconds": 300,
    "max_lifetime_seconds": 1800,
    "trust": "untrusted",
    "tools": {
        "include": ["query", "get", "multi_get", "status"],
        "resources": False,
        "prompts": False,
    },
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
        disabled = set((config.get("agent") or {}).get("disabled_toolsets") or ())
        browser_config = config.get("browser") or {}
        enabled_plugins = set((config.get("plugins") or {}).get("enabled") or ())
        mcp_servers = config.get("mcp_servers") or {}
        context_engine = (config.get("context") or {}).get("engine")
        unknown_plugins = enabled_plugins - PLUGIN_TOOLS.keys()
        if unknown_plugins:
            failures.append(f"{profile}: unreviewed plugins={sorted(unknown_plugins)}")
        if context_engine == "lcm" and "hermes-lcm" not in enabled_plugins:
            failures.append(f"{profile}: lcm context engine requires hermes-lcm")
        if "hermes-lcm" in enabled_plugins and context_engine != "lcm":
            failures.append(f"{profile}: hermes-lcm must be the selected context engine")
        if profile == QMD_PROFILE:
            if set(mcp_servers) != {"qmd"}:
                failures.append(f"{profile}: expected only the reviewed qmd MCP server")
            elif mcp_servers["qmd"] != QMD_SERVER_POLICY:
                failures.append(f"{profile}: qmd MCP policy drift")
        elif mcp_servers:
            failures.append(f"{profile}: unexpected MCP servers={sorted(mcp_servers)}")
        if profile == BROWSER_PROFILE:
            if "browser" in disabled:
                failures.append(f"{profile}: browser must not be disabled")
            for key, required in BROWSER_POLICY.items():
                if browser_config.get(key) != required:
                    failures.append(
                        f"{profile}: browser.{key} must be {required!r}; "
                        f"found {browser_config.get(key)!r}"
                    )
        else:
            if "browser" not in disabled:
                failures.append(f"{profile}: browser must be explicitly disabled")
            if browser_config:
                failures.append(f"{profile}: unexpected browser configuration")
        expected = set(expected_names)
        for platform in PLATFORMS:
            declared = platform_config.get(platform)
            if not isinstance(declared, list) or not declared:
                failures.append(f"{profile}:{platform}: missing positive allowlist")
                continue
            resolved: set[str] = set()
            for toolset_name in declared:
                resolved.update(resolve_toolset(str(toolset_name)))
            for plugin_name in enabled_plugins:
                resolved.update(PLUGIN_TOOLS.get(plugin_name, ()))
            if profile == QMD_PROFILE and mcp_servers.get("qmd") == QMD_SERVER_POLICY:
                resolved.update(f"mcp__qmd__{name}" for name in QMD_TOOLS)
            if profile == BROWSER_PROFILE and browser_config.get("backend") == "off":
                # The static browser toolset contains both mutually exclusive
                # surfaces. backend=off makes browser_exec's registry check fail,
                # leaving only the built-in browser_* tools callable.
                resolved.discard("browser_exec")
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
