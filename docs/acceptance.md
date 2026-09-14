# Deployment acceptance runbook

Run `scripts/validate.sh` first. It checks the installed profile count and
configuration, rootless Docker, service health, loopback listeners, SearXNG,
Firecrawl static and JavaScript extraction, private-address denial, the host
egress table, and a networkless sandbox canary.

The remaining checks require real model or Telegram interactions and therefore
stay explicit rather than consuming quota during bootstrap.

## Resolved tool inventory

Start a fresh session on each reachable surface and run `/tools list`. Record
the result below the matching profile. It must be the exact expansion of the
configured positive allowlist; fail if `execute_code`, `delegate_task`, browser
or computer-use tools, messaging, or any undeclared tool appears.

| Session | Expected toolsets |
| --- | --- |
| Orchestrator CLI and Telegram | kanban, clarify, todo, memory, session_search |
| Researcher Kanban worker | exact list in `policy/kanban-worker-inventory.json` |
| Coder Kanban worker | exact list in `policy/kanban-worker-inventory.json` |
| Reviewer Kanban worker | exact list in `policy/kanban-worker-inventory.json` |
| Wiki Maintainer Kanban worker | exact list in `policy/kanban-worker-inventory.json` |
| Web Scraper Kanban worker | exact list in `policy/kanban-worker-inventory.json` |
| Web Monitor cron worker | web, file |

Also inspect a dashboard session. The dashboard must not widen the default
profile's allowlist. Save all inventories as deployment evidence.

The automated audit resolves every configured toolset through the installed
Hermes registry and compares it with `policy/tool-inventory.json`. It separately
checks the exact union created when the dispatcher injects Kanban lifecycle
tools against `policy/kanban-worker-inventory.json`. When a tested Hermes patch
intentionally changes a toolset, review the new tool before updating either
policy file.

## Kanban request-changes fixture

1. Create a disposable Git repository and a dedicated worktree below
   `/srv/hermes/projects/acceptance`.
2. Ask Orchestrator to create one coding card with an observable acceptance
   criterion and a required Reviewer gate.
3. In the first review, intentionally leave one criterion unmet. Confirm the
   Reviewer returns the same card to Coder with a concrete change request.
4. Let Coder correct it and commit locally. Confirm the second review approves.
5. In both worker transcripts, confirm the worktree appears at `/workspace` and
   that no profile-level `terminal.cwd` overrides it.
6. Confirm there was never more than one in-progress card, no remote changed,
   and nothing was pushed, merged, published, or deployed.

## Telegram authorization fixture

Send a direct message from the configured numeric operator ID and confirm it
reaches `default`. Then message from a second account and from a group. Neither
must receive agent access or create a session. Confirm only the default profile
contains `TELEGRAM_BOT_TOKEN`.

## Monitor fixture

Serve a public test page that can be changed safely. Install a paused monitor
with `scripts/install-monitor.sh`, then:

1. Run it manually once and confirm a baseline with URL, UTC timestamp, and a
   source-provided content hash (when Firecrawl exposes one).
2. Run it unchanged and confirm `[SILENT]` produces no Telegram delivery.
3. Change material content once and confirm exactly one result reaches
   `bot-chat:default`.
4. Keep it paused unless a real target, cadence, selector/schema, and material
   change rule have been reviewed.

## Soak and recovery

Run `scripts/validate.sh --soak-hours 24` in a persistent terminal with one
worker active and one Firecrawl extraction. Review `docker stats`, kernel logs,
and `ss -lnt` during the run. Require no OOM kills, host memory below 10 GiB,
no sustained load above two, and no unexpected public listener.

As root, also record `nft list table inet hermes_egress`; the unprivileged
validator confirms the installed rules file and active nftables service, while
the Firecrawl probes exercise the denial path.

Finally run `scripts/backup.sh`, verify its checksum, stage it with
`scripts/restore.sh`, and compare the restored profiles, Kanban SQLite data,
repositories, and wiki to their sources before declaring readiness.
