#!/usr/bin/env bash
set -Eeuo pipefail

name=${WIKI_TRIAGE_NAME:-wiki-clipping-triage}
schedule=${WIKI_TRIAGE_SCHEDULE:-every 1d at 03:30}
wiki_root=${HERMES_WIKI_ROOT:-/srv/hermes/wiki}
timezone=${WIKI_TRIAGE_TIMEZONE:-Europe/Belgrade}

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

if hermes -p wiki-maintainer cron list 2>/dev/null | grep -Fqi "$name"; then
  echo "A cron job matching '$name' already exists; refusing to create a duplicate." >&2
  exit 1
fi

prompt=$(cat <<EOF
Run the scheduled wiki clipping triage in timezone $timezone.

Scope: process at most 20 files from Inbox/Clippings that existed when this
run began. Classify each complete clipping into exactly one of these primary
wikis: investments, devops, software-development, or ai. Move it to that
wiki's raw/clippings directory, preserve its captured Markdown body and source
provenance, and update or create relevant curated pages using the existing
taxonomy. A clipping may be cited by curated pages in other wikis, but its raw
file must have one primary owner. Skip capture_status: partial files.

Use QMD for semantic page discovery and ordinary file search for exact paths.
Run all frontmatter, link, duplicate, and clipping audits. Use the exact-path
commit contract from scheduled-wiki-maintenance: refuse pre-staged Git work,
leave unrelated changes alone, stage only successful triage paths, verify the
cached path set, and make one local commit for the run. Never push or publish.
Write the dated maintenance report and checkpoint. Return [SILENT] when there
is nothing to process; otherwise report processed, moved, created, modified,
skipped, conflicts, failures, and remaining inbox files.
EOF
)

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
echo "Run it once manually, inspect its commit/report, then resume it with:"
echo "  hermes -p wiki-maintainer cron run $name"
echo "  hermes -p wiki-maintainer cron resume $name"
