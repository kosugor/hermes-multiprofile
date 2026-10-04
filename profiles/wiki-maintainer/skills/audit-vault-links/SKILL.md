---
name: audit-vault-links
description: Check Obsidian links, embeds, and rename effects in a vault scope.
---

# audit-vault-links

## Language

Write internal English in ASD-STE100 style. Write curated wiki prose in Serbian.
Keep required schema labels and values unchanged. Preserve source quotations in
their original language.

Set the scope. List note paths, aliases in frontmatter, headings, and block
IDs. Do not index `.git`, `.obsidian`, `.trash`, `.hermes-backups`, or
`.hermes-maintenance`. Separate old broken links from links that this task
breaks.

Check wikilinks such as `[[note]]` and `[[note|label]]`, heading and block
references, embeds such as `![[asset]]`, and Markdown links. Resolve relative
paths and Obsidian basename links by using the vault's link rules. If two
basenames match, do not choose one without review. A regex scan can find
candidates. It cannot fully parse Obsidian links.

Before a rename, list incoming links and embeds. Check for target collisions
and case-only name changes. Keep alias labels, heading suffixes, and block
references. For an authorized move, update affected references only. Do not
change link-like text in code fences.

Run `scripts/validate-vault.py <vault>` to check the full vault. It parses YAML
frontmatter and links. It also checks freshness, source records, and the
Evidence ledger in `maintain-obsidian-wiki/SCHEMA.md`. This check applies to
`entities/`, `concepts/`, `comparisons/`, and `queries/`. Hubs do not need an
Evidence ledger because they provide navigation. Read affected notes again.
Confirm that new targets exist. Repair clear links in scope only. Propose wider
repairs instead of rewriting the vault. Report new broken links, old issues,
and unclear targets as separate items.

Run `scripts/wiki-audit.py <vault> duplicates` for source-URL and SHA-256
duplicate groups, or `scripts/wiki-audit.py <vault> clippings` for a
read-only clipping report. These commands do not change the vault. They write a
report only when you give `--write-report`.

Do not index maintenance checkpoints or backup directories as notes.
