#!/usr/bin/env bash
set -Eeuo pipefail

name=${WIKI_TRIAGE_NAME:-wiki-clipping-triage}
schedule=${WIKI_TRIAGE_SCHEDULE:-every day at 03:30}
wiki_root=${HERMES_WIKI_ROOT:-/srv/hermes/wiki}
timezone=${WIKI_TRIAGE_TIMEZONE:-Europe/Belgrade}
update_existing=${WIKI_TRIAGE_UPDATE_EXISTING:-0}
profile_config="${HERMES_HOME:-$HOME/.hermes}/profiles/wiki-maintainer/config.yaml"

if [[ ! -f $profile_config ]] \
  || ! grep -Fxq "timezone: $timezone" "$profile_config" \
  || ! grep -Fxq '  docker_mount_cwd_to_workspace: true' "$profile_config" \
  || ! grep -Fxq '  container_persistent: true' "$profile_config" \
  || ! grep -Fxq '  docker_persist_across_processes: false' "$profile_config"; then
  echo "Wiki Maintainer profile needs the $timezone timezone and host-wiki Docker mount settings: $profile_config" >&2
  exit 1
fi

[[ -d $wiki_root && -w $wiki_root ]] || {
  echo "Wiki root must exist and be writable: $wiki_root" >&2
  exit 1
}
[[ -d "$wiki_root/.git" ]] || {
  echo "Wiki root must be a Git repository for automatic triage commits: $wiki_root" >&2
  exit 1
}
for wiki in investments devops software-development ai; do
  [[ -d "$wiki_root/$wiki" ]] || {
    echo "Missing configured wiki directory: $wiki_root/$wiki" >&2
    exit 1
  }
done

existing=0
if hermes -p wiki-maintainer cron list 2>/dev/null | grep -Fqi "$name"; then
  existing=1
fi
if (( existing )) && [[ $update_existing != 1 ]]; then
  echo "A cron job matching '$name' already exists; refusing to create a duplicate." >&2
  echo "Set WIKI_TRIAGE_UPDATE_EXISTING=1 to update the existing paused job." >&2
  exit 1
fi

prompt=$(cat <<EOF
Run the scheduled wiki clipping triage in timezone $timezone.

First verify the scheduled-wiki-maintenance host-wiki mount canaries at
/workspace. If any fail, stop with an explicit error; do not return [SILENT].

Scope: process at most 20 files from Inbox/Clippings that existed when this
run began. Classify each complete clipping into exactly one of these primary
wikis: investments, devops, software-development, or ai. Move it to that
wiki's raw/clippings directory, preserve its captured Markdown body and source
provenance, and update or create relevant curated pages using the existing
taxonomy. A clipping may be cited by curated pages in other wikis, but its raw
file must have one primary owner. Review legacy plain Markdown clippings in
this same triage run: extract only explicit title/source/capture-time details,
add honest legacy review frontmatter to the archive copy, preserve the body
exactly, and carry uncertainty into curated pages. Do not require a separate
migration step. Skip current capture_status: partial files and malformed or
unverifiable files; report each reason without moving the source.

Use QMD for semantic page discovery and ordinary file search for exact paths.
Run all frontmatter, link, duplicate, and clipping audits. Use the exact-path
commit contract from scheduled-wiki-maintenance: refuse pre-staged Git work,
leave unrelated changes alone, stage only successful triage paths (including
an inbox deletion only when that source was tracked), verify the cached path
set, and make one local commit for the run. Never push or publish.
Write the dated maintenance report and checkpoint. Return [SILENT] when there
is nothing to process; otherwise report processed, moved, created, modified,
skipped, conflicts, failures, and remaining inbox files.
EOF
)

if (( existing )); then
  hermes -p wiki-maintainer cron pause "$name"
  hermes -p wiki-maintainer cron edit "$name" \
    --schedule "$schedule" \
    --prompt "$prompt" \
    --skill scheduled-wiki-maintenance \
    --workdir "$wiki_root" \
    --deliver bot-chat:orchestrator \
    --provider openai-codex \
    --model gpt-5.6-terra \
    --reasoning-effort medium
  hermes -p wiki-maintainer cron pause "$name"
  echo "Updated wiki triage job '$name' ($schedule, timezone $timezone)."
else
  hermes -p wiki-maintainer cron create "$schedule" "$prompt" \
    --name "$name" \
    --skill scheduled-wiki-maintenance \
    --workdir "$wiki_root" \
    --deliver bot-chat:orchestrator \
    --provider openai-codex \
    --model gpt-5.6-terra \
    --reasoning-effort medium \
    --paused \
    --paused-reason "Awaiting initial wiki clipping triage review"
  echo "Created paused wiki triage job '$name' ($schedule, timezone $timezone)."
fi
echo "Run it once manually, inspect its commit/report, then resume it with:"
echo "  hermes -p wiki-maintainer cron run $name"
echo "  hermes -p wiki-maintainer cron resume $name"
