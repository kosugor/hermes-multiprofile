---
name: obsidian-research-write
description: Use when turning research findings into structured Obsidian notes in a filesystem-first vault.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [obsidian, research, notes, markdown, filesystem]
    related_skills: [obsidian]
---

# Write Research into Obsidian

## Overview

Use this skill to convert research results into a clean Obsidian note inside the user's vault. It is optimized for filesystem-first vault workflows using Hermes file tools, not GUI automation or plugin-specific APIs.

The goal is to leave behind a note that is useful later: titled clearly, linked where appropriate, and grounded in the actual research output rather than vague placeholders.

## When to Use

- The user asks to save research into Obsidian
- You have summaries, findings, links, or comparisons that should become a note
- You need to create a new research note or update an existing one in the vault
- You want to add wikilinks from a research note to related vault notes

Do not use this skill for:
- General Obsidian GUI automation
- Plugin-specific workflows that require a dedicated MCP server or Obsidian plugin API
- Tiny one-line scratch notes where a full research structure would be overkill

## Workflow

1. **Resolve the vault path.**
   - Prefer `OBSIDIAN_VAULT_PATH`.
   - If unset, use the documented fallback `~/Documents/Obsidian Vault`.
   - Use `terminal` only to resolve the path or confirm existence; once known, switch to file tools.
   - Completion criterion: you have a concrete absolute vault path that exists.

2. **Classify the research destination before writing.**
   - Determine whether the research is **work** or **private/personal**.
   - If the user explicitly says "work research" or equivalent, write under `Work/Research`.
   - If the user explicitly says "private research" or equivalent, write under `Personal/Research`.
   - If the user's wording clearly implies one of those buckets, use the obvious default instead of asking.
   - Only ask when the classification is genuinely ambiguous and would change where the note is stored.
   - Completion criterion: you know which top-level research folder the note belongs in.

3. **Inspect the vault before writing.**
   - Use `search_files(target="files")` to look for likely existing notes by topic.
   - If the user named a destination note, check whether it already exists.
   - If useful, search note contents for related concepts to identify candidate wikilinks.
   - Completion criterion: you know whether to create a new note or update an existing one.

4. **Choose a stable note title and path.**
   - Prefer a human-readable title derived from the research topic.
   - Keep the filename aligned with the note title unless the user wants another convention.
   - Place work research under `Work/Research` and private research under `Personal/Research` unless the user asks for another destination.
   - Avoid introducing shell variables into file tool paths.
   - Completion criterion: you have the exact absolute path to write.

5. **Draft structured markdown.**
   - Use a compact structure like:
     - frontmatter when useful
     - `# Title`
     - `## Summary`
     - `## Key Points`
     - `## Sources`
     - `## Open Questions`
     - `## Related Notes`
     - `## Next Actions`
   - Include real findings, not empty headings, unless the user explicitly asked for a blank template.
   - Add `[[wikilinks]]` only when they are likely to resolve to real or intentionally created notes.
   - Completion criterion: the note content is ready to write and reflects the actual research.

5. **Write or patch the note.**
   - Use `write_file` for a new note or when rewriting the whole note is clearer.
   - Use `patch` for focused updates to an existing note with stable anchors.
   - Prefer file tools over shell text manipulation.
   - Completion criterion: the note has been written successfully.

6. **Verify by reading back and searching.**
   - Read the resulting note with `read_file`.
   - Optionally run `search_files(target="content")` for the title, key phrases, or wikilinks.
   - Completion criterion: the final note on disk matches what you intended to save.

## Importing prior research files

When the user asks to move earlier research into Obsidian, do not just dump raw filenames into the vault.

- Create cleaned Obsidian-native notes with human-readable titles.
- Preserve provenance in frontmatter with a `source_file:` field pointing to the original markdown file.
- Prefer placing bulk imports in a dedicated subfolder such as `Imported Research/` unless the user asked for another destination.
- Add `[[wikilinks]]` between related imported notes.
- Create an index note that links the imported set.
- If the user asks for consolidation, create a master note that synthesizes the imported notes, but keep the source notes unless the user explicitly asks to replace or delete them.
- See `references/import-and-merge.md` for a compact pattern.

## Suggested Output Shape

When saving research, prefer content like this:

```md
---
title: Topic Name
date: YYYY-MM-DD
tags: [research]
status: inbox
source:
---

# Topic Name

## Summary
Short synthesis of the research.

## Key Points
- Finding 1
- Finding 2

## Sources
- https://example.com

## Open Questions
- Unknown or follow-up items

## Related Notes
- [[Existing Note]]

## Next Actions
- Concrete next step
```

## Scope control and evidence discipline

When the user narrows the research scope after an initial pass — for example by geography, time period, vendor, source type, or a regulatory cut — treat that as a **new filtering constraint**, not just a wording tweak.

- Re-run the research against the narrower scope instead of lightly editing the prior answer.
- Prefer a new note title that makes the narrowed scope obvious when that will help later retrieval, for example `Topic in Europe` rather than silently overwriting a broader note.
- In the note itself, separate **confirmed examples** from **exclusions / near-misses** when the distinction matters.
- If the evidence base is thin, say so directly and frame the result as a **conservative shortlist** rather than implying exhaustiveness.
- When a claim depends on weak web snippets, simulator/forum discussion, or non-authoritative secondary material, label confidence explicitly and avoid turning it into a strong factual claim.

## Regulated / financial research writeups

When saving public-market or regulated-finance research into Obsidian, optimize for *auditability* and *later comparison*:

- Keep the source hierarchy visible in the note body: regulator or primary issuer first, secondary aggregators second.
- If a public source does not expose a field consistently (for example, a founding date, fee, or depositary charge), record `n/a` instead of inferring it.
- For ranking tables, anchor the ranking date explicitly in the title or subtitle so the snapshot is reproducible.
- When the user wants multiple tables, split them by analytical purpose rather than forcing every attribute into one giant table:
  - a main facts table
  - a dedicated fees table
  - a separate ranking / net asset snapshot when relevant
- Prefer concise notes on extraction quirks (e.g. dates visible on the site but not the regulator PDF) over long methodological prose.
- If a source exposes data via predictable page metadata or JSON endpoints, capture that in a short reference note for future reuse.

See `references/regulated-financial-research.md` for a compact pattern and source-handling notes.

## Common Pitfalls

1. **Using `$OBSIDIAN_VAULT_PATH` directly in file tools.**
   Resolve to a concrete absolute path first.

2. **Writing a note without checking for an existing note.**
   Search the vault first to avoid duplicates.

3. **Saving a template instead of the research.**
   If the user asked to save findings, fill in the sections with actual content.

4. **Overstating confidence or completeness.**
   If the research only supports a shortlist, say that clearly and include caveats or exclusions.

5. **Adding broken or speculative wikilinks everywhere.**
   Link selectively to real or intentionally created notes.

6. **Declaring success without reading back the note.**
   Always verify by reading the saved file.

## Verification Checklist

- [ ] Vault path resolved to a concrete absolute path
- [ ] Existing notes searched before creating a new one
- [ ] Note title and filename chosen clearly
- [ ] Research findings written in structured markdown
- [ ] `write_file` or `patch` used appropriately
- [ ] Final note read back after writing
- [ ] Any wikilinks verified or intentionally created
