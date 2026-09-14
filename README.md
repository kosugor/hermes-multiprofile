# Hermes multi-profile VPS deployment

This repository installs the seven-profile Hermes layout described below on a
small ARM64 Linux VPS. Hermes itself runs directly as an unprivileged user.
SearXNG, Firecrawl, and every model-controlled terminal session run in rootless
Docker.

## Architecture

| Canonical profile | Display role | Model | Fallback policy |
| --- | --- | --- | --- |
| `default` | Orchestrator | `openai-codex/gpt-5.6-sol` | fail closed |
| `researcher` | Researcher | `openai-codex/gpt-5.6-terra` | OpenRouter free, then Nous free |
| `coder` | Coder | `openai-codex/gpt-5.6-sol` | fail closed |
| `reviewer` | Reviewer | `openai-codex/gpt-5.6-sol` | fail closed |
| `wiki-maintainer` | Wiki Maintainer | `openai-codex/gpt-5.6-terra` | OpenRouter free, then Nous free |
| `web-scraper` | Web Scraper | `openai-codex/gpt-5.6-luna` | OpenRouter free, then Nous free |
| `web-monitor` | Web Monitor | `openai-codex/gpt-5.6-luna` | OpenRouter free, then Nous free |

The default profile owns one multiplexed gateway, the Kanban dispatcher, and
the only Telegram credential. Named profiles are workers. Kanban concurrency
starts at one because the target machine has two CPU cores.

Native Hermes `execute_code` is disabled. File and shell operations use an
ephemeral, networkless Docker backend. The `web` tool remains available to the
appropriate profiles and calls loopback-only SearXNG and Firecrawl services.
The sandbox uses a digest-pinned Python 3.11/Node.js 22 Bookworm base and a
date-pinned Debian snapshot for its reviewed build/test packages.

## Prerequisites

- ARM64 Ubuntu 22.04/24.04 or Debian 12 with cgroup v2.
- At least 10 GiB RAM and 20 GiB free disk.
- A dedicated `hermes` user with a working rootless Docker daemon and systemd
  lingering. `scripts/install-host.sh` performs the host preparation.
- Outbound HTTPS during bootstrap. The checksum-verified official installer is
  pinned to Hermes `v2026.9.11` / package `0.21.2` and commit
  `939e45c91d751fadd94dcd1b873ac3cb44846213`.
- A Telegram bot token and the numeric Telegram ID of its sole operator.
- ChatGPT OAuth access for `openai-codex`; an OpenRouter key is optional but
  required for the configured free fallback.

## Install

Run the host preparation as root on a fresh VPS:

```bash
sudo bash ./scripts/install-host.sh --user hermes
```

Log in as `hermes`, place this checkout at `~/hermes-deployment`, and run:

```bash
bash ./scripts/bootstrap-user.sh
```

The bootstrap is idempotent. It installs the exact Hermes release into the
supported `~/.hermes/hermes-agent` layout, creates `/srv/hermes/projects`,
`/srv/hermes/wiki`, and `/srv/hermes/artifacts`; creates the six named Hermes
profiles; backs up an existing profile config before replacing it; builds the
sandbox image; pulls every service image at its committed ARM64 digest; and
installs user systemd units. Bundled skills are opted out for every profile so
the positive tool policies remain the only capability surface. Bootstrap does
not invent or overwrite secrets.
The committed `infra/images.lock.env` contains no credentials. Bootstrap
refuses any non-digest reference or image that does not resolve to ARM64.

It also creates a `wiki` Kanban board and one board for every immediate Git
repository under `/srv/hermes/projects`, each with an explicit board workdir.
Run `scripts/sync-boards.sh` after adding a repository. Hermes' unavoidable
`default` board remains an unbound control/inbox queue; task cards must still
state `worktree:<path>` or `dir:<path>` explicitly so dispatcher context is
authoritative.

Complete the generated secret files:

```bash
editor ~/.hermes/.env
editor ~/.hermes/profiles/researcher/.env
editor ~/.hermes/profiles/wiki-maintainer/.env
editor ~/.hermes/profiles/web-scraper/.env
editor ~/.hermes/profiles/web-monitor/.env
```

Only `~/.hermes/.env` receives `TELEGRAM_BOT_TOKEN`, the single numeric
`TELEGRAM_ALLOWED_USERS` operator ID, and `TELEGRAM_ALLOWED_CHATS`. Set both ID
fields to the same number; the second field makes access DM-only even for the
operator. The gateway service refuses to start with an empty or broad
allowlist. Put `OPENROUTER_API_KEY` only in the four fallback-enabled profiles.
Do not add an OpenAI API key.

Authenticate interactively with the headless device flow, then start services:

```bash
hermes auth add openai-codex
sudo bash ./scripts/install-egress-guard.sh --user hermes
sudo bash ./scripts/install-egress-guard.sh --user hermes --apply
systemctl --user enable --now hermes-web.service
systemctl --user enable --now hermes-gateway.service
systemctl --user enable --now hermes-dashboard.service
./scripts/validate.sh
```

This is subscription-backed ChatGPT OAuth shared from the root Hermes auth
store by all profiles. Its Codex allowance is quota-limited and is not an
OpenAI API credit balance. Check it with `hermes auth status`; this bundle never
sets `OPENAI_API_KEY`.

The dashboard listens only on `127.0.0.1:9119`. From a workstation:

```bash
ssh -L 9119:127.0.0.1:9119 hermes@your-vps
```

Then open `http://127.0.0.1:9119` locally.
The same SSH-forwarding pattern works over a Tailscale address; do not change
the dashboard bind away from loopback.

## Host egress guard

Firecrawl must reach public sites but must never reach OCI metadata or private
networks. Preview and then install the UID-scoped nftables policy:

```bash
sudo ./scripts/install-egress-guard.sh --user hermes
sudo ./scripts/install-egress-guard.sh --user hermes --apply
```

The apply step writes `/etc/nftables.d/hermes-egress.nft`, loads it, and ensures
the main nftables configuration includes that directory. It should be run from
the VPS console or with a second SSH session available. The policy leaves
loopback, established connections, and public Internet destinations available,
but rejects new link-local, RFC1918, CGNAT, benchmark, and IPv6-local flows for
the `hermes` UID. The established-flow exception preserves an existing SSH or
Tailscale tunnel while redirect targets still require a new, filtered flow.

## Web monitor template

Create a monitor in the paused state, avoiding a create-then-pause race:

```bash
MONITOR_NAME=vendor-release-notes \
MONITOR_URL=https://example.com/releases \
MONITOR_SCHEDULE='every 1h' \
MONITOR_SELECTOR='main release-notes content' \
MONITOR_MATERIALITY='new release, security advisory, or breaking change' \
./scripts/install-monitor.sh
```

Use `MONITOR_SCHEMA` instead of, or alongside, `MONITOR_SELECTOR` when the
monitor should retain a reviewed structured extraction.

Inspect it, run it manually, and resume only after the baseline and Telegram
delivery are correct:

```bash
hermes -p web-monitor cron list
hermes -p web-monitor cron run vendor-release-notes
hermes -p web-monitor cron resume vendor-release-notes
```

The monitor records snapshots below `/srv/hermes/wiki/monitoring/`, suppresses
unchanged results with `[SILENT]`, and sends changes to `bot-chat:default` for
orchestrator triage.

## Operations

```bash
./scripts/compose.sh ps
./scripts/validate.sh
./scripts/backup.sh
hermes cron doctor
hermes kanban inspect
journalctl --user -u hermes-gateway -f
```

`scripts/backup.sh` briefly stops the dashboard and gateway for a consistent
archive. Restore archives are extracted only into a new empty staging directory by
`scripts/restore.sh`; an in-place swap remains a deliberate operator action.

When a worker reports a missing dependency, update the reviewed inputs under
`images/hermes-sandbox/dependencies/` and run
`scripts/rebuild-sandbox.sh --apply` as the operator. Python entries must be
version- and hash-pinned; Node dependencies must come from `package-lock.json`.
Never install a dependency from a model-controlled terminal.

Image upgrades are explicit: edit `infra/images.sources.env`, run
`scripts/upgrade.sh --plan`, inspect its output, then run
`scripts/upgrade.sh --apply`. The script takes a consistent state backup before
it refreshes locked image digests; review and commit the resulting lock. Hermes
itself is intentionally excluded from
that path. Review a tested exact release tag, preview
`scripts/upgrade-hermes.sh --tag <tag>`, then run it with `--apply`. The script
refuses a dirty checkout, takes a backup, installs from the detached tag,
validates, and returns to the old commit if installation or validation fails.
Set `APPROVED_HERMES_TAG=<tag>` for later bootstrap and validation runs.
Never run Compose with floating tags directly.
