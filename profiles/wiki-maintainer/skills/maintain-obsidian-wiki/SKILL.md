---
name: maintain-obsidian-wiki
description: Edit Obsidian notes in scope. Keep their structure, sources, and links.
---

# maintain-obsidian-wiki

## Language

Write internal English in ASD-STE100 style. Write curated wiki prose in Serbian.
Keep required schema labels and values unchanged. Preserve source quotations in
their original language.

Before you search QMD or access the wiki, acquire the shared lock:
`python3 /workspace/.hermes-maintenance/wiki-writer-lock.py acquire --owner
kanban:<task-id>:wiki-maintainer`. Keep the token through validation and
commit. Then run
`python3 /workspace/.hermes-maintenance/wiki-writer-lock.py release --token
<token>`. If acquisition fails, stop without
wiki work. Use `inspect` to report the lock owner. The operator must resolve a
stale or ownerless lock. Never remove a lock only because it is old. Kanban,
Web Scraper, and cron use this helper and path.

Read the wiki's `SCHEMA.md`. Follow its rules for canonical pages. Each page
must answer a clear question and support a decision or procedure. Separate
verified evidence, author claims, inference, and conflict. State where the
content applies. List prerequisites, test status, limits, open questions,
freshness, sources, and useful links. Keep `<topic>/hubs/index.md` as the topic
entry point. If it does not exist, check the path and nearby pages before you
create it.

Read related notes and nearby examples. Follow their folder, frontmatter, and
link rules. Work only under `/workspace`. Resolve each write path. Reject a
path that escapes through a symlink. Stay within the task. Do not add a global
taxonomy.

When you use a source, read the supplied clipping or research report and the
target note. Keep URLs, dates, and uncertainty. Separate source claims from
user comments. Keep aliases, tags, custom fields, block IDs, callouts, and
embeds unless the task asks for a change.

If the workspace uses Git, check Git status first. Keep all user edits. Before
you edit more than one file, copy each affected file to
`/workspace/.hermes-backups/<unique-task-id>/`. Record each changed path. Do
not create a Git repo or commit by default. Check aliases and related topics to
avoid duplicate notes.

Make focused edits. For a rename or link change, use `audit-vault-links`
before and after the edit. Write a temporary file beside its target. Check it
before you replace the target. Do not remove notes or attachments during
deduplication unless the task authorizes removal and you checked all references.

Report created, changed, and moved paths. Report sources, checks, and unresolved
conflicts. Tell Orchestrator which notes changed so its QMD process can refresh
the index. Do not create another index.
