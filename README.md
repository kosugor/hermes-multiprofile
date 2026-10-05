# Hermes multi-profile VPS deployment

This repository installs seven Hermes profiles on a small ARM64 Linux VPS.
Hermes runs as an unprivileged user. Rootless Docker runs SearXNG, Firecrawl,
and every model-controlled terminal session.

## Architecture

| Canonical profile | Role label | Model | Fallback policy |
| --- | --- | --- | --- |
| `orchestrator` | Orchestrator | `openai-codex/gpt-5.6-sol` | fail closed |
| `researcher` | Researcher | `openai-codex/gpt-5.6-terra` | OpenRouter free, then Nous free |
| `coder` | Coder + profile-local LCM | `openai-codex/gpt-5.6-sol` | fail closed |
| `reviewer` | Reviewer | `openai-codex/gpt-5.6-sol` | fail closed |
| `wiki-maintainer` | Wiki Maintainer + QMD wiki search | `openai-codex/gpt-5.6-terra` | OpenRouter free, then Nous free |
| `web-scraper` | Web Scraper | `openai-codex/gpt-5.6-luna` | OpenRouter free, then Nous free |
| `web-monitor` | Web Monitor | `openai-codex/gpt-5.6-luna` | OpenRouter free, then Nous free |

Orchestrator owns the shared gateway, Kanban dispatcher, and only Telegram
credential. The other six profiles work as specialists. Kanban starts one
worker at a time because the host has two CPU cores.

Orchestrator keeps task decomposition manual (`auto_decompose: false`). It builds
one linked task graph. Wiki cards must state the page's question. Review returns
to the original implementer on the same card. It must name an exact artifact
revision. Keep a blocked task blocked until evidence shows that a prerequisite
changed. Web Scraper, Kanban wiki tasks, and cron share one lock:
`/srv/hermes/wiki/.hermes-maintenance/wiki-writer.lock`. Bootstrap installs the
token-checking helper.

Hermes `v2026.9.11` predates an upstream fix for Telegram Kanban grants. The
grant uses `platform_toolsets.telegram`. The Kanban registry gate does not yet
accept that setting in this release. Orchestrator also uses the narrow legacy
setting `toolsets: [kanban]`. Gateway preflight requires it. Remove it only
after a reviewed Hermes upgrade includes the upstream fix.

Only Coder uses the profile-local `hermes-lcm` context engine. The deployment
pins it to
`v1.0.0-rc.1` at commit `8d1b1e6d3d63f5fc7b209e8d7ec1dc9b814f2e54`. Raw
messages and the summary DAG stay in Coder's profile. The normal Hermes state
backup includes them.

Memory is role-scoped. Orchestrator, Researcher, Coder, and Wiki Maintainer use
profile memory. Reviewer, Web Scraper, and Web Monitor have no memory. This
keeps reviews independent and monitor state file-based. We set no cloud or
shared memory service. Profiles with Langfuse use the bundled plugin in
metadata-only mode. Each profile has its own environment label. The plugin
adds no model-callable tools. Wiki Maintainer and Web Scraper's clipping skill
do not use Langfuse.

All profiles use ASD-STE100 Issue 9 for internal English. This rule applies to
`SOUL.md`, memory notes, custom skills, Kanban cards, comments, handoffs, and
messages between profiles. Use the operator's language in replies. Write
curated wiki titles and prose in Serbian. Keep raw clippings and quotes in their
source language. Keep required wiki labels and metadata unchanged. See
[`profiles/WRITING-STANDARD.md`](profiles/WRITING-STANDARD.md).

Only Wiki Maintainer gets read-only QMD `2.8.3` tools for `/srv/hermes/wiki`.
Checksums pin QMD, its dependencies, and three GGUF model files. QMD runs on the
host in stdio mode. It exposes query, retrieval, and status tools only. Default
queries search canonical pages. Raw clippings and failed-source evidence need
the optional `wiki-evidence` collection. The skill pack includes `SCHEMA.md`
and a three-page pilot list. A low-priority timer refreshes the lexical index
every 15 minutes. A second timer refreshes embeddings and the semantic index
overnight at half a CPU. The rebuildable index and about 2 GB of local models
stay under `~/.cache/qmd`. State backups omit them.

On Ampere A1, QMD uses the packaged ARM64 node-llama-cpp CPU backend. A local
test found a native KleidiAI build slower for this wiki's semantic queries. The
production setup does not enable it.

Hermes disables `execute_code`. File and shell tools use a temporary Docker
container with no network. Only Researcher, Reviewer, Web Scraper, and Web
Monitor can use the `web` tool. It calls local SearXNG and Firecrawl services.
These three profiles also use Hermes' built-in browser tools and local headless
Chromium. Browser Use CLI is off. The browser does not save profiles or session
recordings. It restricts sensitive page JavaScript. The dedicated `hermes`
user runs the browser. The host UID egress guard protects it. The sandbox uses
a digest-pinned Python 3.11 and Node.js 22 Bookworm image. Reviewed build and
test packages use a date-pinned Debian snapshot.

## Prerequisites

- ARM64 Ubuntu 22.04/24.04 or Debian 12 with cgroup v2.
- At least 10 GiB RAM and 20 GiB free disk.
- A dedicated `hermes` user with rootless Docker and systemd lingering.
  `scripts/install-host.sh` prepares the host.
- Outbound HTTPS for bootstrap. The checksum-verified official installer is
  pinned to Hermes `v2026.9.11` / package `0.21.2` and commit
  `939e45c91d751fadd94dcd1b873ac3cb44846213`.
- A Telegram bot token and the numeric Telegram ID of its sole operator.
- ChatGPT OAuth access for `openai-codex`. An OpenRouter key is optional but
  required for the configured free fallback.

## Install

Prepare the fresh VPS as root:

```bash
sudo bash ./scripts/install-host.sh --user hermes
```

Log in as `hermes`. Put this checkout at `~/hermes-deployment`. Then run:

```bash
bash ./scripts/bootstrap-user.sh
```

Bootstrap is idempotent. It installs the pinned Hermes release under
`~/.hermes/hermes-agent`. It creates `/srv/hermes/projects`, `/srv/hermes/wiki`,
`/srv/hermes/monitor`, its `monitoring` folder, and `/srv/hermes/artifacts`.
It creates seven profiles. Before it replaces a profile config or skill pack,
it saves a backup. It builds the sandbox image, pulls each image at its
committed ARM64 digest, and installs user systemd units. Each profile opts out
of bundled skills. Bootstrap installs each reviewed profile skill pack and the
shared `asd-ste100` skill in all seven profiles. The shared skill source and
its references, examples, and linter are stored in
[`profiles/shared/skills/asd-ste100`](profiles/shared/skills/asd-ste100).
Bootstrap does not create or overwrite secrets. It adds an idempotent block to
`~/.bashrc` so SSH login shells export the existing systemd user bus address for
`systemctl --user`.

Bootstrap installs the reviewed LCM release at
`~/.hermes/profiles/coder/plugins/hermes-lcm`. An existing checkout must be
clean and use the approved commit. It installs the pinned QMD runtime and local
models. It also builds the first wiki index for Wiki Maintainer. Browser setup
installs `agent-browser` 0.26.0 and Playwright 1.62.1. It downloads the ARM64
Chromium build. It does not install Browser Use CLI. The committed
`infra/images.lock.env` has no credentials. Bootstrap rejects images without a
digest or ARM64 support.

Bootstrap also creates a `wiki` Kanban board and a board for each Git repo
under `/srv/hermes/projects`. Each board has a workdir. Run
`scripts/sync-boards.sh` after you add a repo. Hermes keeps an unbound `default`
board for control and inbox tasks. Each task card must state
`worktree:<path>` or `dir:<path>`. This makes the dispatcher use the right path.

Add secrets to these generated files:

```bash
editor ~/.hermes/profiles/orchestrator/.env
editor ~/.hermes/profiles/researcher/.env
editor ~/.hermes/profiles/coder/.env
editor ~/.hermes/profiles/reviewer/.env
editor ~/.hermes/profiles/wiki-maintainer/.env
editor ~/.hermes/profiles/web-scraper/.env
editor ~/.hermes/profiles/web-monitor/.env
```

Put `TELEGRAM_BOT_TOKEN`, the operator's numeric ID in `TELEGRAM_ALLOWED_USERS`,
and the same ID in `TELEGRAM_ALLOWED_CHATS` only in
`~/.hermes/profiles/orchestrator/.env`. The chat field limits access to direct
messages. The gateway will not start with an empty or broad allowlist. Put
`OPENROUTER_API_KEY` only in the four profiles with a fallback.

Each profile that uses Langfuse needs these credentials in its `.env`:
`HERMES_LANGFUSE_PUBLIC_KEY` (`pk-lf-...`),
`HERMES_LANGFUSE_SECRET_KEY` (`sk-lf-...`), and an HTTPS
`HERMES_LANGFUSE_BASE_URL`. Set `HERMES_LANGFUSE_CAPTURE=metadata`. The
validator rejects missing credentials, non-HTTPS URLs, or another capture mode.
Do not add an OpenAI API key.

For an existing deployment, review the required values in `~/.hermes/.env`.
Copy them to `~/.hermes/profiles/orchestrator/.env` before you start the new
gateway. Bootstrap does not read or change the built-in `default` profile or
its files.

Use the headless device flow to sign in. Then start the services:

```bash
hermes auth add openai-codex
sudo bash ./scripts/install-egress-guard.sh --user hermes
sudo bash ./scripts/install-egress-guard.sh --user hermes --apply
systemctl --user enable --now hermes-web.service
systemctl --user enable --now hermes-qmd-index.timer
systemctl --user enable --now hermes-qmd-embed.timer
systemctl --user enable --now hermes-gateway.service
systemctl --user enable --now hermes-dashboard.service
./scripts/validate.sh
```

All profiles use subscription-backed ChatGPT OAuth from the root Hermes auth
store. The Codex allowance has a quota. It is not OpenAI API credit. Run
`hermes auth status` to check it. This bundle does not set `OPENAI_API_KEY`.

The dashboard listens on the VPS's Tailscale IPv4 address at port `9119`.
Configure the address before restarting the dashboard:

```bash
install -d -m 0700 ~/.config/hermes
printf 'HERMES_DASHBOARD_HOST=%s\n' "$(tailscale ip -4 | head -n 1)" \
  > ~/.config/hermes/dashboard.env
chmod 0600 ~/.config/hermes/dashboard.env
systemctl --user daemon-reload
systemctl --user restart hermes-dashboard.service
```

Open `http://<vps-tailscale-ip>:9119` from a device on the tailnet. Keep access
limited through your Tailscale access policy. SearXNG and Firecrawl remain bound
to loopback.

## Host egress guard

Firecrawl must reach public sites. It must not reach OCI metadata or private
networks. Preview the UID-scoped nftables policy. Then install it:

```bash
sudo ./scripts/install-egress-guard.sh --user hermes
sudo ./scripts/install-egress-guard.sh --user hermes --apply
```

The apply step writes `/etc/nftables.d/hermes-egress.nft` and loads it. It also
adds that folder to the main nftables config. Run it from the VPS console or
keep a second SSH session open. The policy allows loopback, established
connections, and public Internet traffic. For the `hermes` UID, it rejects new
link-local, RFC1918, CGNAT, benchmark, and IPv6-local traffic. The established
flow rule keeps SSH or Tailscale tunnels open. A redirect target still needs a
new flow that passes the filter.

## Web monitor template

Create the monitor in the paused state. This avoids a create-then-pause race:

```bash
MONITOR_NAME=vendor-release-notes \
MONITOR_URL=https://example.com/releases \
MONITOR_SCHEDULE='every 1h' \
MONITOR_SELECTOR='main release-notes content' \
MONITOR_MATERIALITY='new release, security advisory, or breaking change' \
./scripts/install-monitor.sh
```

Use `MONITOR_SCHEMA` instead of or with `MONITOR_SELECTOR` when the monitor
needs a reviewed structured extract.

Inspect the monitor. Run it by hand. Resume it only after you check the
baseline and Telegram delivery:

```bash
hermes -p web-monitor cron list
hermes -p web-monitor cron run vendor-release-notes
hermes -p web-monitor cron resume vendor-release-notes
```

The monitor uses `/srv/hermes/monitor` on the host. Docker mounts it at
`/workspace` with no network. The installer checks the mount canary that
bootstrap creates. Snapshots go under `/srv/hermes/monitor/monitoring/`. The
monitor returns `[SILENT]` when nothing changes. It sends changes to
`bot-chat:orchestrator` for review.

Current cron jobs keep their workdir and snapshots. Move their snapshots to
`/srv/hermes/monitor/monitoring/`. Then recreate the jobs. The installer does
not change current jobs. Web Monitor also has the `cronjob` tool. Ask the
profile to check or manage its schedules. It keeps new or changed jobs paused
until you approve the target and schedule.

## URL clipping and wiki triage

Send this command to the Telegram operator bot:

```text
clip https://example.com/article
```

After you install or change the compatibility setting, restart the gateway.
Send `/new` before you retry the command. Current conversations keep their old
tool schema.

Orchestrator sends this one-time capture to Web Scraper. Complete Markdown
files go to `/srv/hermes/wiki/Inbox/Clippings`. Repeated captures keep dates,
source details, and body hashes. Other URLs are not clipping requests.

The task card must set `workspace_kind=dir` and
`workspace_path=/srv/hermes/wiki`. The pinned Hermes release needs both values.
A board's default workdir does not prevent a scratch workspace. The absolute
path names the host mount source. Docker mounts it at `/workspace`. Web Scraper
must save clippings under `/workspace/Inbox/Clippings`. It must not look for
`/srv/hermes/wiki` inside Docker.

If an old Orchestrator prompt made a blocked scratch card, archive it. Redeploy
the profile, restart the gateway, and send `/new`. Then retry. This Hermes
release cannot change workspace kind or path with `kanban edit`.

If a valid `dir:/srv/hermes/wiki` card blocks because the worker looks for the
host path in Docker, deploy the updated Web Scraper profile. Before you unblock
the card, add a comment. State that Docker mounts the host path at `/workspace`.
State that this rule replaces any request to expose `/srv/hermes/wiki` in
Docker. Then unblock the same card. Do not create a replacement.

The pinned release needs `container_persistent: true` for Web Scraper and Wiki
Maintainer. This keeps the task workdir as the Docker mount source. It does not
allow container reuse across processes. The clipping skill checks the wiki's
`.git` folder. It must stop if `/workspace` is empty. If a done card has no
host file, keep it as false-success evidence. Deploy this fix. Then create a
replacement card with a new idempotency key.

Install the daily Wiki Maintainer triage job. It starts paused. Check its first
run before you enable local commits:

```bash
./scripts/install-wiki-triage.sh
hermes -p wiki-maintainer cron run wiki-clipping-triage
hermes -p wiki-maintainer cron resume wiki-clipping-triage
```

Before you resume the job, check
`hermes -p wiki-maintainer cron runs wiki-clipping-triage`. If no run appears,
check the profile's `cron/output/wiki-clipping-triage/` files. Also check
`/srv/hermes/wiki/.hermes-maintenance/reports/`, Git status, and the latest wiki
commit. A successful agent run does not prove that it processed a clipping.
Wiki Maintainer uses `timezone: Europe/Belgrade`. The 03:30 run follows local
time through daylight saving changes.

The job runs every day at 03:30 Europe/Belgrade. It processes up to 20 inbox
clippings. It archives each source under one of these folders:
`investments/raw/clippings`, `devops/raw/clippings`,
`software-development/raw/clippings`, or `ai/raw/clippings`. It updates or
creates curated pages with source links. It commits only paths that pass that
run's checks. It leaves partial captures, conflicts, and unrelated worktree
changes alone. An empty successful run returns `[SILENT]`.

For older clippings without the capture frontmatter, deploy the updated Wiki
Maintainer profile and skill. Update the paused job. Then run triage:

```bash
profile="$HOME/.hermes/profiles/wiki-maintainer"
stamp=$(date -u +%Y%m%dT%H%M%SZ)
cp -p "$profile/config.yaml" "$profile/config.yaml.before-legacy-triage.$stamp"
cp -p "$profile/skills/scheduled-wiki-maintenance/SKILL.md" \
  "$profile/skills/scheduled-wiki-maintenance/SKILL.md.before-legacy-triage.$stamp"
install -m 0644 profiles/wiki-maintainer/config.yaml "$profile/config.yaml"
install -m 0644 profiles/wiki-maintainer/skills/scheduled-wiki-maintenance/SKILL.md \
  "$profile/skills/scheduled-wiki-maintenance/SKILL.md"
hermes -p wiki-maintainer config check
WIKI_TRIAGE_UPDATE_EXISTING=1 ./scripts/install-wiki-triage.sh
hermes -p wiki-maintainer cron run wiki-clipping-triage
```

Triage reads older title, source, and capture headers. It reviews each clipping.
It adds legacy provenance to the archived file and keeps the Markdown body. It
records uncertainty about source access or capture completeness. It adds that
uncertainty to curated pages. The update keeps the job paused. Check the local
commit and report before you resume the schedule.

## Operations

```bash
./scripts/compose.sh ps
./scripts/validate.sh
./scripts/backup.sh
hermes -p orchestrator cron doctor
hermes -p orchestrator kanban inspect
journalctl --user -u hermes-gateway -f
```

The web service starts SearXNG and the extraction stack. During long coding
tasks, stop extraction. Search and the gateway remain available:

```bash
./scripts/compose.sh extraction-stop
./scripts/validate.sh --core-web
```

Restore extraction before research or monitoring. Run
`./scripts/compose.sh extraction-up`. The next restart of `hermes-web.service`
also restores the full stack.

`scripts/backup.sh` stops the dashboard and gateway for a consistent archive.
The backup contains projects, wiki, artifacts, profile state, and runtime
secrets. It omits Hermes, Node, QMD, and browser runtimes because setup can
recreate them. The script checks free space before it stages files.
`scripts/restore.sh` extracts an archive only into a new empty folder. Run
bootstrap first to restore the runtimes. Then restore approved state paths.

When a worker reports a missing dependency, update the reviewed files under
`images/hermes-sandbox/dependencies/`. As the operator, run
`scripts/rebuild-sandbox.sh --apply`. Pin each Python package by version and
hash. Use `package-lock.json` for Node packages. Never install a package from a
model-controlled terminal.

Upgrade images by an explicit process. Edit `infra/images.sources.env`. Run
`scripts/upgrade.sh --plan` and check its output. Then run
`scripts/upgrade.sh --apply`. The script saves a state backup before it updates
image digests. Review and commit the new lock. This process does not upgrade
Hermes.

For Hermes, choose a tested release tag. Preview
`scripts/upgrade-hermes.sh --tag <tag>`. Then run it with `--apply`. The script
refuses a dirty checkout. It saves a backup and installs from the detached tag.
It checks the install. If the install or check fails, it restores the old
commit. Set `APPROVED_HERMES_TAG=<tag>` for later bootstrap and validation runs.
Never run Compose with floating tags.
