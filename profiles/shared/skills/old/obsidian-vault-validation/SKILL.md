---
name: obsidian-vault-validation
description: Validate and smoke-test Hermes filesystem-first integration with an Obsidian vault.
version: 1.0.0
author: Hermes Agent
created_by: agent
platforms: [linux, macos, windows]
---

# Obsidian Vault Validation

Use this skill when the task is to verify that Hermes can actually work with an Obsidian vault, not just describe the integration.

## When to use

Trigger this skill when the user asks to:
- test the Obsidian skill
- verify Obsidian integration
- confirm Hermes can read/write the vault
- smoke-test a newly configured `OBSIDIAN_VAULT_PATH`

This skill complements the bundled `obsidian` skill. The bundled skill explains how to operate on the vault; this skill gives a concrete validation sequence.

## Validation goals

A successful test should verify all of the following with real tool output:
1. Vault path resolves to a concrete absolute path.
2. The path exists and is a directory.
3. Hermes can list markdown notes in the vault.
4. Hermes can read at least one note, or create one if the vault is empty.
5. Hermes can search note contents.
6. Hermes can create a note with Obsidian wikilinks.
7. Hermes can patch or append to that note.
8. Hermes can read back the final content to verify the write.

## Workflow

1. **Resolve the vault path first.**
   - Prefer `OBSIDIAN_VAULT_PATH`.
   - Do not pass shell variables directly into file tools; resolve them to an absolute path first.

1.5. **Treat large broken-link clusters as redirect candidates.**
   - If many backlinks point to the same legacy path, prefer creating a small alias/redirect note at that exact legacy path.
   - Keep the alias note minimal and point it to the canonical note with a single wikilink.
   - This preserves old backlinks and avoids churn from rewriting many historical references.

2. **Check the directory.**
   - Confirm the path exists and is a directory before using file tools.

3. **List notes.**
   - Search for `*.md` under the vault.
   - If notes exist, pick one for a read test.
   - If the vault is empty, proceed directly to creating a test note.

4. **Run a read/search smoke test.**
   - Read one note.
   - Run a content search restricted to `*.md` to verify search works.

5. **Create a disposable test note.**
   - Use a clearly named note such as `Hermes Obsidian Skill Test.md`.
   - Include simple frontmatter, a heading, and at least one wikilink.
   - If helpful, create a companion note to verify inter-note links.

6. **Patch the note.**
   - Use a targeted `patch` to append a short status line or section.
   - Prefer anchored edits over full rewrites when validating append/edit behavior.

7. **Read back the note.**
   - Confirm the final content includes the created section, wikilinks, and appended text.

8. **Report succinctly.**
   - State what was verified: resolve path, list, read, search, create, patch, read-back.
   - Include note paths created during the test.

## Suggested test note shape

```md
---
title: Hermes Obsidian Skill Test
tags: [hermes, obsidian, test]
---

# Hermes Obsidian Skill Test

This note was created by Hermes to verify Obsidian vault integration.

## Links
- [[Some Existing Note]]
- [[Hermes Obsidian Companion]]

## Status
- Created successfully
```

Then patch in:

```md
- Appended successfully

## Append Test
This section was appended with a targeted patch.
```

## Pitfalls

- The environment variable name is `OBSIDIAN_VAULT_PATH`.
- File tools need a concrete absolute path; they do not expand shell variables.
- A passing validation should include a real write-and-read-back cycle, not only a directory existence check.
- If the vault already contains notes, still perform a create/patch/read-back sequence so write access is verified, not just read access.

## Output standard

Prefer a concise checklist-style conclusion:
- resolved vault path
- listed notes
- read note
- searched contents
- created note
- patched note
- verified final content

## References

- `references/smoke-test-example.md` — compact example of a full validation pass
- `references/maintenance-wikilinks-sweep.md` — broken-wikilink sweep notes and alias/redirect note pattern
