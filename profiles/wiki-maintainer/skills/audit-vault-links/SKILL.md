---
name: audit-vault-links
description: Check Obsidian links, embeds and rename consequences within an assigned
  vault scope.
---

# audit-vault-links

Identify the scope and collect note paths, frontmatter aliases, headings and block IDs. Ignore .git, .obsidian and .hermes-backups for note indexing. Distinguish existing broken links from ones introduced by this task.

Inspect wikilinks [[note]], aliases [[note|label]], heading/block references, embeds ![[asset]], and Markdown links. Resolve relative paths and Obsidian basename links using existing vault conventions. Ambiguous duplicate basenames require judgment; do not silently choose one. A plain regex scan is only a candidate finder, not full Obsidian parsing.

Before a rename, list incoming links/embeds, target collision risks and case-only rename issues. Preserve alias display text, heading suffixes and block references. For an authorized move, update only affected references and avoid changing link-looking text inside code fences.

After edits, re-read affected notes and verify new targets exist. Report newly broken links, preexisting issues and ambiguous targets separately. Repair only in-scope unambiguous references; propose broader repairs instead of bulk rewriting the vault. For substantial changes retain the before-state described in maintain-obsidian-wiki.

Exclude /vault/.hermes-maintenance from ordinary note indexing; it contains automation checkpoints and reports.
