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

Read `references/canonical-wiki-schema.md` in this skill. It is the
authoritative contract. Do not depend on `/workspace/SCHEMA.md`. Each canonical
page must answer a clear question and support a decision or procedure. Separate
verified evidence, author claims, inference, and conflict. State where the
content applies. List prerequisites, test status, limits, open questions,
freshness, sources, and useful links. Keep `<topic>/hubs/index.md` as the topic
entry point. If it does not exist, check the path and nearby pages before you
create it.

Read related notes and nearby examples. Follow their folder, frontmatter, and
link rules. For a new canonical page, choose its role before you write:
`entities/`, `concepts/`, `comparisons/`, `queries/`, or `hubs/`. Use the
relevant `hubs/index.md` as a question-oriented router. List each canonical
page once in its primary navigation section. Use links for related topics; do
not duplicate the page or repeat its claims in several category lists.

Prefer an existing canonical page when new evidence adds to its decision or
procedure. Create a page only when the topic is central to a source or has
support from at least two sources. Do not create a page for a passing mention.
Use a lowercase, hyphenated filename for a new curated page when the active
schema and nearby paths do not require another form. Keep raw capture names
unchanged. Add at least two useful outbound links when relevant notes exist.
Do not invent facts from a title, snippet, filename, or prior knowledge.

Use `references/canonical-wiki-schema.md` when it conflicts with legacy topic
rules. Do not apply legacy requirements for `guides/`, `index.md`, `log.md`,
`updated`, a legacy tag list, approval gates, archive moves, or old validator
commands unless the schema and task also require them. Keep raw capture bytes
unchanged. Do not repair an unresolved source path by guessing it.

## Legacy corpus boundary

Before a canonical write, inspect `git status --short`. Use the linked schema
for every target scope. Do not invent extra rules from the legacy corpus. Keep
user changes unchanged.

Treat dated maintenance reports, triage queues, and audit snapshots as
historical operational evidence. Do not present them as the current state until
you verify them again. Keep event logs separate from curated knowledge.

Work only under `/workspace`. Resolve each write path. Reject a path that
escapes through a symlink. Stay within the task. Do not add a global taxonomy.

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
