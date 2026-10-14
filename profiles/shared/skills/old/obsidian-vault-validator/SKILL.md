---
name: obsidian-vault-validator
description: Validate full-vault Obsidian links and note-title aliases.
version: 0.1.0
author: Goran Kosutic, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [obsidian, vault, validation, wikilinks]
    related_skills: [obsidian, obsidian-wiki-maintenance]
---

# Obsidian Vault Validator Skill

Use this skill for deterministic validation of an entire Obsidian vault. It validates Markdown wikilinks across all vault areas, not only one wiki, and enforces the canonical link form with a vault-relative path and an alias equal to the target note's YAML `title`.

## When to Use

- Before or after maintaining any Obsidian wiki.
- When checking whether links work across wiki boundaries.
- When normalizing links to the canonical full-path form.
- When a maintenance workflow needs a vault-wide link-integrity gate.

Do not use this as a replacement for wiki-specific metadata, index, provenance, or source-path validation.

## Prerequisites

- A concrete vault directory.
- Python 3.10+ and only the standard library.

## How to Run

From this skill directory:

```bash
python scripts/validate-vault.py /path/to/obsidian-vault
python scripts/validate-vault.py /path/to/obsidian-vault --json
```

The validator excludes `.git/`, `.obsidian/`, and `.trash/`. It scans every remaining Markdown note, including raw/source areas.

## Canonical Link Format

Every internal wikilink must use the full vault-relative Markdown path and an explicit alias identical to the target note's `title`:

```md
[[wiki/ai/concepts/example-note|Example Note]]
```

The `.md` suffix is optional for compatibility with Obsidian, but the path must include the complete vault-relative directory path. Basename-only links, wiki-root-relative links, missing aliases, mismatched aliases, unsafe paths, missing targets, ambiguous targets, and missing headings/block IDs are errors.

## Procedure

1. Resolve the vault to an absolute directory.
2. Run `scripts/validate-vault.py` without `--json` and separate errors by source note and line.
3. Repair only links within the requested scope; do not rewrite raw source prose automatically.
4. Re-run the validator and require zero errors before reporting success.
5. For machine-readable automation, use `--json` and require an empty problem list.

## Integration with Wiki Maintenance

When `obsidian-wiki-maintenance` is active, run this validator first as the vault-wide link gate, then run the maintenance skill's wiki-specific metadata/index/provenance checks. The two checks are complementary and must not be conflated.

## Pitfalls

- YAML `title` is authoritative for the required alias; a filename or Obsidian display name is not a substitute.
- Links inside fenced code blocks are ignored because they are examples, not navigation.
- External URLs are not wikilinks and are ignored.
- A clean vault-wide link result does not prove `index.md`, frontmatter, or `sources:` integrity.
- The validator reports problems but never edits notes.

## Verification

A successful run ends with `problems=0` and exit status 0. Run the bundled tests directly:

```bash
python scripts/test-validate-vault.py
```
