---
name: repo-ingest
description: "Copy Markdown files from GitHub into wiki raw/doc."
version: 0.1.0
author: Goran Kosutic, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [github, repository, markdown, ingestion, obsidian]
    related_skills: [obsidian, obsidian-wiki-ingestion]
---

# GitHub Repository Ingest

Use this skill when the user wants all Markdown documentation from a GitHub repository copied into an existing Obsidian wiki. The workflow preserves repository-relative paths, records immutable provenance, avoids duplicate content, and verifies complete coverage. It does not synthesize or rewrite the imported documentation.

## When to Use

- The user provides a GitHub repository URL and a wiki destination.
- The user asks to import, mirror, or ingest repository documentation.
- The desired output is raw source preservation under `raw/doc/`.

Do not use this for a single article, arbitrary web pages, or a request to summarize the repository instead of preserving its files.

## Prerequisites

- A public GitHub repository URL, or an already authenticated GitHub CLI session for a private repository.
- An existing wiki path, resolved to an absolute filesystem path.
- `git` or the GitHub CLI available through `terminal`.
- Read/write access to the target wiki.

Never put tokens, cookies, or credentials into the copied Markdown or generated manifest.

## How to Run

Use `terminal` for repository discovery and temporary checkout. Use `read_file`, `write_file`, `patch`, and `search_files` for wiki inspection and updates. Prefer a temporary directory created with Python's `tempfile` rather than a fixed machine-specific path.

Canonical invocation pattern:

```bash
python - <<'PY'
import tempfile
from pathlib import Path
# Clone or download the repository into a temporary directory,
# enumerate Markdown files, and write the ingest manifest.
PY
```

For a public repository, a shallow clone is sufficient:

```bash
git clone --depth 1 --filter=blob:none --sparse <REPOSITORY_URL> <TEMP_DIR>
```

If sparse checkout filtering hides documentation files, retry with a normal shallow clone before concluding that the repository has no Markdown files.

## Procedure

1. **Validate inputs.** Parse the repository URL without changing its spelling, resolve the wiki destination to an absolute path, and confirm that `<wiki>/raw/doc/` is the intended target. Completion criterion: repository identity and target directory are unambiguous.

2. **Orient in the wiki.** Read `SCHEMA.md`, `index.md`, and recent `log.md` when they exist. Inspect existing files under `raw/doc/` before writing. Completion criterion: local frontmatter, naming, and logging conventions are recorded.

3. **Acquire the repository.** Clone the requested repository at the default branch into a temporary directory. For a private repository, use the user's existing GitHub authentication; never ask for or record a token in a file. Completion criterion: the checkout's remote URL and commit are captured in the manifest.

4. **Enumerate documents deterministically.** Find files whose extensions are `.md` or `.markdown`, case-insensitively, excluding `.git/`, `.github/`, vendored dependency directories, and temporary checkout metadata. Never copy any `.github` directory or its contents, regardless of nesting depth. Sort paths using stable lexicographic order. Completion criterion: the manifest contains the exact source count and every relative source path.

5. **Preserve repository structure.** For each source document, write to `<wiki>/raw/doc/<relative-source-path>`. Keep the original filename and path. If the destination would escape `raw/doc/`, reject that path. Completion criterion: every manifest source path maps to exactly one destination path.

6. **Add provenance without corrupting source content.** Prefer a small YAML frontmatter block containing `source_repo`, `source_path`, `source_commit`, `source_url`, `ingested`, and `sha256`, followed by the original Markdown body. The digest must be computed over the exact original source bytes, not over a reconstructed or normalized string. If the wiki convention requires a different hash scope, follow `SCHEMA.md` and record the scope in the manifest. Completion criterion: every written file has a reproducible hash and provenance fields.

7. **Deduplicate safely.** Before replacing an existing raw document, compare its recorded canonical source identity and hash. Leave identical content untouched. For changed content, overwrite only when the source path and repository identity match; otherwise preserve the old file and create a collision-safe filename, recording the collision. Completion criterion: no unrelated raw document is overwritten.

8. **Write a deterministic manifest.** Store a manifest under `<wiki>/raw/doc/` or the location specified by the local schema. Include repository URL, commit, ingest timestamp, source count, copied count, skipped-identical count, collision count, and per-file source/destination/hash records. Do not include credentials. Completion criterion: manifest counts are generated programmatically and agree with the file records.

9. **Update the wiki log only if the wiki uses one.** Append one concise entry to `log.md` listing the repository, commit, counts, manifest path, and any collisions or failures. Do not create entity/concept pages or rewrite `index.md` unless the user explicitly asks for downstream wiki integration. Completion criterion: the log names every created or updated control file.

10. **Verify end to end.** Re-enumerate the repository documents and compare them programmatically with the manifest. Verify each destination exists, each provenance source path matches, each hash matches the original bytes according to the declared scope, and no broken relative destination was created. Completion criterion: `source_count == manifest_count == verified_count`, with zero unhandled failures.

## Quick Reference

- Target folder: `<wiki>/raw/doc/`
- Accepted extensions: `.md`, `.markdown`, case-insensitive
- Preserve: repository-relative path and original Markdown body
- Record: repository URL, source path, commit, canonical source URL, ingest date, SHA-256
- Required final check: deterministic manifest plus source/destination/hash coverage comparison
- Side effects: raw documents and, when configured by the wiki, one append-only log entry

## Pitfalls

- Do not use GitHub search results as the inventory; the checked-out repository is authoritative.
- Do not silently flatten paths or rename two same-named files from different directories into one file.
- Do not treat `README.md` and `docs/README.md` as duplicates merely because their basenames match.
- Do not normalize line endings before hashing the original source. If the written file has frontmatter, keep the original digest separately from any digest required by the wiki schema.
- Do not copy `.git` internals, generated dependency trees, secrets, or files outside the repository checkout.
- Do not claim success if sparse checkout, authentication, rate limits, or network errors prevented exhaustive enumeration; report the exact blocker and partial counts.
- A repository may contain Markdown files with frontmatter already. Preserve the original body and avoid creating nested/conflicting metadata without recording the original metadata boundary.
- The current session's skill catalog may not show this newly created skill until a new session starts; this is expected.

## Verification Checklist

- [ ] Repository URL and wiki path were validated.
- [ ] `SCHEMA.md`, `index.md`, and recent `log.md` were inspected when present.
- [ ] Default-branch commit was recorded.
- [ ] All `.md`/`.markdown` files were enumerated deterministically.
- [ ] Every source has exactly one destination under `raw/doc/`.
- [ ] Original bytes were preserved and hashes are reproducible.
- [ ] Existing identical files were skipped; collisions were not overwritten silently.
- [ ] Manifest counts equal programmatically verified counts.
- [ ] Log entry was added only when local wiki conventions require it.
- [ ] No credentials were written to the wiki.
