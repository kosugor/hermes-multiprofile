---
name: maintain-obsidian-wiki
description: Make scoped Obsidian note edits while preserving conventions, provenance and links.
---

# maintain-obsidian-wiki

Before QMD search or any wiki access, acquire the shared lock with
`python3 /workspace/.hermes-maintenance/wiki-writer-lock.py acquire --owner
kanban:<task-id>:wiki-maintainer`. Retain the returned token through validation
and commit, then run
`python3 /workspace/.hermes-maintenance/wiki-writer-lock.py release --token
<token>`. If acquisition fails, stop without
wiki work. Use `inspect` to report an existing owner; stale/ownerless locks
require explicit operator reconciliation and must never be auto-broken by age.
Kanban, Web Scraper, and cron use this same helper and path.

Read the wiki's `SCHEMA.md` and follow its canonical page requirements. The page
must answer an explicit question and support a decision or procedure; preserve
the distinction between verified evidence, author claims, inference, and
conflict. Include applicability, prerequisites, tested/untested status,
limitations, open questions, freshness, provenance, and useful links.
Maintain `<topic>/hubs/index.md` as the topic entry point; create it if absent,
after checking the exact path and nearby conventions.

Read the relevant notes and nearby examples to infer current folder, frontmatter and linking conventions. Work only under `/workspace` and resolve write paths to reject symlink escapes. Respect the task's scope; do not impose a new global taxonomy.

For source integration, read the provided clipping/research artifact and the target note. Preserve URLs, dates and uncertainty. Distinguish imported claims from existing user commentary. Keep aliases, tags, custom fields, block IDs, callouts and embeds unless the task specifically changes them.

Check the initial git status if the workspace uses Git; preserve all existing edits. Before multi-file edits, keep copies of affected originals in `/workspace/.hermes-backups/<unique-task-id>/` and record changed paths. Do not add a new Git repo or commit automatically. Avoid note duplication: check aliases and existing topics first.

Apply focused patches. For renames and link-changing edits use `audit-vault-links` before and after. Write intermediate files beside their target and replace only after validating content. Do not delete original notes or attachments in a deduplication task unless that removal is authorized and references are accounted for.

Return created/modified/moved paths, provenance, checks and unresolved conflicts. Tell the orchestrator which notes changed for its existing QMD refresh process; do not create a separate knowledge index here.
