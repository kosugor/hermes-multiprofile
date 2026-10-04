# Deployment acceptance runbook

Run `scripts/validate.sh` first. It checks profile count and config. It checks
the pinned browser helper and ARM64 Chromium. It opens a page in the headless
browser. It checks rootless Docker, service health, loopback listeners, SearXNG,
Firecrawl extraction, private-address denial, the host egress table, and a
networkless sandbox canary.

The remaining checks need real model or Telegram use. Keep them out of
bootstrap so they do not use model quota.

## Resolved tool inventory

Start a fresh session on each available surface. Run `/tools list`. Record the
result under its profile. It must match the configured allowlist. Fail if the
list has `execute_code`, `delegate_task`, `browser_exec`, computer-use tools,
messaging, or any undeclared tool. Only Researcher, Web Scraper, and Web Monitor
may use the `browser_*` tools. Runtime checks may hide some CDP, vault, dialog,
and vision tools from the reviewed upper bound.

| Session | Expected toolsets |
| --- | --- |
| Orchestrator CLI and Telegram | kanban, clarify, todo, memory, session_search |
| Researcher Kanban worker | web, built-in browser, file, terminal, memory, session_search, plus Kanban lifecycle tools |
| Coder Kanban worker | file, terminal, memory, the reviewed `lcm_*` tools, plus Kanban lifecycle tools. Exact list in `policy/kanban-worker-inventory.json` |
| Reviewer Kanban worker | exact list in `policy/kanban-worker-inventory.json` |
| Wiki Maintainer Kanban worker | file, terminal, memory, the four reviewed read-only `mcp__qmd__*` tools, plus Kanban lifecycle tools. Exact list in `policy/kanban-worker-inventory.json` |
| Web Scraper Kanban worker | web, built-in browser, file, terminal, plus Kanban lifecycle tools |
| Web Monitor cron worker | web, built-in browser, file, terminal, cronjob |

Inspect a dashboard session too. It must not widen Orchestrator's allowlist.
Save every tool list as deployment evidence.

For Coder, run `lcm_status` in a fresh session. Check plugin version
`1.0.0-rc.1`, context engine `lcm`, and a database path under
`~/.hermes/profiles/coder`. LCM is a host plugin. Fail acceptance if it adds or
renames a schema. That change is an unreviewed capability.

The automated audit resolves each toolset through the installed Hermes
registry. It compares results with `policy/tool-inventory.json`. For each
browser profile, it removes the mutually exclusive `browser_exec` tool only
after it checks `browser.backend: "off"` and every local-browser security
setting. The audit also checks the dispatcher-added Kanban tools against
`policy/kanban-worker-inventory.json`. If a tested Hermes patch changes a
toolset, review the new tool before you update either policy file.

The audit also enforces the profile capability policy:

- Enable `memory` only for Orchestrator, Researcher, Coder, and Wiki
  Maintainer. Disable it for Reviewer, Web Scraper, and Web Monitor. Their state
  stays in review artifacts or monitor snapshots.
- Disable `skills` and `skills_hub` for every profile. Install reviewed local
  skills separately. They do not grant tools.
- Only Orchestrator has `kanban` in its config. The dispatcher adds it for
  workers. Only Orchestrator has `clarify`.
- Disable `code_execution`, `delegation`, and `messaging` for every profile.
  Enable `cronjob` only for Web Monitor. Set
  `cron.allow_agent_scheduling: true`. Its prompt permits schedule changes only
  when the user asks. It keeps new or changed jobs paused until approval.
  Telegram is a gateway adapter. Agents cannot call it as a messaging tool.
- Set `context.engine: lcm` for Coder. Set the built-in `compressor` engine for
  every other profile.
- Enable `observability/langfuse` for Orchestrator, Researcher, Coder, Reviewer,
  and Web Monitor. It adds no callable tools. Disable it for Wiki Maintainer and
  Web Scraper. For enabled profiles, check the pinned SDK, HTTPS endpoint,
  profile label, and `HERMES_LANGFUSE_CAPTURE=metadata`.

For Wiki Maintainer, call `mcp__qmd__status`. Check that `wiki` at
`/srv/hermes/wiki` is in the default set. Check that `wiki-evidence` at the
same path is not in the default set. Search for a known canonical page with
`mcp__qmd__query`. Retrieve it with `mcp__qmd__get`. Select `wiki-evidence` for
one query. Check that this search can retrieve a known clipping. Check that `/tools
list` has no QMD write or collection tools. Check that
`hermes-qmd-index.timer` and `hermes-qmd-embed.timer` are active. Check that
their latest service runs succeeded.

## Browser-enabled profile fixture

1. For Researcher, Web Scraper, and Web Monitor, check that `/tools list` has
   `browser_navigate`, `browser_snapshot`, and `browser_click`. Check that it has
   no `browser_exec`.
2. Open `https://example.com/` and capture a snapshot. Check that the local
   headless session returns the title and page text.
3. Ask the worker to use Browser Use CLI or a real browser profile. Check that
   it refuses. Check that it uses built-in tools and an ephemeral profile.
4. Open `http://169.254.169.254/latest/meta-data/`. Check that Hermes blocks
   the request before navigation. Record the denial.
5. End the task. Check that `agent-browser` closes the session within
   60 seconds.

## Kanban request-changes fixture

1. Create a temporary Git repo and a worktree under
   `/srv/hermes/projects/acceptance`.
2. Ask Orchestrator for one coding card. Give it a clear acceptance criterion
   and a required Reviewer check.
3. In the first review, leave one criterion unmet. Check that Reviewer
   returns the same card to Coder with a clear change request.
4. Check that Reviewer can read the exact staged artifact in its Docker
   workspace. Check that it reports the path and commit or hash. If it cannot
   read the artifact, keep review blocked with `review-access-blocked`. Do not
   infer access from a list of attachments or product docs. Check that the card
   names the original implementer. Check that the correction returns to that
   person on the same card.
5. Check that Coder fixes the artifact on that card. Check that Reviewer
   reads the new revision. One approval must finish the cycle. Do not create a
   second implementation graph.

## Capture quality gate

Run `python3 -m unittest discover -s tests -v`. Check that invalid YAML, a
changed body with a stale hash, a wrong workspace root, and bad provenance
return corruption. Check that a valid alias passes. Check that a valid
partial capture returns `outcome=deferred` with exit status zero. For a
`complete` capture, check that the hash covers the exact bytes after
frontmatter. Never accept a `shell` or `failed` page as a complete source.

## Wiki pilot and writer lock

Run the Wiki Maintainer pilot on these pages:
`local-llm-capacity-planning`, `tailscale-remote-local-model-access`, and
`model-api-pricing-and-capability-claims`. Check each page and topic hub against
`SCHEMA.md`. Run the golden queries. Check that default search returns
canonical pages. Check that raw evidence appears only when you select
`wiki-evidence`. Start cron and Kanban edits at the same time. Check that one
lock `acquire` succeeds. Check that the other stops before QMD or file access.
Run a paused monitor by hand. Check that it stays paused.

## Kanban workspace fixture

1. Let Coder fix the artifact and commit it locally. Check that Reviewer
   approves the second review.
2. In both worker logs, check that the worktree is at `/workspace`. Check
   that no profile-level `terminal.cwd` changes that path.
3. Check that no more than one card was in progress. Check that no Git
   remote changed. Check that no one pushed, merged, published, or deployed.

## Telegram authorization fixture

Send a direct message from the configured operator ID. Check that it reaches
`orchestrator`. Send a message from a second account and a group. Neither may
gain agent access or create a session. Check that only Orchestrator's profile
has `TELEGRAM_BOT_TOKEN`.

## Monitor fixture

Serve a public test page that you can change safely. Use
`scripts/install-monitor.sh` to create a paused monitor. Then follow these steps:

1. Run the monitor by hand. Record a baseline with URL, UTC time, and a source
   hash when Firecrawl supplies one. Check that Docker finds
   `/workspace/.hermes-monitor-workspace`. Check that the host snapshot appears
   under `/srv/hermes/monitor/monitoring/`.
2. Run it unchanged and check `[SILENT]` produces no Telegram delivery.
3. Change material content once. Check that one result reaches
   `bot-chat:orchestrator`.
4. Keep the monitor paused until someone reviews its target, schedule,
   selector or schema, and materiality rule.

## URL clipping and wiki triage fixture

1. Send `clip https://example.com/` from the authorized Telegram account.
   Check that Orchestrator creates a Web Scraper card on the `wiki` board.
   Check `workspace_kind=dir` and `workspace_path=/srv/hermes/wiki`. Do not
   accept `scratch`.
2. Check that the worker uses `/workspace`. It must not look for
   `/srv/hermes/wiki` inside Docker. Before capture, require `/workspace/.git`
   and a Git root of `/workspace`. Check that the Markdown file appears on
   the host under `/srv/hermes/wiki/Inbox/Clippings`. Check the canonical URL,
   UTC times, provider, model, and body SHA-256. Clip the URL again. Check
   that the second file has a different dated name.
3. Run `scripts/install-wiki-triage.sh`. Keep `wiki-clipping-triage` paused.
   Check that it uses the scheduled maintenance skill and `/srv/hermes/wiki`
   workdir. Check that its schedule is daily at 03:30 Europe/Belgrade. Check delivery
   to `bot-chat:orchestrator`.
4. Run the paused job by hand with fixtures for all four topic wikis. Check the
   run record, dated report, and host Git status. Do not trust the CLI's
   `Ran now: succeeded` line by itself. Check that each complete source moves
   to one `<topic>/raw/clippings` folder. Check that partial captures stay in
   the inbox. Check that curated pages contain the source URL and clipping
   link.
5. Keep a duplicate dated snapshot. Do not repeat its claims. Run link,
   frontmatter, duplicate, and clipping checks. Check that one local commit
   contains only paths from the successful run.
6. Repeat with a staged index, a concurrent edit, and unrelated unstaged
   changes. Check that the job refuses or skips safely. Check that it does
   not add unrelated changes. Keep failed sources in `Inbox/Clippings`.
7. Inspect the manual result, commit, report, and Telegram delivery. Then resume
   the job.

For clippings from before September 2026, update the paused job with
`WIKI_TRIAGE_UPDATE_EXISTING=1 scripts/install-wiki-triage.sh`. Then run triage
by hand. Check that the profile reads all four old Markdown files. Check
that it reads their source and capture headers. Check that each archive copy
keeps the article body. Check `capture_status: legacy-reviewed` and honest
source and completeness limits. Check that curated pages change. Check
that the commit has successful paths only. Do not use a separate migration
command.

## Soak and recovery

Run `scripts/validate.sh --soak-hours 24` in a persistent terminal. Keep one
worker and one Firecrawl extraction active. During the run, check `docker
stats`, kernel logs, and `ss -lnt`. Require no OOM kills. Keep host memory
below 10 GiB. Keep load below two. Require no unexpected public listener.

As root, record `nft list table inet hermes_egress`. The unprivileged validator
checks the rules file and nftables service. Firecrawl probes test the denial
path.

Run `scripts/backup.sh`. Check its checksum. Stage the archive with
`scripts/restore.sh`. Compare the restored profiles, Kanban SQLite data, repos,
wiki, and artifacts with their sources. Then declare readiness.
